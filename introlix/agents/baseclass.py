from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Callable, Dict, Optional, Any, List, Type
from abc import ABC, abstractmethod

DEFAULT_AGENT_NAME = "Agent"
DEFAULT_AGENT_DESCRIPTION = "An agent that can perform a task"
DEFAULT_TOOl_DESCRIPTION = "An tool to be executed"


class Tool(BaseModel):
    name: str = Field(default=None, description="The name of the tool")
    description: str = Field(
        default=DEFAULT_TOOl_DESCRIPTION,
        description="The description of what the tool does and is responsible for",
    )
    function: Callable  # Function to execute the tool
    input_schema: Optional[Dict] = Field(
        default=None, description="The input for the tool"
    )  # Optional schema for tool input

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
        description="The description of what the agent does and is responsible for",
    )
    tools: List[Tool] = Field(default=[], description="The tool that should be called")
    task: Optional[str] = Field(default=None, description="User query or task")
    output_type: Optional[Type[BaseModel]] = Field(
        default=None, description="Expected output model"
    )
    output_parser: Optional[Callable[[str], Any]] = None


class AgentOutput(BaseModel):
    result: Any  # Structured or parsed result
    performance: Dict = {}  # Metrics (e.g., execution time, tool calls)
    next_agent: Optional[str] = None  # Optional next agent to call

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BaseAgent(ABC):
    def __init__(self, config: AgentInput, model):
        self.config = config
        self.model = model

    @abstractmethod
    async def execute(self, prompt) -> AgentOutput:
        """Execute the agent's main functionality asynchronously."""
        pass

    async def _call_llm(self, prompt):
        output = self.model.create_chat_completion(
            messages=[
                {"role": "system", "content": self.config.task},
                {"role": "user", "content": prompt},
            ],
        )

        return output.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def _parse_output(self, raw_output: str) -> Any:
        """Parse raw LLM output using output_parser or output_type."""
        if self.config.output_parser:
            return self.config.output_parser(raw_output)
        if self.config.output_type:
            try:
                # Assume output_type is a Pydantic model and parse JSON
                return self.config.output_type.model_validate_json(raw_output)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse output as {self.config.output_type.__name__}: {e}"
                )
        return raw_output
