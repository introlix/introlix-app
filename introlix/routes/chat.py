from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from introlix.models import ChatRequest, ChatResponse
from introlix.agents.chat_agent import ChatAgent

chat_router = APIRouter(prefix='/chat')


@chat_router.post('/')
async def chat(request: ChatRequest):
    model = ""
    if request.model == "auto":
        model = "deepseek/deepseek-chat-v3.1:free"
    else:
        model = request.model

    chat_agent = ChatAgent(
        unique_id=request.workspace_id,
        model=model

    )

    if request.search:
        user_prompt = f"{request.prompt}\nSearch on the internet."
    else:
        user_prompt = request.prompt

    async def stream():
        async for chunk in chat_agent.arun(user_prompt):
            yield chunk
    return StreamingResponse(stream(), media_type="text/plain")