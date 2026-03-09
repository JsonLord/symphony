from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_docs_redirect():
    response = client.get("/", follow_redirects=False)
    # The root endpoint now returns index.html, not a redirect
    assert response.status_code == 200
    assert "Symphony - TODO App Issues" in response.text

def test_create_profile():
    response = client.post(
        "/api/v1/settings/profiles",
        json={
            "profile_name": "Test Profile",
            "hf_space_id": "test-space",
            "parameters": {"key": "val"}
        }
    )
    assert response.status_code == 200
    assert "profile_id" in response.json()

def test_create_project():
    # First, create profile
    prof_resp = client.post(
        "/api/v1/settings/profiles",
        json={"profile_name": "Test Profile", "parameters": {}}
    )
    profile_id = prof_resp.json()["profile_id"]

    # Create project
    response = client.post(
        "/api/v1/projects/",
        json={
            "title": "Test Project",
            "description": "desc",
            "profile_id": profile_id
        }
    )
    assert response.status_code == 200
    project_data = response.json()
    assert "project_id" in project_data
    assert project_data["status"] == "planning_complete"

    # Get tasks
    tasks_resp = client.get(f"/api/v1/projects/{project_data['project_id']}/tasks")
    assert tasks_resp.status_code == 200
    tasks_data = tasks_resp.json()
    assert len(tasks_data["tasks"]) == 4 # fallback now returns 4 tasks

def test_inject_task():
    # Inject task
    response = client.post(
        "/api/v1/tasks/inject",
        json={
            "repository_id": "test/repo",
            "task_type": "error_report",
            "profile_id": "dummy_profile",
            "context": {
                "space_id": "target",
                "failing_job_name": "job",
                "jules_template": "Failure_Declaration"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "injected"
    assert "task_id" in data

def test_ideation_stream():
    # Use TestClient stream context manager
    with client.stream("POST", "/api/v1/stream", json={"message": "Hello test", "forward_to_telegram": False}) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        content = ""
        for line in response.iter_lines():
            content += line + "\n"

        # In testing locally without the real AUTHENTICATION_TOKEN or an active plandex,
        # it falls back to yielding a "failed" string but it does yield an SSE stream.
        assert "data:" in content
        assert "event: end" in content
