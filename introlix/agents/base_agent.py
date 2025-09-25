import json
import logging
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel
from introlix.agents.baseclass import BaseAgent, PromptTemplate, AgentInput

class Agent(BaseAgent):
    def __init__(self, model, instruction, output_model_class: Type[BaseModel], config: Optional[AgentInput] = None, max_iterations: int = 1):
        super().__init__(config=config, model=model, max_iterations=max_iterations)
        self.logger = logging.getLogger(__name__)

        self.row_instruction = instruction
        self.output_model_class = output_model_class

    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        """Build context-specific prompt for analysis with proper input validation."""

        # Enhanced instruction that uses the validated input
        instruction = f"""
        {self.row_instruction}
        """

        return PromptTemplate(user_prompt=user_prompt, system_prompt=instruction)

    def _decide_action(self, parsed_output: Any) -> Dict[str, Any]:
        """Override the base class method to handle ContextOutput specifically."""

        # If it's a ContextOutput object, always treat it as final
        if isinstance(parsed_output, self.output_model_class):
            return {"type": "final", "answer": parsed_output}

        # Fallback to parent implementation for other types
        return super()._decide_action(parsed_output)
    

# TODO: Develop this Agent class for handling 