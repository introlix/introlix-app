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
    id: Optional[str] = None
    name: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Workspace Workspace Items
class WorkspaceItem(BaseModel):
    id: Optional[str] = None
    workspace_id: str
    item_type: Literal["research_desk", "chat", "deep_research"]
    
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

# Context Agent
class ContextAgent(BaseModel):
    conv_history: str = None
    questions: List[str] = None
    move_next: bool = None
    confidence_level: float = None
    final_prompt: str = None
    research_parameters: dict = None

# Research Desk
class ResearchDeskRequest(BaseModel):
    prompt: str
    model: str

class ResearchDeskContextAgentRequest(BaseModel):
    prompt: str
    model: str
    answers: Optional[str] = None
    research_scope: str
    user_files: Optional[List] = None

class ResearchDesk(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: Optional[str] = None
    state: Optional[Literal["initial", "context_agent", "planner_agnet", "explorer_agent", "complete"]] = "initial" 
    title: Optional[str] = None
    documents: Optional[dict] = None
    context_agent: Optional[ContextAgent] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)