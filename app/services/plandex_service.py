import httpx
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

def create_project(title: str):
    url = f"{settings.PLANDEX_API_URL}/projects"
    logger.info(f"Attempting to create Plandex project '{title}' at {url}")
    headers = {"Authorization": f"Bearer {settings.AUTHENTICATION_TOKEN}"} if settings.AUTHENTICATION_TOKEN else {}
    try:
        res = httpx.post(url, json={"name": title}, headers=headers, timeout=5.0)
        logger.info(f"Plandex create_project response status: {res.status_code}")
        res.raise_for_status()
        pid = res.json().get("id", "fallback-id")
        logger.info(f"Created Plandex project ID: {pid}")
        return pid
    except Exception as e:
        logger.error(f"Plandex create_project failed: {e}")
        return "fallback-id"

def generate_plan(project_data: dict):
    title = project_data.get("title", "Unknown")
    logger.info(f"Generating plan for project: {title}")
    project_id = create_project(title)

    url = f"{settings.PLANDEX_API_URL}/projects/{project_id}/plans"
    logger.info(f"Requesting Plandex plan generation at {url}")
    headers = {"Authorization": f"Bearer {settings.AUTHENTICATION_TOKEN}"} if settings.AUTHENTICATION_TOKEN else {}

    try:
        res = httpx.post(url, json={"title": title, "prompt": f"Break down {title} into standard pipeline tasks."}, headers=headers, timeout=5.0)
        logger.info(f"Plandex generate_plan response status: {res.status_code}")
        res.raise_for_status()
    except Exception as e:
        logger.error(f"Plandex generate_plan failed: {e}")

    logger.info("Applying default fallback pipeline sequence.")
    repo_name = f"owner/{title.lower().replace(' ', '-')}"
    return [
        {"repository_id": repo_name, "tag": "Codebase Adaptation"},
        {"repository_id": repo_name, "tag": "Deployment"},
        {"repository_id": repo_name, "tag": "Test-API-Functionality-Test"},
        {"repository_id": repo_name, "tag": "Functionality-Testing"}
    ]
