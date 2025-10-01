import os
import json
from introlix.services.LLMState import LLMState
import asyncio

llmstate = LLMState()

async def run_llm():
    response = await llmstate.get_open_router(model_name="deepseek/deepseek-chat-v3.1:free", sys_prompt="You are an assistant", user_prompt="Hello How are you?")
    output = json.dumps(response.json(), indent=2)
    return output

print(asyncio.run(run_llm()))