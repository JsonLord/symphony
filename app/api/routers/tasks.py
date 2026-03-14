from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas, domain
from app.services import jules_service

router = APIRouter()

import logging

logger = logging.getLogger(__name__)

@router.post("/inject", response_model=schemas.TaskInjectResponse)
def inject_task(request: schemas.TaskInjectRequest, db: Session = Depends(get_db)):
    logger.info(f"Injecting task of type {request.task_type} into repo {request.repository_id}")
    # Find current max queue position for this repo
    last_task = db.query(domain.Task).filter(
        domain.Task.repository_id == request.repository_id
    ).order_by(domain.Task.queue_position.desc()).first()

    next_pos = (last_task.queue_position + 1) if last_task else 0

    # But usually injections happen at the front of the pending queue, so let's set it to be next.
    # For simplicity, we just add it to position 0 and shift others, or just give it priority.
    # We will give it queue_position = -1 to jump the queue.
    priority_pos = -1

    db_task = domain.Task(
        repository_id=request.repository_id,
        task_type=request.task_type,
        tag="Error Report",
        context=request.context.model_dump(),
        queue_position=priority_pos,
        status="pending"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return {"task_id": db_task.id, "status": "injected", "queue_position": priority_pos}

import httpx
from app.core.config import settings

@router.post("/report-issue", response_model=schemas.ReportIssueResponse)
def report_issue(request: schemas.ReportIssueRequest, db: Session = Depends(get_db)):
    logger.info(f"Report issue triggered for space {request.space_id} by profile {request.profile_id}")
    # Fetch actual build logs via HF API
    # The URL matches the requested structure: https://huggingface.co/api/spaces/{profile_id}/{space_id}/logs/build
    # or /logs/run. We'll attempt fetching build logs first.

    url = f"https://huggingface.co/api/spaces/{request.profile_id}/{request.space_id}/logs/build"
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"} if settings.HF_TOKEN else {}

    log_content = "Failed to retrieve logs"

    try:
        # Since it's an SSE stream, we can stream the text out up to a reasonable limit
        with httpx.stream("GET", url, headers=headers) as response:
            if response.status_code == 200:
                lines = []
                for idx, line in enumerate(response.iter_lines()):
                    lines.append(line)
                    if idx > 100: # Limit to 100 lines for the prompt context
                        break
                log_content = "\n".join(lines)
            else:
                log_content = f"HF API responded with status {response.status_code}"
    except Exception as e:
        logger.error(f"Exception fetching logs: {str(e)}")
        log_content = f"Exception fetching logs: {str(e)}"

    logger.info("Logs retrieved. Creating Jules session context.")
    context = {
        "task": f"Analyze Failure for {request.space_id}",
        "logs": log_content,
        "repository_id": "JsonLord/agent-notes" # using requested test repo
    }

    session_id = jules_service.create_session(request.profile_id, context)
    return {"status": "logs_retrieved_and_sent", "jules_session_id": session_id}
