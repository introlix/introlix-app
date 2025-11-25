"""
Generic Agent Implementation Module

This module provides a generic Agent class that extends BaseAgent with structured
output validation using Pydantic models. It handles LLM output parsing, including
cleaning of artifacts like <think> tags and markdown code blocks, and validates
responses against specified output schemas.

The Agent class is designed for tasks requiring structured, validated outputs
and can be easily configured with custom instructions and output models.
"""

import re
import json
import logging
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel
from introlix.agents.baseclass import BaseAgent, PromptTemplate, AgentInput

class Agent(BaseAgent):
    """
    A generic agent implementation that interacts with an LLM to perform tasks based on instructions 
    and structured output requirements.

    This agent handles prompt construction, output parsing (including cleaning of LLM artifacts 
    like <think> tags), and validation against a Pydantic model. It is designed to be flexible 
    and easily extensible for various agentic workflows.

    Attributes:
        row_instruction (str): The base system instruction for the agent.
        output_model_class (Type[BaseModel]): The Pydantic model used for output validation.
        logger (logging.Logger): Logger instance for the agent.
    """

    def __init__(self, 
                 model: Any, 
                 instruction: str, 
                 output_model_class: Type[BaseModel], 
                 config: Optional[AgentInput] = None, 
                 max_iterations: int = 1):
        """
        Initialize the Agent.

        Args:
            model: The LLM model instance to be used by the agent.
            instruction (str): The base system instruction/prompt for the agent.
            output_model_class (Type[BaseModel]): The Pydantic model class used to validate 
                                                  and structure the agent's output.
            config (Optional[AgentInput]): Configuration for the agent, including tools and 
                                           other settings. Defaults to None.
            max_iterations (int): The maximum number of iterations the agent is allowed to run. 
                                  Defaults to 1.
        """
        super().__init__(config=config, model=model, max_iterations=max_iterations)
        self.logger = logging.getLogger(__name__)

        self.row_instruction = instruction
        self.output_model_class = output_model_class

    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        """
        Constructs the prompt template for the LLM based on the user input and current state.

        Args:
            user_prompt (str): The input prompt provided by the user.
            state (Dict[str, Any]): The current state of the agent execution.

        Returns:
            PromptTemplate: A structured template containing the user prompt and system instructions.
        """

        instruction = f"""
        {self.row_instruction}
        """

        return PromptTemplate(user_prompt=user_prompt, system_prompt=instruction)

    async def _parse_output(self, raw_output: str) -> Any:
        """
        Parses and validates the raw string output from the LLM.

        This method performs several cleaning steps:
        1. Removes <think> tags and their content (often used by reasoning models).
        2. Strips Markdown code block delimiters.
        3. Parses the cleaned string as JSON.
        4. Handles nested response structures (e.g., {'type': 'final', 'answer': ...}).
        5. Validates the resulting dictionary against `output_model_class`.

        Args:
            raw_output (str): The raw string response from the LLM.

        Returns:
            Any: An instance of `output_model_class` containing the validated data.

        Raises:
            ValueError: If the output cannot be parsed as JSON.
            Exception: If validation against `output_model_class` fails.
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
        """
        Determines the next action based on the parsed output.

        Args:
            parsed_output (Any): The validated output from `_parse_output`.

        Returns:
            Dict[str, Any]: A dictionary representing the decision, typically containing 
                            a 'type' (e.g., 'final') and the 'answer'.
        """

        # If it's our expected output model, wrap it properly
        if isinstance(parsed_output, self.output_model_class):
            return {"type": "final", "answer": parsed_output}

        # Fallback to parent implementation
        return super()._decide_action(parsed_output)
