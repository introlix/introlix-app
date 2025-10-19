from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import uuid

# Chat Agent Response Model
class ChatResponse(BaseModel):
    response: str

# Chat Endpoint Request Model
class ChatRequest(BaseModel):
    prompt: str
    model: str
    search: bool
    agent: str

# Workspace Model
class Workspace(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Workspace Workspace Items
# Chat
class Message(BaseModel):
    """Individual message in a chat"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    tokens: Optional[int] = None  # Token count for this message
    model: Optional[str] = None  # Model used (for assistant messages)

class WorkspaceChat(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Deep Research
class WorkspaceItem(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    type: str
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
