"""
The Context Agent is responsible for gathering all necessary information from the user
before research begins. It expands vague or incomplete queries into detailed, 
well-scoped prompts by asking clarification questions when required.

Input Format:
==============================================================================
QUERY: <original user query>
ANSWER_TO_QUESTIONS: <user's answers to previous clarification questions>
USER_FILES: <list of uploaded file metadata and extracted content summaries>
RESEARCH_SCOPE: <narrow | medium | comprehensive>
==============================================================================

Output Format:
==============================================================================
QUESTIONS: <list of clarification questions to ask the user, if more context is needed>
MOVE_NEXT: <true | false>
CONFIDENCE_LEVEL: <0.0-1.0 score indicating certainty about having enough context>
FINAL_PROMPT: <detailed and enriched prompt consolidating user query and answers>
RESEARCH_PARAMETERS: {
    "estimated_duration": "<short | medium | long>",
    "complexity_level": "<basic | intermediate | advanced>",
    "required_sources": "<academic | news | mixed | technical>",
    "research_depth": "<surface | detailed | comprehensive>"
}
==============================================================================

Notes:
------
- Maximum 5 clarification questions per iteration to avoid user fatigue
- CONFIDENCE_LEVEL helps determine if borderline cases should proceed
- RESEARCH_PARAMETERS guide downstream agent behavior and resource allocation
- If uploaded files contain relevant context, integrate them into FINAL_PROMPT
- Track conversation history to avoid repeating questions
"""

import json
import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .baseclass import AgentInput, AgentOutput, BaseAgent


class ResearchParameters(BaseModel):
    estimated_duration: Literal["short", "medium", "long"] = Field(description="Estimated research duration")
    complexity_level: Literal["basic", "intermediate", "advanced"] = Field(description="Research complexity level")
    required_sources: Literal["academic", "news", "mixed", "technical"] = Field(description="Type of sources required")
    research_depth: Literal["surface", "detailed", "comprehensive"] = Field(description="Depth of research required")


class ContextInput(BaseModel):
    query: str = Field(description="Original user query")
    answer_to_questions: Optional[str] = Field(default=None, description="User's answers to previous clarification questions")
    user_files: Optional[List[Dict]] = Field(default=None, description="List of uploaded file metadata and extracted content summaries")
    research_scope: str = Field(default="medium", description="Research scope: narrow | medium | comprehensive")


class ContextOutput(BaseModel):
    questions: List[str] = Field(description="List of clarification questions to ask the user")
    move_next: bool = Field(description="Whether to proceed to next agent")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence score indicating certainty about having enough context")
    final_prompt: str = Field(description="Detailed and enriched prompt consolidating user query and answers")
    research_parameters: ResearchParameters = Field(description="Research parameters for downstream agents")


class ContextAgent(BaseAgent):
    def __init__(self, config: AgentInput, model, max_iterations: int = 3):
        super().__init__(config, model, max_iterations)
        self.logger = logging.getLogger(__name__)
        
    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> str:
        """Build context-specific prompt for analysis."""
        
        # Parse input if it's JSON, otherwise treat as simple query
        try:
            input_data = json.loads(user_prompt)
            context_input = ContextInput(**input_data)
        except (json.JSONDecodeError, ValueError):
            context_input = ContextInput(query=user_prompt)
        
        files_context = ""
        if context_input.user_files:
            files_context = f"\nUSER_FILES: {json.dumps(context_input.user_files, indent=2)}"
        
        answers_context = ""
        if context_input.answer_to_questions:
            answers_context = f"\nANSWER_TO_QUESTIONS: {context_input.answer_to_questions}"
        
        return f"""
You are a Context Agent in the Introlix Research Platform - a sophisticated multi-agent system for automated research. Your role is CRITICAL as you determine the entire research workflow that follows.

## Your Mission
Gather ALL necessary information from the user before research begins. You are the gateway that determines whether the research will be successful or fail. Your output directly controls:
- Planner Agent (creates research plans)
- Explorer Agents (web searches in parallel)
- Verifier Agent (fact-checking)
- Knowledge Gap Agent (quality control)
- Researcher Agent (final synthesis)

## Current Input Analysis
QUERY: {context_input.query}
RESEARCH_SCOPE: {context_input.research_scope}{files_context}{answers_context}

## Critical Analysis Required
You MUST thoroughly analyze this input and determine if you have enough context for successful research. Consider:

### Query Specificity Assessment
1. Is the query specific enough for meaningful research?
2. What are the exact research objectives?
3. What specific information is the user seeking?
4. Are there any ambiguities that could lead to poor research outcomes?

### Research Type & Scope Analysis
5. What type of research is being requested? (academic, business, technical, news, etc.)
6. How should the research scope (narrow/medium/comprehensive) affect the approach?
7. What level of detail is expected in the final output?
8. What is the intended use of the research results?

### Source Requirements & Quality
9. What sources would be most appropriate and credible?
10. What types of evidence would be most valuable?
11. Are there any specific domains, timeframes, or geographic considerations?
12. What would constitute "high-quality" sources for this query?

### User Context Integration
13. If user files are provided, how do they inform the research direction?
14. What context from previous answers should influence the research?
15. Are there any constraints or preferences mentioned?

### Research Parameters Optimization
16. What would be the optimal research parameters for this specific query?
17. How should the research scope influence parameter selection?
18. What resource allocation would be most effective?

## Required Output Structure
Respond with a JSON object containing:
- type: "final"
- answer: JSON object with the following structure:
  {{
    "questions": ["specific clarifying question 1", "specific clarifying question 2"],
    "move_next": true/false,
    "confidence_level": 0.0-1.0,
    "final_prompt": "detailed, enriched, and comprehensive prompt that consolidates ALL user input and context",
    "research_parameters": {{
      "estimated_duration": "CHOOSE ONE: short OR medium OR long",
      "complexity_level": "CHOOSE ONE: basic OR intermediate OR advanced", 
      "required_sources": "CHOOSE ONE: academic OR news OR mixed OR technical",
      "research_depth": "CHOOSE ONE: surface OR detailed OR comprehensive"
    }}
  }}

## Critical Guidelines
- CONFIDENCE_LEVEL: If < 0.7, ask clarifying questions (max 5 to avoid user fatigue)
- CONFIDENCE_LEVEL: If >= 0.7, proceed to next agent
- CONFIDENCE_LEVEL helps determine if borderline cases should proceed
- FINAL_PROMPT: Must be comprehensive and include ALL relevant context from user files and answers
- Track conversation history to avoid repeating questions
- RESEARCH_PARAMETERS: Must guide downstream agent behavior and resource allocation
- Choose appropriate values for each research parameter based on thorough query analysis
- Consider research scope (narrow/medium/comprehensive) when setting parameters
- Ensure the research can be transformed into a full research paper if needed
- Consider both deep research and quick shallow search capabilities of the platform

## Quality Standards
Your output determines the success of the entire research pipeline. Be thorough, precise, and comprehensive in your analysis.
"""
    
    async def _parse_output(self, raw_output: str) -> Any:
        """Parse LLM output and validate structure."""
        try:
            parsed_output = json.loads(raw_output)
            if parsed_output.get("type") == "final" and "answer" in parsed_output:
                answer = parsed_output["answer"]
                if isinstance(answer, str):
                    answer = json.loads(answer)
                return ContextOutput(**answer)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback for malformed output
        return ContextOutput(
            questions=[],
            move_next=True,
            confidence_level=0.8,
            final_prompt=raw_output,
            research_parameters=ResearchParameters(
                estimated_duration="medium",
                complexity_level="intermediate", 
                required_sources="mixed",
                research_depth="detailed"
            )
        )