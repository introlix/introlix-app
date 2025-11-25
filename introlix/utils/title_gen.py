from introlix.llm_config import cloud_llm_manager
from introlix.config import CLOUD_PROVIDER


async def generate_title(prompt: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a title generator for chatbot. Your task is to generate best by seeing user prompt. Don't response with any exta token. Just give a simple title.",
        },
        {"role": "user", "content": prompt},
    ]

    output = await cloud_llm_manager(
        model_name="gemini-2.0-flash",
        provider=CLOUD_PROVIDER,
        messages=messages,
        stream=False,
    )

    return output


if __name__ == "__main__":
    import asyncio

    prompt = "Explain the theory of relativity in simple terms."
    title = asyncio.run(generate_title(prompt))
    print("Generated Title:", title)
