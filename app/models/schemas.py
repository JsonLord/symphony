from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ProjectCreate(BaseModel):
    title: str
    description: str
    profile_id: str
    image_base64: Optional[str] = None

class ProjectResponse(BaseModel):
    project_id: str
    status: str

class TaskResponse(BaseModel):
    task_id: str
    repository_id: str
    tag: str
    status: str
    jules_session_id: Optional[str] = None

class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]

class ProfileCreate(BaseModel):
    profile_name: str
    hf_space_id: Optional[str] = None
    parameters: Dict[str, str]

class ProfileResponse(BaseModel):
    profile_id: str

class WebhookPayload(BaseModel):
    repository_id: str
    session_id: str
    event: str
    status: str

class WebhookResponse(BaseModel):
    acknowledged: bool
    next_task_triggered: bool

class TaskInjectContext(BaseModel):
    space_id: str
    failing_job_name: str
    jules_template: str

class TaskInjectRequest(BaseModel):
    repository_id: str
    task_type: str = "error_report"
    profile_id: str
    context: TaskInjectContext

class TaskInjectResponse(BaseModel):
    task_id: str
    status: str
    queue_position: int

class ReportIssueRequest(BaseModel):
    task_id: str
    profile_id: str
    space_id: str

class ReportIssueResponse(BaseModel):
    status: str
    jules_session_id: str
