from sqlalchemy.orm import Session
from app.models.domain import Task
from app.services import jules_service

def trigger_next_task(db: Session, repository_id: str):
    # Find the next pending task for this repo, ordered by queue_position
    next_task = db.query(Task).filter(
        Task.repository_id == repository_id,
        Task.status == "pending"
    ).order_by(Task.queue_position).first()

    if next_task:
        next_task.status = "in_progress"
        # In a real app, this would use the profile linked to the project
        session_id = jules_service.create_session("dummy-profile", {"task": next_task.tag})
        next_task.jules_session_id = session_id
        db.commit()
        return True
    return False
