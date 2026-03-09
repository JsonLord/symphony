import httpx
from app.core.config import settings

def create_session(profile_id: str, context: dict):
    # This hits the Jules API proxy POST /sessions endpoint.
    url = f"{settings.JULES_API_URL}/api/jules/sessions"

    # We use a static prompt mapping unless Jules template variables are provided.
    payload = {
        "title": f"Task: {context.get('task', 'Unknown')}",
        "prompt": f"Execute task {context.get('task')} for profile {profile_id}. Ensure APIs are in, write test scripts, and verify Docs endpoint.",
        "sourceContext": context
    }

    headers = {
        "Content-Type": "application/json",
        "X-Jules-Agent-Id": "jules-symphony-orchestrator"
    }

    try:
        res = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        res.raise_for_status()
        data = res.json()
        return data.get("id", f"session-{profile_id}-{context.get('task')}")
    except Exception as e:
        print(f"Jules API create_session failed: {e}")
        # Return a fallback string for testing
        return f"fallback-session-{context.get('task')}"
