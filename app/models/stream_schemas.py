from pydantic import BaseModel
from typing import Optional

class ChatMessageRequest(BaseModel):
    message: str
    forward_to_telegram: bool = False
    project_id: Optional[str] = None
    image_base64: Optional[str] = None
