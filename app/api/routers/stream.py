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

async def mock_plandex_stream(user_message: str):
    # This simulates a continuous stream response from the Plandex agent.
    # We yield parts of the sentence progressively.

    response_words = [
        "I", " am", " analyzing", " your", " request", " for", " project", " ideation.",
        "\n\nBased", " on", " your", " message: ", f"\"{user_message}\"", ",",
        " I", " will", " begin", " breaking", " this", " down", " into", " sequential", " tasks.",
        "\n\nWould", " you", " like", " to", " proceed", " with", " creating", " the", " GitHub", " repositories?"
    ]

    full_response = ""
    for word in response_words:
        await asyncio.sleep(0.1) # Simulate generation delay
        full_response += word
        yield f"data: {word}\n\n"

    yield "event: end\ndata: \n\n"

@router.post("")
async def ideation_stream_handler(request: Request, body: stream_schemas.ChatMessageRequest, background_tasks: BackgroundTasks):

    if body.forward_to_telegram:
        background_tasks.add_task(forward_to_telegram, body.message, "User")

    async def event_generator():
        full_response = ""
        try:
            # Note: In a real implementation, we would forward the request to Plandex's streaming API
            # For example: `httpx.stream("POST", f"{settings.PLANDEX_API_URL}/plans/{id}/{branch}/tell")`
            # For this MVP, we yield a mock stream
            async for chunk in mock_plandex_stream(body.message):
                if chunk.startswith("data: "):
                    full_response += chunk[6:].strip("\n")
                yield chunk
        finally:
            if body.forward_to_telegram:
                # Forward the completed assistant response to telegram
                background_tasks.add_task(forward_to_telegram, full_response, "Plandex Agent")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
