# Symphony Adaptation Project Plan

## 1. Project Description

**Vision and Goals of Symphony Adaptation**
The goal is to build an organizational AI agent—the "Symphony Adaptation"—that serves as an intelligent orchestrator for software development tasks. The core idea is to offload all actual coding strictly to the **Jules API**, while the Symphony Adaptation acts as the brain that sorts, categorizes, and directs the flow of work.

When a user defines a new project, an internal LLM analyzes the request and sends it to **Plandex** to generate a structured implementation plan. The Symphony system then breaks this plan down into granular tasks and assigns them to specific GitHub repositories. Each task follows a strict sequential pipeline within a repository:
1. Codebase Adaptation
2. Deployment
3. Test-API-Functionality-Test (API-Test)
4. Functionality-Testing

While tasks across *different* repositories can run in parallel, tasks *within* a single repository must run sequentially. The system relies heavily on event-driven state transitions, using **n8n Webhooks** (triggered by emails or GitHub events) to verify when a task is finished and automatically enqueue the next one.

**Dynamic Task Injection**
Alongside the automated lifecycle, users have the ability to manually create and inject additional tasks into the workflow when fit. For example, if an error occurs during deployment or testing, a user (or automated monitor) can create an **"Error Report"** task. This task will retrieve the build/container logs (via the HF Space API), combine them with the failing job's context, and send the payload specifically to the **"Failure_Declaration"** Jules template to automatically generate a fix or diagnosis.

**In‑app Integrations of Components**
- **Frontend / UI**: A reactive Kanban interface (Vue 3 + Tailwind) featuring project management tasks. It includes a **Chat** tab for continuous interaction with the Plandex Ideation Agent, complete with a toggle to forward interactions to Telegram.
- **Organisation Agent (LLM) & Stream Handler**: The system provides an `IdeationStreamHandler` (`/api/v1/stream`) to continuously stream interactions from the Plandex agent. It also intercepts new project definitions, sorts the requirements, and structures the payload.
- **Telegram Integration**: When enabled in the UI, chat messages and agent responses are forwarded to a Telegram chat using the `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` Hugging Face space secrets.
- **Plandex Integrator**: Communicates with the Plandex API (`/projects`, `/plans`, `/branches`, etc.) to generate and retrieve the breakdown of tasks.
- **Task Orchestrator (State Machine)**: The core engine that receives tasks from Plandex, assigns them to repositories, and manages their sequential tags (Codebase Adaptation -> Deployment, etc.).
- **Jules API Integrator**: Fills out Jules templates (via the JSON `variables` block format) based on the task parameters and sends them to the Jules API (`POST /sessions`) using the appropriate `X-Jules-Agent-Id`. It enforces the rule that APIs must be built, functionality tested via scripts, and Docs endpoints verified.
- **Webhook Handler**: An endpoint to receive signals from n8n (e.g., CI/CD or email updates) containing a GitHub repo ID and session ID, which triggers the Task Orchestrator to advance the task state.
- **Log Retriever**: A service to hit the Hugging Face Spaces logs API via SSE to retrieve container/build logs using `$HF_TOKEN` and forward them to Jules as a "Report Issue" task.

**Proposed FASTAPI Setup**
- **App Structure**:
  - `main.py`: Entry point, FastAPI initialization.
  - `api/routers/`: Separate routers for `/projects`, `/tasks`, `/webhooks`, `/settings`, and `/stream`.
  - `services/`: Business logic encapsulating `plandex_service.py`, `jules_service.py`, `llm_service.py`, and `hf_vault_service.py`.
  - `models/`: SQLAlchemy ORM models (Project, Repository, Task, SettingsProfile) and Pydantic schemas for request/response validation.
  - `core/`: Configurations, dependency injection (DB sessions, HTTP client sessions), and security (API key verification).
- **Dependency Injection**: Dependencies for database sessions (e.g., `get_db`), configuration settings, and authenticated HTTP clients (e.g., `get_jules_client`, `get_plandex_client`).
- **Configuration & Environment Handling**: Managed via `pydantic-settings`. App secrets like `HF_TOKEN`, database URLs, and default API keys will be read from the environment, while project-specific parameters will be dynamically pulled from the Hugging Face Secret Vault at runtime based on the configured Settings Profiles.

---

## 2. Tasks and Tests

**Task 1: Project & Database Initialization**
- **Action**: Set up the FastAPI skeleton, configure SQLAlchemy with Alembic, and create models for Projects, Tasks, and Settings Profiles.
- **Test (Integration)**: Write an integration test using an in-memory SQLite DB to verify that a Project and associated Tasks can be created, saved, and queried correctly.

**Task 2: Settings Profile & Secret Vault Integration**
- **Action**: Implement the Settings tab backend logic to store profile definitions and their parameter mappings. Create a service that securely fetches values from the Hugging Face Secret Vault during runtime execution.
- **Test (Unit)**: Mock the HF Secret Vault API response. Ensure the `hf_vault_service` correctly maps the stored parameter names to the mocked secret values without exposing them in plaintext logs.

**Task 3: Project Ideation & Plandex Pipeline**
- **Action**: Implement the "Start New Project" flow. This triggers the LLM sorting logic, sends the payload to the Plandex `/projects` and `/plans` endpoints, and parses the returned tasks into the local DB.
- **Test (E2E/Integration)**: Mock the LLM output and the Plandex API responses. Assert that a single `POST /projects` request correctly populates the database with a structured list of Tasks assigned to dummy repositories.

**Task 4: Task Orchestration & State Machine**
- **Action**: Build the internal queueing logic. Ensure tasks for the same repository are executed strictly sequentially (Codebase Adaptation -> Deployment -> API Test -> Functionality Test), while tasks for different repos can be dispatched concurrently.
- **Test (Unit)**: Create a mock state with multiple tasks across two repositories. Verify the orchestrator dispatches the first tasks for both repos simultaneously, but refuses to dispatch the second task for Repo A until the first is marked complete.

**Task 5: Jules API Integration (The Coding Agent)**
- **Action**: Implement the service that constructs a payload for the Jules API. It must read the `X-Jules-Agent-Id` from the profile, fill out the JSON variables in the template (enforcing the API, test scripts, and Docs requirements), and call `POST /sessions`.
- **Test (Integration)**: Mock the `https://harvesthealth-chat-app.hf.space/` endpoints. Verify that the templating engine correctly replaces `{{variables}}` and successfully submits the payload.

**Task 6: Webhook Processing (n8n/GitHub)**
- **Action**: Create the `/webhooks/n8n` endpoint. It will receive a payload containing the `github_repo_id` and `session_id`. The system must look up the active task, mark it complete, and trigger the Orchestrator to start the next task in the sequence.
- **Test (E2E)**: Simulate a webhook POST request. Assert that the current task's state changes from `In Progress` to `Completed`, and that the next task in the sequence for that repo transitions to `In Progress`.

**Task 7: Report Issue (Log Retrieval) & Dynamic Task Injection**
- **Action**: Implement the task to fetch SSE build/run logs from the Hugging Face Spaces API using `curl` logic natively in Python (e.g., `httpx` with stream support). Allow users to manually create this task to inject into the repository's lifecycle. The service must forward the logs and failing job context specifically to the **"Failure_Declaration"** Jules template via the Jules API.
- **Test (Unit)**: Mock an SSE stream response simulating HF logs. Verify the service consumes the stream, buffers it appropriately, and correctly constructs the payload for the "Failure_Declaration" template before sending it to Jules.

**Task 8: Ideation Stream & Telegram Forwarding**
- **Action**: Implement the `IdeationStreamHandler` at `/api/v1/stream` returning a Server-Sent Events (SSE) stream. Include background tasks to forward messages to Telegram using the `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets.
- **Test (Unit)**: Test the `/stream` endpoint to ensure it returns a valid SSE stream and correctly queues background tasks for Telegram forwarding when the toggle is enabled.

---

## 3. Functionality Expectations

**User Perspective**
- The user can access a dashboard to click "Start New Project" and provide a high-level prompt.
- The user can interact continuously with the Plandex Ideation Agent via a dedicated "Chat" tab.
- The user can toggle Telegram forwarding in the chat tab to mirror the conversation to a configured Telegram channel.
- The user can configure "Settings Profiles" where they specify project environments and link parameter names to secure Hugging Face vault secrets.
- The user has visibility into the task queue, seeing exactly which repository is currently undergoing which phase (Codebase Adaptation, Deployment, API Test, Functionality Testing).
- The user can manually create and inject additional tasks into a repository's queue when fit. For instance, they can trigger an "Error Report" task that automatically retrieves failing logs and sends them to the "Failure_Declaration" Jules template for immediate debugging and resolution.

**Technical Perspective**
- The system operates entirely hands-off regarding code creation; it strictly acts as a dispatcher and state manager.
- It seamlessly integrates multiple external APIs: Plandex for work breakdown, Jules API for code execution, and HF Spaces for logs/secrets.
- The background orchestrator ensures strict sequential consistency per repository. A new task in a repo will *never* start until the previous task's webhook confirms completion.
- Parallelism is safely achieved across boundaries (distinct repository IDs).
- All interactions with the Jules API use predefined, strictly typed templates ensuring that testing and documentation are implicitly requested for every functionality.

**Constraints & Assumptions**
- **Constraint**: The orchestrator must not attempt to edit code directly.
- **Assumption**: The n8n webhooks will reliably deliver the necessary context (Repo ID, Session ID, Status) to map events back to internal tasks.
- **Assumption**: The Jules API is capable of parsing the templates and independently pushing code to the target GitHub repositories.

---

## 4. API Endpoints to be Exposed

**1. `POST /api/v1/projects`**
- **Description**: Starts a new project ideation flow. Triggers the LLM and Plandex integration.
- **Request Schema**:
  ```json
  {
    "title": "My New App",
    "description": "High level idea description",
    "profile_id": "uuid-of-settings-profile"
  }
  ```
- **Response Schema**: `{ "project_id": "uuid", "status": "analyzing" }`
- **Auth**: Requires standard bearer token / internal auth.

**2. `GET /api/v1/projects/{project_id}/tasks`**
- **Description**: Lists all broken-down tasks for a specific project, including their current sequential tag and status.
- **Response Schema**:
  ```json
  {
    "tasks": [
      {
        "task_id": "uuid",
        "repository_id": "owner/repo",
        "tag": "Codebase Adaptation",
        "status": "in_progress",
        "jules_session_id": "session-123"
      }
    ]
  }
  ```

**3. `POST /api/v1/settings/profiles`**
- **Description**: Creates or updates a settings profile with variable mappings to be pulled from the HF Vault.
- **Request Schema**:
  ```json
  {
    "profile_name": "Production Profile",
    "hf_space_id": "my-space",
    "parameters": {
      "db_password": "HF_VAULT_DB_PASSWORD_KEY"
    }
  }
  ```
- **Response Schema**: `{ "profile_id": "uuid" }`

**4. `POST /api/v1/webhooks/n8n`**
- **Description**: Receives status updates from external systems (like n8n monitoring emails/GitHub). Advances the state machine.
- **Request Schema**:
  ```json
  {
    "repository_id": "owner/repo",
    "session_id": "session-123",
    "event": "deployment_success",
    "status": "completed"
  }
  ```
- **Response Schema**: `{ "acknowledged": true, "next_task_triggered": true }`
- **Auth**: Requires a secure Webhook Secret token in headers to prevent spoofing.

**5. `POST /api/v1/stream`**
- **Description**: `IdeationStreamHandler` endpoint for continuous chat interaction with the Plandex agent. Returns a Server-Sent Events (SSE) stream and optionally forwards messages to Telegram.
- **Request Schema**:
  ```json
  {
    "message": "User's chat message",
    "forward_to_telegram": true,
    "project_id": "optional-uuid"
  }
  ```
- **Response Schema**: `text/event-stream` stream containing `data: ...` chunks.

**6. `POST /api/v1/tasks/inject`**
- **Description**: Allows a user or external monitor to inject a dynamic task into the sequential queue. Specifically supports an "error_report" task type that fetches logs and routes to the "Failure_Declaration" Jules template.
- **Request Schema**:
  ```json
  {
    "repository_id": "owner/repo",
    "task_type": "error_report",
    "profile_id": "uuid",
    "context": {
      "space_id": "target-space-id",
      "failing_job_name": "deployment-job",
      "jules_template": "Failure_Declaration"
    }
  }
  ```
- **Response Schema**: `{ "task_id": "uuid", "status": "injected", "queue_position": 2 }`
