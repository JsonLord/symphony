from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas, domain
from app.services import llm_service, plandex_service, orchestrator_service, kanboard_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new project: {project.title}")

    # Sync project to external Kanboard
    kanboard_res = kanboard_service.sync_project_to_kanboard(project.title, project.description)
    kanboard_project_id = kanboard_res.get("project_id", 1) if kanboard_res else 1

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
    logger.info("Calling LLM sorting service...")
    llm_service.sort_project(project.title, project.description)
    logger.info("Calling Plandex to generate project tasks...")
    plan_response = plandex_service.generate_plan({"title": project.title})

    tasks_data = plan_response.get("tasks", [])
    plandex_plan_id = plan_response.get("plandex_plan_id")

    # Store the actual Plandex plan ID in the project so the stream endpoint can use it
    db_project.plandex_plan_id = plandex_plan_id
    db.commit()

    logger.info(f"Received {len(tasks_data)} tasks from Plandex (Plan ID: {plandex_plan_id}). Storing in database.")
    for i, t_data in enumerate(tasks_data):
        db_task = domain.Task(
            project_id=db_project.id,
            repository_id=t_data["repository_id"],
            tag=t_data["tag"],
            queue_position=i
        )
        db.add(db_task)

        # Sync generated tasks to Kanboard
        kanboard_service.sync_task_to_kanboard(
            project_id=str(kanboard_project_id),
            title=f"{t_data['repository_id']} - {t_data['tag']}",
            description=f"Auto-generated task from Plandex pipeline phase: {t_data['tag']}"
        )

    db.commit()

    # Trigger first tasks for each repo
    unique_repos = set(t["repository_id"] for t in tasks_data)
    for repo in unique_repos:
        logger.info(f"Triggering initial orchestrator task for repository: {repo}")
        orchestrator_service.trigger_next_task(db, repo)

    db_project.status = "planning_complete"
    db.commit()

    logger.info(f"Project {db_project.id} created successfully.")
    return {"project_id": db_project.id, "status": db_project.status}

@router.get("/{project_id}/tasks", response_model=schemas.TaskListResponse)
def get_project_tasks(project_id: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching tasks for project {project_id}")
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
