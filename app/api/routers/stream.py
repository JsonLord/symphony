from fastapi import APIRouter, Request, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import httpx
from app.models import stream_schemas, domain
from app.core.config import settings
from app.core.database import get_db
from app.services import ocr_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def forward_to_telegram(message: str, sender: str = "User"):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram forwarding skipped: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secrets.")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": f"*{sender}*: {message}",
        "parse_mode": "Markdown"
    }

    try:
        logger.info(f"Forwarding message to Telegram as {sender}...")
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, timeout=5.0)
            res.raise_for_status()
        logger.info("Successfully forwarded to Telegram.")
    except Exception as e:
        logger.error(f"Failed to forward message to Telegram: {e}")

@router.post("")
async def ideation_stream_handler(request: Request, body: stream_schemas.ChatMessageRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"Received stream request. Forward to telegram: {body.forward_to_telegram}")
    if body.forward_to_telegram:
        background_tasks.add_task(forward_to_telegram, body.message, "User")

    # Lookup the Plandex plan ID if a project ID is provided
    plan_id = "default-plan-id"
    if body.project_id:
        db_proj = db.query(domain.Project).filter(domain.Project.id == body.project_id).first()
        if db_proj and db_proj.plandex_plan_id:
            plan_id = db_proj.plandex_plan_id

    # Process image if provided
    final_message = body.message
    if body.image_base64:
        logger.info("Image provided in stream request. Extracting markdown via OCR...")
        markdown_text = ocr_service.convert_image_to_markdown(body.image_base64)
        final_message += f"\n\nExtracted Image Content:\n{markdown_text}"

    async def event_generator():
        full_response = ""
        branch_name = "main"
        url = f"{settings.PLANDEX_API_URL}/plans/{plan_id}/{branch_name}/tell"

        # From testing, the plandex API requires the token via Authorization.
        headers = {"Authorization": f"Bearer {settings.AUTHENTICATION_TOKEN}"} if settings.AUTHENTICATION_TOKEN else {}

        try:
            logger.info(f"Opening SSE stream to Plandex at {url}")
            async with httpx.AsyncClient() as client:
                # Based on standard Plandex endpoints, we send the prompt to the tell endpoint
                async with client.stream("POST", url, headers=headers, json={"prompt": final_message}, timeout=30.0) as response:
                    if response.status_code != 200:
                        error_msg = f"Plandex streaming failed with status {response.status_code}"
                        logger.error(error_msg)
                        yield f"data: {error_msg}\n\n"
                        yield "event: end\ndata: \n\n"
                        return

                    logger.info("Plandex stream opened successfully. Relaying chunks...")
                    async for chunk in response.aiter_lines():
                        if chunk:
                            # Forward the raw SSE chunks
                            yield chunk + "\n\n"
                            if chunk.startswith("data: "):
                                full_response += chunk[6:]
                    yield "event: end\ndata: \n\n"
        except Exception as e:
            error_msg = f"Connection error to Plandex API: {e}"
            logger.error(error_msg)
            yield f"data: {error_msg}\n\n"
            yield "event: end\ndata: \n\n"
        finally:
            if body.forward_to_telegram and full_response:
                # Forward the completed assistant response to telegram
                background_tasks.add_task(forward_to_telegram, full_response, "Plandex Agent")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
