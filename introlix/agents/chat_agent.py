"""
Conversational Chat Agent Module

This module provides the ChatAgent class, an intelligent conversational agent with
internet search capabilities. The agent can:

- Maintain conversation history across multiple turns
- Use search tools to gather current information
- Reason about whether it needs more information
- Stream responses back to users in real-time
- Make decisions about tool usage vs. direct answers

The ChatAgent is designed for interactive chat interfaces where users ask questions
and the agent provides informed, up-to-date answers by searching the web when needed.
"""

import json
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator
from introlix.agents.baseclass import (
    AgentInput,
    BaseAgent,
    PromptTemplate,
    Tool,
)
from introlix.agents.explorer_agent import ExplorerAgent
from introlix.llm_config import cloud_llm_manager
from introlix.config import CLOUD_PROVIDER


class ToolCall(BaseModel):
    """Structured tool call from LLM"""

    name: str
    input: Dict[str, Any]


class AgentDecision(BaseModel):
    """LLM decision output"""

    type: str = Field(description="Action type: 'tool', 'final', or 'continue'")
    thought: Optional[str] = Field(default=None, description="Agent's reasoning")
    tool_calls: Optional[List[ToolCall]] = Field(
        default=None, description="Tools to call in parallel"
    )
    answer: Optional[str] = Field(
        default=None, description="Final answer if type is 'final'"
    )
    needs_more_info: Optional[bool] = Field(
        default=False, description="Whether more information is needed"
    )


INSTRUCTION = """
You are Introlix Chat a part of Introlix. You task is to chat with user and answer to users query. Today's date is {date}. Always provide up-to-date information.
You have access to internet search using search tool. You have access to mutliple tools:
{tools}

Decision format (respond in JSON):
{{
    "type": "tool" | "final",
    "thought": "your reasoning",
    "tool_calls": [{{"name": "tool_name", "input": {{...}}}}],  // if type is "tool"
    "answer": "your answer",  // if type is "final"
    "needs_more_info": true/false  // whether you need another iteration
}}

Guidelines:
1. Always use search tool when you needs to get latest information or you don't know the answer.
2. Don't make a fake or dummy data when you don't know. If a user asks anything that you don't know or you need more information then you again you search tool.
3. If you already know the answer, set type="final" immediately
4. If tool results are sufficient, set needs_more_info=false
5. Always incldue search source at the end of the answer.
6. Don't add any tokens like <｜begin▁of▁sentence｜> or other extra tokens that user don't needs to see

Examples:

User: "What is the capital of France?"
Response: {{"type": "final", "thought": "I know this", "answer": "The capital of France is Paris."}}

User: "Compare GPT-5 and Gemini 2.5"
Response: {{"type": "tool", "thought": "Need to search both", "tool_calls": [{{"name": "search", "input": {{"queries": ["GPT-5 features", "Gemini 2.5 features"]}}}}], "needs_more_info": false}}

User: "What's the weather in Paris?"
Response: {{"type": "tool", "thought": "Need current weather data", "tool_calls": [{{"name": "search", "input": {{"queries": ["weather in Paris today"]}}}}], "needs_more_info": false}}
"""


class ChatAgent(BaseAgent):
    """
    An agent designed for conversational interactions with search capabilities.

    This agent can:
    1. Maintain conversation history.
    2. Use tools (specifically search) to gather information.
    3. Reason about whether it needs more information or can answer directly.
    4. Stream its response back to the user.

    Attributes:
        unique_id (str): A unique identifier for the user or session.
        tools (List[Dict]): A list of tool definitions available to the agent.
        sys_prompt (str): The system prompt defining the agent's behavior and persona.
        conversation_history (List[Dict]): The history of the conversation.
    """

    def __init__(
        self,
        unique_id: str,
        model: str,
        config: Optional[AgentInput] = None,
        max_iterations=5,
        conversation_history: Optional[List[Dict]] = None,
    ):
        """
        Initialize the ChatAgent.

        Args:
            unique_id (str): Unique identifier for the session/user.
            model (str): The name of the LLM model to use.
            config (Optional[AgentInput]): Configuration for the agent. If None, a default config
                                           with search tools is created.
            max_iterations (int): Maximum number of reasoning/tool-use steps. Defaults to 5.
            conversation_history (Optional[List[Dict]]): Existing conversation history. Defaults to None.
        """

        if config is None:
            config = AgentInput(
                name="ChatAgent",
                description="An intelligent agent that can search and reason",
                tools=self._create_tools(),
            )
        super().__init__(model, config, max_iterations)

        self.unique_id = unique_id
        self.tools = [{"name": "search", "description": "Search on internet."}]

        self.explorer = ExplorerAgent()

        self.sys_prompt = INSTRUCTION.format(
            date=datetime.now().strftime("%Y-%m-%d"), tools=self.tools
        )
        self.conversation_history = conversation_history or []

    def _create_tools(self):
        """
        Creates the default tools for the agent, specifically the search tool.

        Returns:
            List[Tool]: A list of Tool objects available to the agent.
        """

        async def search(queries: List[str] = None, query: str = None) -> str:
            """Search tool that accepts both 'queries' and 'query' for flexibility"""

            # Handle query format
            if query is not None and queries is None:
                queries = [query]
            elif queries is None:
                return "Error: No search queries provided"

            results = await self.explorer.run(
                queries=queries,
                unique_id=self.unique_id,
                get_answer=True,
                max_results=5,
            )

            return "\n\n---\n\n".join(str(results))

        return [
            Tool(
                name="search",
                description="Search the internet for information. Use this tool when you need current data or facts you don't know. IMPORTANT: Input must be a dictionary with 'queries' key containing a list of search queries. For single searches, pass one query in the list; for multiple searches, pass multiple queries. Examples: Single search: {'queries': ['weather in Paris']} | Multiple searches: {'queries': ['GPT-5 features', 'Gemini 2.5 features']} | Always use 'queries' (plural) not 'query'.",
                function=search,
            )
        ]

    def _build_messages_array(
        self, user_prompt: str, state: Dict[str, Any]
    ) -> List[Dict]:
        """
        Constructs the list of messages to send to the LLM.

        This includes:
        1. The system prompt.
        2. Recent conversation history (truncated to manage context).
        3. The current user prompt.
        4. Results from any tools executed in the current turn.
        5. Instructions for the agent to make a decision (JSON format).

        Args:
            user_prompt (str): The current user query.
            state (Dict[str, Any]): The current state containing tool results and history.

        Returns:
            List[Dict]: A list of message dictionaries formatted for the LLM.
        """
        messages = [{"role": "system", "content": self.sys_prompt}]

        # Add conversation history (last 10 messages to manage tokens)
        recent_history = (
            self.conversation_history[-10:]
            if len(self.conversation_history) > 10
            else self.conversation_history
        )

        for msg in recent_history:
            role = msg.get("role")
            content = msg.get("content")
            if role in ["user", "assistant"] and content:
                messages.append({"role": role, "content": content})

        # Build current user prompt with tool results if any
        current_prompt_parts = [f"User Query: {user_prompt}"]

        if state.get("tool_results"):
            current_prompt_parts.append("\nTool Results:")
            for tool_name, result in state["tool_results"].items():
                current_prompt_parts.append(f"\n{tool_name}:\n{result}")

        if state.get("history"):
            last_step = state["history"][-1]
            if last_step.get("parsed"):
                parsed = last_step["parsed"]
                if isinstance(parsed, dict) and parsed.get("needs_more_info"):
                    current_prompt_parts.append(
                        "\n\nYou indicated you need more info. What do you need next?"
                    )

        current_prompt_parts.append("\n\nYour decision (respond in JSON):")

        messages.append({"role": "user", "content": "\n".join(current_prompt_parts)})

        return messages

    async def _call_llm_with_messages(self, messages: List[Dict], stream: bool = False):
        """
        Calls the LLM with the constructed message array.

        Args:
            messages (List[Dict]): The list of messages to send.
            stream (bool): Whether to stream the response. Defaults to False.

        Returns:
            The response from the LLM (string or generator).
        """
        output = await cloud_llm_manager(
            model_name=self.model,
            provider=CLOUD_PROVIDER,
            messages=messages,
            stream=stream,
        )
        return output

    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        """
        Legacy method required by BaseAgent but not used in this implementation.

        The ChatAgent uses `_build_messages_array` instead to support chat history.
        """
        pass

    async def arun(self, user_prompt: str) -> AsyncGenerator[str, None]:
        """
        Runs the agent asynchronously, handling the reasoning loop and streaming the response.

        The process involves:
        1. Iterating up to `max_iterations`.
        2. Building messages and calling the LLM to get a decision (Action/Thought).
        3. Parsing the LLM's JSON output.
        4. Executing tools if requested.
        5. If the agent decides it has enough info (or hits max iterations), it generates a final answer.
        6. The final answer is streamed back to the caller.

        Args:
            user_prompt (str): The user's input query.

        Yields:
            str: Chunks of the response, including thoughts, tool status, and the final answer.
        """
        state = {"history": [], "tool_results": {}}

        for iteration in range(self.max_iterations):
            messages = self._build_messages_array(user_prompt, state)

            # Call LLM (non-streaming for decision)
            raw_output = await self._call_llm_with_messages(
                messages=messages, stream=False
            )

            try:
                # Cleaning the raw_output
                raw_output = raw_output.strip()

                if "<｜begin▁of▁sentence｜>" in raw_output:
                    raw_output = raw_output.replace("<｜begin▁of▁sentence｜>", "")

                if "<｜end▁of▁sentence｜>" in raw_output:
                    raw_output = raw_output.replace("<｜end▁of▁sentence｜>", "")

                # Remove any trailing special characters
                raw_output = raw_output.strip().rstrip("<｜").rstrip("▁")

                # Extract JSON from markdown if present
                if "```json" in raw_output:
                    json_start = raw_output.find("```json") + 7
                    json_end = raw_output.find("```", json_start)
                    raw_output = raw_output[json_start:json_end].strip()
                elif "```" in raw_output:
                    json_start = raw_output.find("```") + 3
                    json_end = raw_output.find("```", json_start)
                    raw_output = raw_output[json_start:json_end].strip()
            except:
                pass

            # Parse decision
            try:
                decision = AgentDecision.model_validate_json(raw_output)
            except Exception as e:
                # Fallback parsing
                try:
                    decision_dict = json.loads(raw_output)
                    decision = AgentDecision(**decision_dict)
                except:
                    yield json.dumps(
                        {
                            "type": "error",
                            "content": "Could not parse LLM output as JSON",
                            "error": str(e),
                        }
                    ) + "\n"
                    break

            # Show thought process
            if decision.thought:
                yield json.dumps(
                    {"type": "thinking", "content": decision.thought}
                ) + "\n"

            # Handle decision type
            if decision.type == "final":
                yield json.dumps(
                    {
                        "type": "answer",
                        "content": decision.answer,
                    }
                ) + "\n"
                break

            elif decision.type == "tool" and decision.tool_calls:
                yield json.dumps(
                    {
                        "type": "tool_calls_start",
                        "tools": [tc.name for tc in decision.tool_calls],
                        "count": len(decision.tool_calls),
                    }
                ) + "\n"
                for tc in decision.tool_calls:
                    tool = next(
                        (t for t in self.config.tools if t.name == tc.name), None
                    )
                    if not tool:
                        yield json.dumps(
                            {
                                "type": "error",
                                "content": f"Tool {tc.name} not found",
                            }
                        ) + "\n"
                        continue

                    try:
                        result = await tool.execute(tc.input)
                        state["tool_results"][tc.name] = result
                        yield json.dumps(
                            {
                                "type": "tool_result",
                                "tool": tc.name,
                                "content": "completed",
                            }
                        ) + "\n"
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        state["tool_results"][tc.name] = error_msg
                        yield json.dumps(
                            {
                                "type": "tool_result",
                                "tool": tc.name,
                                "content": error_msg,
                            }
                        ) + "\n"

            # If no more information needed
            if not decision.needs_more_info:
                # Phase 3: Generate final answer with streaming

                final_messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant. Provide a clear, comprehensive answer based on the search results and conversation context. In the end of answer always include source if the data is from search. If no source is given then don't give source at the end.",
                    }
                ]
                # Add conversation history
                recent_history = (
                    self.conversation_history[-10:]
                    if len(self.conversation_history) > 10
                    else self.conversation_history
                )
                for msg in recent_history:
                    role = msg.get("role")
                    content = msg.get("content")
                    if role in ["user", "assistant"] and content:
                        final_messages.append({"role": role, "content": content})

                # Add current query and tool results
                final_prompt_parts = [f"User asked: {user_prompt}\n"]
                final_prompt_parts.append("\nTool Results:")
                for tool_name, result in state["tool_results"].items():
                    final_prompt_parts.append(
                        f"\nOutput From {tool_name} Tool: {result}"
                    )

                final_prompt_parts.append(
                    "\n\nProvide a comprehensive answer to the user's question based on these search results and conversation history."
                )

                final_messages.append(
                    {"role": "user", "content": "\n".join(final_prompt_parts)}
                )

                # Stream the final response
                response_stream = await self._call_llm_with_messages(
                    final_messages, stream=True
                )

                async for chunk in response_stream:
                    yield json.dumps({"type": "answer_chunk", "content": chunk}) + "\n"

                break


async def main():
    agent = ChatAgent(unique_id="user1", model="gemini-2.5-flash")

    async for chunk in agent.arun("Current PM of Nepal?"):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
