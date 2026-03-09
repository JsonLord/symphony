from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas, domain
from app.services import orchestrator_service

router = APIRouter()

@router.post("/n8n", response_model=schemas.WebhookResponse)
def receive_webhook(payload: schemas.WebhookPayload, db: Session = Depends(get_db)):
    # Find active task for this session
    task = db.query(domain.Task).filter(
        domain.Task.repository_id == payload.repository_id,
        domain.Task.jules_session_id == payload.session_id,
        domain.Task.status == "in_progress"
    ).first()

    triggered = False
    if task:
        task.status = "completed"
        db.commit()
        triggered = orchestrator_service.trigger_next_task(db, payload.repository_id)

    return {"acknowledged": True, "next_task_triggered": triggered}
