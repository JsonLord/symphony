import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def authenticate_kanboard():
    """Authenticates with Kanboard and returns the token."""
    if not settings.KANBOARD_API_URL:
        return None

    login_url = f"{settings.KANBOARD_API_URL}/api/login"
    try:
        # Use the AUTHENTICATION_TOKEN for login as requested
        payload = {"token": settings.AUTHENTICATION_TOKEN} if settings.AUTHENTICATION_TOKEN else {
            "username": settings.KANBOARD_USERNAME,
            "password": settings.KANBOARD_PASSWORD
        }
        res = httpx.post(login_url, json=payload, timeout=5.0)
        res.raise_for_status()
        data = res.json()
        return data.get("token") # Assuming the API returns a token that can be used in subsequent headers
    except Exception as e:
        logger.error(f"Failed to authenticate Kanboard service: {e}")
        return None

def sync_project_to_kanboard(title: str, description: str):
    if not settings.KANBOARD_API_URL:
        logger.info("KANBOARD_API_URL not configured. Skipping Kanboard sync.")
        return None

    token = authenticate_kanboard()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    url = f"{settings.KANBOARD_API_URL}/api/projects"
    # Basic attempt to sync project
    try:
        # The prompt says POST /api/projects?name=MyProject&description=Details
        params = {"name": title, "description": description}
        res = httpx.post(url, params=params, headers=headers, timeout=5.0)
        res.raise_for_status()
        logger.info(f"Successfully synced project to Kanboard: {title}")
        return res.json()
    except Exception as e:
        logger.error(f"Failed to sync project to Kanboard: {e}")
        return None

def sync_task_to_kanboard(project_id: str, title: str, description: str):
    if not settings.KANBOARD_API_URL:
        return None

    token = authenticate_kanboard()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    url = f"{settings.KANBOARD_API_URL}/api/tasks"
    try:
        params = {"project_id": project_id, "title": title, "description": description}
        res = httpx.post(url, params=params, headers=headers, timeout=5.0)
        res.raise_for_status()
        logger.info(f"Successfully synced task to Kanboard: {title}")
        return res.json()
    except Exception as e:
        logger.error(f"Failed to sync task to Kanboard: {e}")
        return None
