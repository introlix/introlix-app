from introlix.services.LLMState import LLMState

llm_state = LLMState()


async def generate_title(prompt: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a title generator for chatbot. Your task is to generate best by seeing user prompt. Don't response with any exta token. Just give a simple title.",
        },
        {"role": "user", "content": prompt},
    ]
    response = await llm_state.get_open_router(
        model_name="qwen/qwen3-235b-a22b:free", messages=messages, stream=False
    )
    output = response.json()

    try:
        new_title = output["choices"][0]["message"]["content"]
    except:
        new_title = output

    return new_title