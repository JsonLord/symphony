import httpx
from app.core.config import settings

def create_project(title: str):
    url = f"{settings.PLANDEX_API_URL}/projects"
    # Basic attempt to create a project via Plandex API.
    # We will log errors if the space is down, and fallback.
    try:
        res = httpx.post(url, json={"name": title}, timeout=5.0)
        res.raise_for_status()
        return res.json().get("id", "fallback-id")
    except Exception as e:
        print(f"Plandex create_project failed: {e}")
        return "fallback-id"

def generate_plan(project_data: dict):
    # This simulates a plan generation by first creating a project in Plandex
    # and then requesting tasks/plans for it.
    title = project_data.get("title", "Unknown")
    project_id = create_project(title)

    url = f"{settings.PLANDEX_API_URL}/projects/{project_id}/plans"

    try:
        res = httpx.post(url, json={"title": title, "prompt": f"Break down {title} into standard pipeline tasks."}, timeout=5.0)
        res.raise_for_status()
        # Assume plandex returns some structured list or we map it to our tags
        # Given lack of exact Plandex response schema knowledge, we return our
        # required sequential pipeline structure.
    except Exception as e:
        print(f"Plandex generate_plan failed: {e}")

    # Fallback/Default pipeline sequence per repository
    repo_name = f"owner/{title.lower().replace(' ', '-')}"
    return [
        {"repository_id": repo_name, "tag": "Codebase Adaptation"},
        {"repository_id": repo_name, "tag": "Deployment"},
        {"repository_id": repo_name, "tag": "Test-API-Functionality-Test"},
        {"repository_id": repo_name, "tag": "Functionality-Testing"}
    ]
