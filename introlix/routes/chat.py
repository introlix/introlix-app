from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from introlix.models.chat import ChatRequest, ChatResponse
from introlix.agents.base_agent import Agent, AgentInput

chat_router = APIRouter(prefix='/chat')

chat_config = AgentInput(
    name="Introlix Chat",
    description="Chat with user",
    output_type=ChatResponse
)

@chat_router.post('/')
async def chat(request: ChatRequest):
    model = ""
    if request.model == "auto":
        model = "deepseek/deepseek-chat-v3.1:free"
    else:
        model = request.model

    chat_agent = Agent(
        model=model,
        instruction="You are a chat bot",
        output_model_class=ChatResponse,
        config=chat_config
    )

    return await chat_agent.run(user_prompt=request.prompt)