from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas, domain
from app.services import jules_service

router = APIRouter()

@router.post("/inject", response_model=schemas.TaskInjectResponse)
def inject_task(request: schemas.TaskInjectRequest, db: Session = Depends(get_db)):
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

@router.post("/report-issue", response_model=schemas.ReportIssueResponse)
def report_issue(request: schemas.ReportIssueRequest, db: Session = Depends(get_db)):
    # Mock log retrieval and jules submission
    session_id = jules_service.create_session(request.profile_id, {"logs": "Mock logs..."})
    return {"status": "logs_retrieved_and_sent", "jules_session_id": session_id}
