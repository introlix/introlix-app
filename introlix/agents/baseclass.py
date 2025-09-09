import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

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
    function: callable  # Function to execute the tool
    input_schema: Optional[Dict] = Field(
        default=None, description="Optional schema for tool input"
    )

    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v

    def execute(self, input_data: Dict) -> Any:
        """Execute the tool with given input."""
        return self.function(input_data)


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
    output_parser: Optional[callable] = None


class AgentOutput(BaseModel):
    result: Any
    performance: Dict = {}
    next_agent: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

class PromptTemplate(BaseModel):
    user_prompt: str
    system_prompt: str

class BaseAgent(ABC):
    def __init__(self, config: AgentInput, model, max_iterations: int = 10):
        self.config = config
        self.model = model
        self.instruction = "" 
        self.max_iterations = max_iterations

    @abstractmethod
    async def execute(self) -> AgentOutput:
        """Execute agent task (can be overridden if needed)"""
        return await self.run_loop(self.config.task)

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM and return raw output"""
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

    async def run_loop(self, user_prompt: str) -> AgentOutput:
        """Run the agent loop with LLM-driven stopping and max_iterations"""
        state = {"history": [], "tool_results": {}}

        for step in range(self.max_iterations):
            _prompts = self._build_prompt(user_prompt, state)
            prompt = _prompts.user_prompt
            self.instruction = _prompts.system_prompt
            raw_output = await self._call_llm(prompt)
            parsed_output = await self._parse_output(raw_output)
            state["history"].append(
                {"step": step, "raw": raw_output, "parsed": parsed_output}
            )

            action = self._decide_action(parsed_output)

            if action["type"] == "final":
                return AgentOutput(
                    result=action.get("answer", parsed_output),
                    performance={"steps": step + 1},
                )

            elif action["type"] == "tool":
                tool_name, tool_input = action["name"], action.get("input", {})
                tool = next((t for t in self.config.tools if t.name == tool_name), None)
                if not tool:
                    raise ValueError(f"Tool {tool_name} not found")
                tool_result = tool.execute(tool_input)
                state["tool_results"][tool_name] = tool_result

            elif action["type"] == "agent":
                return AgentOutput(result=None, next_agent=action["name"])

        # Max iteration reached
        return AgentOutput(
            result="Max iterations reached", performance={"steps": self.max_iterations}
        )

    def _decide_action(self, parsed_output: Any) -> Dict[str, Any]:
        """Decide what to do next based on parsed LLM output"""
        try:
            if isinstance(parsed_output, BaseModel):
                output = parsed_output
            else:
                output = json.loads(parsed_output)
            # Ensure minimal required fields
            if "type" not in output:
                output["type"] = "final"
            return output
        except Exception:
            return {"type": "final", "answer": parsed_output}

    @abstractmethod
    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        """Build prompt with history and tool results"""

# TODO: run_loop and _decide_action should be imporoved