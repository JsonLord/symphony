from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas, domain
from app.services import llm_service, plandex_service, orchestrator_service

router = APIRouter()

@router.post("/", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = domain.Project(
        title=project.title,
        description=project.description,
        profile_id=project.profile_id,
        status="analyzing"
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Process project
    llm_service.sort_project(project.title, project.description)
    tasks_data = plandex_service.generate_plan({"title": project.title})

    for i, t_data in enumerate(tasks_data):
        db_task = domain.Task(
            project_id=db_project.id,
            repository_id=t_data["repository_id"],
            tag=t_data["tag"],
            queue_position=i
        )
        db.add(db_task)
    db.commit()

    # Trigger first tasks for each repo
    unique_repos = set(t["repository_id"] for t in tasks_data)
    for repo in unique_repos:
        orchestrator_service.trigger_next_task(db, repo)

    db_project.status = "planning_complete"
    db.commit()

    return {"project_id": db_project.id, "status": db_project.status}

@router.get("/{project_id}/tasks", response_model=schemas.TaskListResponse)
def get_project_tasks(project_id: str, db: Session = Depends(get_db)):
    tasks = db.query(domain.Task).filter(domain.Task.project_id == project_id).all()
    return {"tasks": [
        {
            "task_id": t.id,
            "repository_id": t.repository_id,
            "tag": t.tag,
            "status": t.status,
            "jules_session_id": t.jules_session_id
        } for t in tasks
    ]}
