from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import httpx
from app.models import stream_schemas
from app.core.config import settings

router = APIRouter()

async def forward_to_telegram(message: str, sender: str = "User"):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("Telegram forwarding skipped: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secrets.")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": f"*{sender}*: {message}",
        "parse_mode": "Markdown"
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, timeout=5.0)
            res.raise_for_status()
    except Exception as e:
        print(f"Failed to forward message to Telegram: {e}")

@router.post("")
async def ideation_stream_handler(request: Request, body: stream_schemas.ChatMessageRequest, background_tasks: BackgroundTasks):
    if body.forward_to_telegram:
        background_tasks.add_task(forward_to_telegram, body.message, "User")

    async def event_generator():
        full_response = ""
        plan_id = body.project_id if body.project_id else "default-plan"
        branch_name = "main"
        url = f"{settings.PLANDEX_API_URL}/plans/{plan_id}/{branch_name}/tell"

        # From testing, the plandex API requires the token via Authorization.
        headers = {"Authorization": f"Bearer {settings.AUTHENTICATION_TOKEN}"} if settings.AUTHENTICATION_TOKEN else {}

        try:
            async with httpx.AsyncClient() as client:
                # Based on standard Plandex endpoints, we send the prompt to the tell endpoint
                async with client.stream("POST", url, headers=headers, json={"prompt": body.message}, timeout=30.0) as response:
                    if response.status_code != 200:
                        error_msg = f"Plandex streaming failed with status {response.status_code}"
                        yield f"data: {error_msg}\n\n"
                        yield "event: end\ndata: \n\n"
                        return

                    async for chunk in response.aiter_lines():
                        if chunk:
                            # Forward the raw SSE chunks
                            yield chunk + "\n\n"
                            if chunk.startswith("data: "):
                                full_response += chunk[6:]
                    yield "event: end\ndata: \n\n"
        except Exception as e:
            error_msg = f"Connection error to Plandex API: {e}"
            yield f"data: {error_msg}\n\n"
            yield "event: end\ndata: \n\n"
        finally:
            if body.forward_to_telegram and full_response:
                # Forward the completed assistant response to telegram
                background_tasks.add_task(forward_to_telegram, full_response, "Plandex Agent")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
