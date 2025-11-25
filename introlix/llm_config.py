from typing import List, Dict, Union, AsyncGenerator
from introlix.services.LLMState import LLMState

llm_state = LLMState()


async def cloud_llm_manager(
    model_name: str,
    provider: str,
    messages: List[Dict[str, str]],
    stream: bool = False,
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Make a call to the LLM (OpenRouter) with given messages.

    Args:
        model_name: The name of the model to use.
        provider: The LLM provider (e.g., "openrouter", "google_ai_studio").
        messages: List of message dicts in OpenAI format.
        stream: Whether to stream the response.

    Returns:
        Response object or async generator for streaming.
    """
    if provider == "openrouter":
        response = await llm_state.get_open_router(
            model_name=model_name, messages=messages, stream=stream
        )

        if stream:
            # Return the generator directly for streaming
            return response
        else:
            # Non-streaming response
            output = response.json()
            try:
                return output["choices"][0]["message"]["content"]
            except:
                return output
            
    elif provider == "google_ai_studio":
        response = await llm_state.get_ai_studio(
            model_name=model_name, messages=messages, stream=stream
        )

        if stream:
            return response

        # Gemini-specific JSON parsing
        output = response.json()
        try:
            # Extract text from Gemini structure: candidates[0].content.parts[0].text
            return output["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            return str(output)  # Fallback for debugging errors
