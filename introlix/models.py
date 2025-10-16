from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ChatResponse(BaseModel):
    response: str

class ChatRequest(BaseModel):
    prompt: str
    model: str
    search: bool
    agent: str
    workspace_id: str

class Workspace(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class WorkspaceItem(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    type: str
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
