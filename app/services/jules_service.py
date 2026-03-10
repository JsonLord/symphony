import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def create_session(profile_id: str, context: dict):
    url = f"{settings.JULES_API_URL}/api/jules/sessions"
    logger.info(f"Preparing to create Jules session at {url} for profile {profile_id}")

    # We use a static prompt mapping unless Jules template variables are provided.
    prompt_text = f"Execute task {context.get('task')} for profile {profile_id}. Ensure APIs are in, write test scripts, and verify Docs endpoint."

    if "logs" in context:
        prompt_text += f"\n\nFailure Logs:\n{context['logs']}"

    payload = {
        "title": f"Task: {context.get('task', 'Unknown')}",
        "prompt": prompt_text
    }

    repo_name = context.get("repository_id", "JsonLord/agent-notes")
    # According to the exact docs: "Requires title, prompt, and sourceContext."
    # The sourceContext string should point to the registered source name for the repo.
    payload["sourceContext"] = f"sources/github/{repo_name}"

    headers = {
        "Content-Type": "application/json",
        "X-Jules-Agent-Id": "jules-symphony-orchestrator"
    }

    try:
        logger.info(f"Sending payload to Jules API: {payload}")
        res = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        logger.info(f"Jules API create_session response status: {res.status_code}")
        res.raise_for_status()
        data = res.json()
        session_id = data.get("id", f"session-{profile_id}-{context.get('task')}")
        logger.info(f"Successfully created Jules session ID: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Jules API create_session failed: {e}")
        return f"fallback-session-{context.get('task')}"
