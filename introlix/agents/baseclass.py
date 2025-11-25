"""
Base Agent Framework Module

This module provides the foundational classes and abstractions for building AI agents
in the Introlix Research Platform. It includes:

- BaseAgent: Abstract base class for all agents with LLM interaction capabilities
- Tool: Representation of callable tools that agents can use
- AgentInput: Configuration structure for agent initialization
- AgentOutput: Standardized output format for agent execution
- PromptTemplate: Structure for passing prompts to LLMs

These classes form the core framework that all specialized agents (ChatAgent,
ExplorerAgent, etc.) build upon, providing consistent interfaces for LLM
communication, tool execution, and output handling.
"""

import json
import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable, Union, AsyncGenerator

from pydantic import BaseModel, Field, ConfigDict, field_validator
from introlix.config import CLOUD_PROVIDER
from introlix.llm_config import cloud_llm_manager

DEFAULT_AGENT_NAME = "Agent"
DEFAULT_AGENT_DESCRIPTION = "An agent that can perform a task"
DEFAULT_TOOL_DESCRIPTION = "A tool to be executed"


class Tool(BaseModel):
    """
    Represents a tool that an agent can use.

    Attributes:
        name (str): The name of the tool.
        description (str): A description of the tool's purpose and functionality.
        function (Optional[Any]): The callable function that implements the tool logic.
        input_schema (Optional[Dict]): A JSON schema defining the expected input for the tool.
    """
    name: str = Field(default=None, description="The name of the tool")
    description: str = Field(
        default=DEFAULT_TOOL_DESCRIPTION,
        description="The description of what the tool does and is responsible for",
    )
    function: Optional[Any] = Field(
        default=None, description="The callable function to execute"
    )
    input_schema: Optional[Dict] = Field(
        default=None, description="Optional schema for tool input"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v

    async def execute(self, input_data: Dict) -> Any:
        """Execute the tool with given input.

        Supports both sync and async callables. If the underlying function
        returns an awaitable, it will be awaited. This method is async so
        callers should await it.
        """
        if self.function is None:
            raise RuntimeError("No function configured for tool")

        # Call the underlying function
        result = self.function(**input_data)

        # If the result is awaitable (coroutine/future), await it
        if inspect.isawaitable(result):
            return await result

        return result


class AgentInput(BaseModel):
    """
    Configuration for an agent.

    Attributes:
        name (str): The name of the agent.
        description (str): A description of the agent's role.
        tools (List[Tool]): A list of tools available to the agent.
        task (Optional[str]): The specific task or query for the agent.
        output_type (Optional[Type[BaseModel]]): The expected Pydantic model for the output.
        output_parser (Optional[Callable[[str], Any]]): A custom function to parse the LLM's raw string output.
    """
    name: str = Field(default=DEFAULT_AGENT_NAME, description="The name of the agent")
    description: str = Field(
        default=DEFAULT_AGENT_DESCRIPTION,
        description="The description of what the agent does",
    )
    tools: List[Tool] = Field(
        default=[], description="The tools available to this agent"
    )
    task: Optional[str] = Field(default=None, description="User query or task")
    output_type: Optional[Type[BaseModel]] = None
    output_parser: Optional[Callable[[str], Any]] = Field(
        default=None, description="Custom output parser function"
    )


class AgentOutput(BaseModel):
    """
    Standardized output format for an agent execution.

    Attributes:
        result (Any): The final result of the agent's execution.
        performance (Dict): Metrics regarding the execution (e.g., number of steps, time taken).
        next_agent (Optional[str]): The name of the next agent to call in a multi-agent flow.
    """
    result: Any
    performance: Dict = {}
    next_agent: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PromptTemplate(BaseModel):
    """
    Structure for passing prompts to the LLM.

    Attributes:
        user_prompt (str): The specific input or query from the user.
        system_prompt (str): The system-level instructions or context for the LLM.
    """
    user_prompt: str
    system_prompt: str


class BaseAgent(ABC):
    """
    Abstract base class for building agents.

    This class provides the foundational structure for an agent, including:
    - LLM interaction (calling cloud or local models).
    - Output parsing and validation.
    - Action decision logic (determining whether to return a final answer, call a tool, or delegate to another agent).
    - Execution loops (single run or iterative).

    Attributes:
        config (Optional[AgentInput]): Configuration settings for the agent.
        model (Any): The LLM model instance or identifier.
        instruction (str): The current system instruction for the agent.
        max_iterations (int): The maximum number of steps the agent can take in a loop.
    """

    def __init__(
        self, model, config: Optional[AgentInput] = None, max_iterations: int = 10
    ):
        """
        Initialize the BaseAgent.

        Args:
            model: The LLM model to use.
            config (Optional[AgentInput]): Configuration object containing tools, description, etc.
            max_iterations (int): Maximum number of iterations for the run loop. Defaults to 10.
        """
        self.config = config
        self.model = model
        self.instruction = ""
        self.max_iterations = max_iterations

    async def _call_llm(
        self, prompt: str, cloud: bool = True, stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Calls the configured LLM with the given prompt.

        Args:
            prompt (str): The user prompt to send to the LLM.
            cloud (bool): If True, uses the cloud LLM manager. If False, uses a local model. Defaults to True.
            stream (bool): If True, returns an async generator for streaming the response. Defaults to False.

        Returns:
            Union[str, AsyncGenerator[str, None]]: The LLM's response as a string or an async generator if streaming.
        """
        if cloud:
            messages = [
                {"role": "system", "content": self.instruction},
                {"role": "user", "content": prompt},
            ]
            output = await cloud_llm_manager(
                model_name=self.model,
                provider=CLOUD_PROVIDER,
                messages=messages,
                stream=stream,
            )
            return output
        else:
            # Local model (non-streaming only)
            output = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": self.instruction},
                    {"role": "user", "content": prompt},
                ],
            )
            return output.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def _call_llm_with_messages(self, messages: List[Dict], stream: bool = False):
        """
        Calls the LLM with a list of message objects (chat history format).

        Args:
            messages (List[Dict]): A list of message dictionaries (e.g., [{"role": "user", "content": "..."}]).
            stream (bool): Whether to stream the response. Defaults to False.

        Returns:
            The output from the cloud LLM manager.
        """

        output = await cloud_llm_manager(
            model_name=self.model,
            provider=CLOUD_PROVIDER,
            messages=messages,
            stream=stream,
        )

        return output

    async def _parse_output(self, raw_output: str) -> Any:
        """
        Parses the raw string output from the LLM.

        It attempts to parse the output using:
        1. A custom `output_parser` if defined in the config.
        2. A Pydantic `output_type` if defined in the config.
        3. Returns the raw string if no parser is configured.

        Args:
            raw_output (str): The raw response string from the LLM.

        Returns:
            Any: The parsed output.

        Raises:
            ValueError: If parsing fails against the specified `output_type`.
        """
        if self.config.output_parser:
            return self.config.output_parser(raw_output)
        if self.config.output_type:
            try:
                return self.config.output_type.model_validate_json(raw_output)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse output as {self.config.output_type.__name__}: {e}"
                )
        return raw_output

    async def run(self, user_prompt: str, stream: bool = False) -> AgentOutput:
        """
        Executes a single run of the agent.

        This method builds the prompt, calls the LLM, parses the output, and determines the action.
        It is suitable for single-turn tasks.

        Args:
            user_prompt (str): The input prompt from the user.
            stream (bool): Whether to stream the LLM response. Defaults to False.

        Returns:
            AgentOutput: The result of the agent's execution, including the answer and performance metrics.
        """
        state = {"history": [], "tool_results": {}}
        prompts = self._build_prompt(user_prompt, state)
        self.instruction = prompts.system_prompt
        raw_output = await self._call_llm(prompts.user_prompt, stream=stream)

        try:
            parsed_output = await self._parse_output(raw_output)
        except Exception as e:
            print(f"Parse failed: {e}")  # Using print instead of self.logger
            parsed_output = raw_output

        state["history"].append({"step": 1, "raw": raw_output, "parsed": parsed_output})

        action = self._decide_action(parsed_output)

        if action["type"] == "final":
            answer = None
            if isinstance(action, dict) and "answer" in action:
                answer = action["answer"]
            elif hasattr(parsed_output, "__dict__"):  # fallback for Pydantic/BaseModel
                answer = parsed_output
            else:
                answer = parsed_output  # fallback to raw output

            return AgentOutput(
                result=answer,
                performance={"steps": 1},
            )

        elif action["type"] == "tool":
            tool_name, tool_input = action["name"], action.get("input", {})
            tool = next((t for t in self.config.tools if t.name == tool_name), None)
            if not tool:
                raise ValueError(f"Tool {tool_name} not found")
            tool_result = await tool.execute(tool_input)
            state["tool_results"][tool_name] = tool_result

        elif action["type"] == "agent":
            return AgentOutput(result=None, next_agent=action["name"])

    async def run_loop(self, user_prompt: str) -> AgentOutput:
        """
        Executes the agent in a loop, allowing for multi-step reasoning or tool usage.

        The loop continues until:
        1. The agent returns a 'final' action.
        2. The agent delegates to another agent.
        3. The maximum number of iterations (`max_iterations`) is reached.

        Args:
            user_prompt (str): The initial input prompt from the user.

        Returns:
            AgentOutput: The final result of the agent's execution loop.
        """
        state = {"history": [], "tool_results": {}}

        for step in range(self.max_iterations):
            prompts = self._build_prompt(user_prompt, state)
            self.instruction = prompts.system_prompt
            raw_output = await self._call_llm(prompts.user_prompt)

            try:
                parsed_output = await self._parse_output(raw_output)
            except Exception as e:
                self.logger.error(f"Parse failed: {e}")
                parsed_output = raw_output

            state["history"].append(
                {"step": step, "raw": raw_output, "parsed": parsed_output}
            )

            action = self._decide_action(parsed_output)

            if action["type"] == "final":
                return AgentOutput(
                    result=(
                        parsed_output["answer"]
                        if "answer" in parsed_output
                        else parsed_output
                    ),
                    performance={"steps": step + 1},
                )

            elif action["type"] == "tool":
                tool_name, tool_input = action["name"], action.get("input", {})
                tool = next((t for t in self.config.tools if t.name == tool_name), None)
                if not tool:
                    raise ValueError(f"Tool {tool_name} not found")
                tool_result = await tool.execute(tool_input)
                state["tool_results"][tool_name] = tool_result

            elif action["type"] == "agent":
                return AgentOutput(result=None, next_agent=action["name"])

        # Max iteration reached
        return AgentOutput(
            result="Max iterations reached", performance={"steps": self.max_iterations}
        )

    def _decide_action(self, parsed_output: Any) -> Dict[str, Any]:
        """
        Determines the next action based on the parsed LLM output.

        This method normalizes the output into a dictionary with a 'type' field
        (e.g., 'final', 'tool', 'agent'). It handles Pydantic models, dictionaries,
        and raw strings (attempting to parse them as JSON).

        Args:
            parsed_output (Any): The output from `_parse_output`.

        Returns:
            Dict[str, Any]: A dictionary describing the action to take.
        """

        # Handle BaseModel (structured Pydantic output) first
        if isinstance(parsed_output, BaseModel):
            result = parsed_output.model_dump()
            # Ensure type field exists
            if "type" not in result:
                result["type"] = "final"
            return result

        # Handle dictionary
        if isinstance(parsed_output, dict):
            # Ensure type field exists
            if "type" not in parsed_output:
                parsed_output["type"] = "final"
            return parsed_output

        # Handle string - try to parse as JSON first
        if isinstance(parsed_output, str):
            try:
                json_result = json.loads(parsed_output)
                if isinstance(json_result, dict):
                    # Ensure type field exists
                    if "type" not in json_result:
                        json_result["type"] = "final"
                    return json_result
                else:
                    # JSON parsed but not a dict, treat as final answer
                    return {"type": "final", "answer": json_result}
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, treat as final answer
                self.logger.warning("Fallback: treating string output as final answer")
                return {"type": "final", "answer": parsed_output}

        # Fallback for any other type
        self.logger.warning(
            f"Fallback: treating {type(parsed_output)} output as final answer"
        )
        return {"type": "final", "answer": parsed_output}

    @abstractmethod
    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        """
        Abstract method to build the prompt for the LLM.

        Subclasses must implement this to define how the user prompt and current state
        (history, tool results) are combined into a `PromptTemplate`.

        Args:
            user_prompt (str): The user's input.
            state (Dict[str, Any]): The current state of the execution (e.g., history, tool outputs).

        Returns:
            PromptTemplate: The constructed prompt template.
        """
