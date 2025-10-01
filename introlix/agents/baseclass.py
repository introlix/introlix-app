import json
import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable

from pydantic import BaseModel, Field, ConfigDict, field_validator

DEFAULT_AGENT_NAME = "Agent"
DEFAULT_AGENT_DESCRIPTION = "An agent that can perform a task"
DEFAULT_TOOL_DESCRIPTION = "A tool to be executed"


class Tool(BaseModel):
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
    result: Any
    performance: Dict = {}
    next_agent: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PromptTemplate(BaseModel):
    user_prompt: str
    system_prompt: str


class BaseAgent(ABC):
    def __init__(self, model, config: Optional[AgentInput] = None, max_iterations: int = 10):
        self.config = config
        self.model = model
        self.instruction = ""
        self.max_iterations = max_iterations

    async def _call_llm(self, prompt: str, cloud: bool = True) -> str:
        """Call LLM and return raw output"""
        if cloud:
            from introlix.services.LLMState import LLMState

            llm_state = LLMState()
            response = await llm_state.get_open_router(
                model_name=self.model, sys_prompt=self.instruction, user_prompt=prompt
            )

            output = response.json()
            try:
                return output["choices"][0]["message"]["content"]
            except:
                return output
        else:
            output = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": self.instruction},
                    {"role": "user", "content": prompt},
                ],
            )
            return output.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def _parse_output(self, raw_output: str) -> Any:
        """Parse LLM output using output_parser or output_type"""
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

    async def run(self, user_prompt: str) -> AgentOutput:
        """Run the agent"""
        state = {"history": [], "tool_results": {}}
        prompts = self._build_prompt(user_prompt, state)
        self.instruction = prompts.system_prompt
        raw_output = await self._call_llm(prompts.user_prompt)

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
        """Run the agent loop with LLM-driven stopping and max_iterations"""
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
                    result=parsed_output["answer"] if "answer" in parsed_output else parsed_output,
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
        """Decide what to do next based on parsed LLM output."""

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
        """Build prompt with history and tool results"""
