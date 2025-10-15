from pydantic import BaseModel

class ChatResponse(BaseModel):
    response: str

class ChatRequest(BaseModel):
    prompt: str
    model: str
    search: bool
    agent: str
    workspace_id: str