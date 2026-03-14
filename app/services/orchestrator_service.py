import httpx
from sqlalchemy.orm import Session
from app.models.domain import Task
from app.services import jules_service, kanboard_service
from app.core.config import settings

def fetch_logs(space_id: str):
    url = f"https://huggingface.co/api/spaces/harvesthealth/{space_id}/logs/build"
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"} if settings.HF_TOKEN else {}

    log_content = "Failed to retrieve logs"
    try:
        with httpx.stream("GET", url, headers=headers) as response:
            if response.status_code == 200:
                lines = []
                for idx, line in enumerate(response.iter_lines()):
                    lines.append(line)
                    if idx > 100:
                        break
                log_content = "\n".join(lines)
            else:
                log_content = f"HF API responded with status {response.status_code}"
    except Exception as e:
        log_content = f"Exception fetching logs: {str(e)}"

    return log_content

def trigger_next_task(db: Session, repository_id: str):
    # Find the next pending task for this repo, ordered by queue_position
    next_task = db.query(Task).filter(
        Task.repository_id == repository_id,
        Task.status == "pending"
    ).order_by(Task.queue_position).first()

    if next_task:
        next_task.status = "in_progress"
        db.commit()

        context = {"task": next_task.tag, "repository_id": repository_id}

        # Fetch the Kanboard project link for the Jules agent context
        # (Assuming project ID 1 for scaffolding purposes, normally fetched from db_project)
        kanboard_link = kanboard_service.get_project_link("1")
        if kanboard_link:
            context["task"] += f" (Kanboard Tracker: {kanboard_link})"

        # If it's an error report, we fetch logs and explicitly pass the requested template to Jules
        if next_task.task_type == "error_report" and next_task.context:
            space_id = next_task.context.get("space_id", "Unknown")
            jules_template = next_task.context.get("jules_template", "Failure_Declaration")
            failing_job = next_task.context.get("failing_job_name", "Unknown")

            logs = fetch_logs(space_id)
            context["logs"] = logs
            context["task"] = f"Analyze {failing_job} error logs via {jules_template} template. (Tracking on Kanboard: {kanboard_link})"
            context["template"] = jules_template

        # In a real app, this would use the profile linked to the project
        session_id = jules_service.create_session("dummy-profile", context)
        next_task.jules_session_id = session_id
        db.commit()
        return True
    return False
