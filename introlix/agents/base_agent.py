import re
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

        instruction = f"""
        {self.row_instruction}
        """

        return PromptTemplate(user_prompt=user_prompt, system_prompt=instruction)

    async def _parse_output(self, raw_output: str) -> Any:
        """
        Override parent's _parse_output to handle:
        1. <think> tags from LLM
        2. Nested {"type": "final", "answer": {...}} structure
        3. Direct JSON output
        """
        try:
            # Step 1: Remove <think> tags and any content between them
            cleaned = raw_output
            if '<think>' in cleaned:
                cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)
            
            # Step 2: Strip whitespace and remove markdown code blocks if present
            cleaned = cleaned.strip()
            if cleaned.startswith('```'):
                # Remove markdown code blocks
                cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
                cleaned = re.sub(r'\n```\s*$', '', cleaned)
                cleaned = cleaned.strip()
            
            # Step 3: Try to parse as JSON
            try:
                parsed_json = json.loads(cleaned)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {e}")
                self.logger.error(f"Attempted to parse: {cleaned[:200]}...")
                raise ValueError(f"Invalid JSON: {e}")
            
            # Step 4: Handle nested {"type": "final", "answer": {...}} structure
            if isinstance(parsed_json, dict):
                if parsed_json.get("type") == "final" and "answer" in parsed_json:
                    parsed_json = parsed_json["answer"]
            
            # Step 5: Validate with output_model_class
            return self.output_model_class(**parsed_json)
            
        except Exception as e:
            self.logger.error(f"Failed to parse output as {self.output_model_class.__name__}: {e}")
            self.logger.error(f"Raw output: {raw_output[:500]}...")
            
            # Fallback: treat as string
            print(f"Parse failed: {e}")
            print("Fallback: treating string output as final answer")
            raise

    def _decide_action(self, parsed_output: Any) -> Dict[str, Any]:
        """Override the base class method to handle output model specifically."""

        # If it's our expected output model, wrap it properly
        if isinstance(parsed_output, self.output_model_class):
            return {"type": "final", "answer": parsed_output}

        # Fallback to parent implementation
        return super()._decide_action(parsed_output)

# TODO: Develop this Agent class for handling 