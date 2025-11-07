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
import asyncio
import logging
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from introlix.agents.baseclass import AgentInput, AgentOutput, BaseAgent, PromptTemplate


class ResearchParameters(BaseModel):
    estimated_duration: Literal["short", "medium", "long"] = Field(
        description="Estimated research duration"
    )
    complexity_level: Literal["basic", "intermediate", "advanced"] = Field(
        description="Research complexity level"
    )
    required_sources: Literal["academic", "news", "mixed", "technical"] = Field(
        description="Type of sources required"
    )
    research_depth: Literal["surface", "detailed", "comprehensive"] = Field(
        description="Depth of research required"
    )


class ContextInput(BaseModel):
    query: str = Field(description="Original user query")
    answer_to_questions: Optional[str] = Field(
        default=None, description="User's answers to previous clarification questions"
    )
    user_files: Optional[List[Dict]] = Field(
        default=None,
        description="List of uploaded file metadata and extracted content summaries",
    )
    research_scope: str = Field(
        default="medium", description="Research scope: narrow | medium | comprehensive"
    )


class ContextOutput(BaseModel):
    questions: List[str] = Field(
        description="List of clarification questions to ask the user"
    )
    move_next: bool = Field(description="Whether to proceed to next agent")
    confidence_level: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score indicating certainty about having enough context",
    )
    final_prompt: str = Field(
        description="Detailed and enriched prompt consolidating user query and answers"
    )
    research_parameters: ResearchParameters = Field(
        description="Research parameters for downstream agents"
    )


class ContextAgent(BaseAgent):
    def __init__(
        self, config: AgentInput, model, conversation_history, max_iterations: int = 3
    ):
        super().__init__(config=config, model=model, max_iterations=max_iterations)
        self.logger = logging.getLogger(__name__)

        self.conversation_history = conversation_history

        self.row_instruction = f"""
        You are a Context Agent in the Introlix Research Platform - a sophisticated multi-agent system for automated research. Your role is CRITICAL as you determine the entire research workflow that follows.
        
        Today's date is {datetime.now().strftime("%Y-%m-%d")}

        ## Your Mission
        Gather ALL necessary information from the user before research begins. You are the gateway that determines whether the research will be successful or fail. Your output directly controls:
        - Planner Agent (creates research plans)
        - Explorer Agents (web searches in parallel)
        - Verifier Agent (fact-checking)
        - Knowledge Gap Agent (quality control)
        - Researcher Agent (final synthesis)

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

        Note: Never make move_next ture if CONFIDENCE_LEVEL < 0.7

        ## Quality Standards
        Your output determines the success of the entire research pipeline. Be thorough, precise, and comprehensive in your analysis.


        ## EXAMPLE OUTPUT 1: Need More Info

        ```json
        {{
        "type": "final",
        "answer": {{
            "questions": [
            "What time period should this research cover?",
            "Are you looking for academic research or industry applications?"
            ],
            "move_next": false,
            "confidence_level": 0.5,
            "final_prompt": "User wants research on AI in healthcare but scope needs clarification",
            "research_parameters": {{
            "estimated_duration": "medium",
            "complexity_level": "intermediate",
            "required_sources": "mixed",
            "research_depth": "detailed"
            }}
        }}
        }}
        ```
        """

    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        """Build context-specific prompt for analysis with proper input validation."""

        pass

    def _build_messages_array(
        self, user_prompt: str, state: Dict[str, Any]
    ) -> List[Dict]:
        # Parse and validate input using the ContextInput modelCONFIDENCE_LEVEL
        try:
            if isinstance(user_prompt, str):
                # Try to parse as JSON first
                try:
                    input_data = json.loads(user_prompt)
                    context_input = ContextInput(**input_data)
                except json.JSONDecodeError:
                    # If not JSON, treat as simple query string
                    context_input = ContextInput(query=user_prompt)
            else:
                # If already a dict, use directly
                context_input = ContextInput(**user_prompt)
        except ValueError as e:
            # Log validation error and use fallback
            self.logger.warning(f"Input validation failed: {e}")
            context_input = ContextInput(query=str(user_prompt))

        messages = [{"role": "system", "content": self.row_instruction}]

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

        # Adding more information for good prompt
        user_prompt_final = []

        current_input = f"""
        # Current Input Analysis
                - Original Query: {context_input.query}
                - Research Scope: {context_input.research_scope}
                - Previous Answers: {context_input.answer_to_questions or "None provided"}
                - User Files: {len(context_input.user_files) if context_input.user_files else 0} files

                CRITICAL INSTRUCTION: 
                - If user has provided answers to previous questions, INCORPORATE them into your analysis
                - Do NOT repeat similar questions - build upon what you already know
                - Only ask NEW clarifying questions if absolutely necessary
                - If confidence level >= 0.7 based on existing information, set move_next = true
        """

        # Build user prompt sections using validated input
        sections = [
            f"QUERY: {context_input.query}",
            f"RESEARCH_SCOPE: {context_input.research_scope}",
        ]

        if context_input.answer_to_questions:
            sections.insert(
                1,
                f"USER'S ANSWERS TO PREVIOUS QUESTIONS: {context_input.answer_to_questions}",
            )

        if context_input.user_files:
            sections.append(
                f"USER_FILES: {json.dumps(context_input.user_files, indent=2)}"
            )

        user_prompt_final = "\n".join(current_input)
        user_prompt_final = "\n".join(sections)

        messages.append({"role": "user", "content": "\n".join(user_prompt_final)})

        return messages

    async def _parse_output(self, raw_output: str) -> Any:
        """Parse LLM output and validate structure."""
        
        # Strip markdown code fences if present
        cleaned_output = raw_output.strip()
        
        # Try to extract JSON from the response
        # Look for JSON objects in the text
        import re
        
        # Pattern to find JSON objects
        json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
        
        # Find all potential JSON objects
        json_matches = re.findall(json_pattern, cleaned_output, re.DOTALL)
        
        # Try to parse each match
        for json_str in reversed(json_matches):  # Start from the end (likely the final output)
            try:
                parsed = json.loads(json_str)
                
                # Check if this is the answer structure we want
                if isinstance(parsed, dict):
                    # Case 1: {"type": "final", "answer": {...}}
                    if parsed.get("type") == "final" and "answer" in parsed:
                        answer = parsed["answer"]
                        
                        # If answer is a string, try to parse it
                        if isinstance(answer, str):
                            try:
                                answer = json.loads(answer)
                            except json.JSONDecodeError:
                                pass
                        
                        if isinstance(answer, dict):
                            # Validate it has required fields
                            if all(key in answer for key in ["questions", "move_next", "confidence_level", "final_prompt"]):
                                return ContextOutput(**answer)
                    
                    # Case 2: Direct ContextOutput structure
                    if all(key in parsed for key in ["questions", "move_next", "confidence_level", "final_prompt"]):
                        return ContextOutput(**parsed)
            
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        
        # If no valid JSON found, try the original approach with code fence stripping
        if cleaned_output.startswith("```"):
            lines = cleaned_output.split("\n")
            # Remove opening fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_output = "\n".join(lines).strip()
            
            try:
                parsed_output = json.loads(cleaned_output)
                if parsed_output.get("type") == "final" and "answer" in parsed_output:
                    answer = parsed_output["answer"]
                    
                    if isinstance(answer, str):
                        try:
                            answer = json.loads(answer)
                        except json.JSONDecodeError:
                            pass
                    
                    if isinstance(answer, dict):
                        return ContextOutput(**answer)
                
                if all(key in parsed_output for key in ["questions", "move_next", "confidence_level", "final_prompt"]):
                    return ContextOutput(**parsed_output)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Fallback for malformed output
        self.logger.warning(f"Could not parse valid ContextOutput, using fallback. Raw output length: {len(raw_output)}")
        return ContextOutput(
            questions=[],
            move_next=False,
            confidence_level=0.0,
            final_prompt="Failed to parse LLM output. Please try again.",
            research_parameters=ResearchParameters(
                estimated_duration="medium",
                complexity_level="intermediate",
                required_sources="mixed",
                research_depth="detailed",
            ),
        )

    def _decide_action(self, parsed_output: Any) -> Dict[str, Any]:
        """Override the base class method to handle ContextOutput specifically."""

        # If it's a ContextOutput object, always treat it as final
        if isinstance(parsed_output, ContextOutput):
            return {"type": "final", "answer": parsed_output}

        # Fallback to parent implementation for other types
        return super()._decide_action(parsed_output)

    async def arun(self, user_prompt: str):
        state = {"history": [], "tool_results": {}}

        messages = self._build_messages_array(user_prompt, state)

        raw_output = await self._call_llm_with_messages(messages=messages, stream=False)

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

    async def process(
        self,
        query: str,
        answers: Optional[str] = None,
        research_scope: str = "medium",
        user_files: Optional[List] = None,
    ) -> ContextOutput:
        """
        Single method - takes input, returns output. That's it.
        """
        context_input = ContextInput(
            query=query,
            answer_to_questions=answers,
            research_scope=research_scope,
            user_files=user_files,
        )

        result = await self.arun(json.dumps(context_input.model_dump()))
        return result.result


# ========== Testing the agent ==========
async def run_context_agent():
    config = AgentInput(
        name="ContextAgent",
        description="Context gathering before research",
        output_type=ContextOutput,
    )
    agent = ContextAgent(config=config, model="moonshotai/kimi-k2:free")

    # Initial query
    user_query = {
        "query": "The Evolution of Large Language Models (2018–2025): Technical Advances, Ethical Challenges, and Industry Impacts",
        "research_scope": "medium",
    }

    iteration = 0
    max_question_iterations = 5

    while iteration < max_question_iterations:
        print(f"\n=== Iteration {iteration + 1} ===")

        # Make LLM call ONLY here, after user has provided input
        print("🤖 Processing your query...")
        result: AgentOutput = await agent.run_loop(user_prompt=json.dumps(user_query))

        print("\n=== Agent Output ===")
        print(f"Questions: {result.result.questions}")
        print(f"Move Next: {result.result.move_next}")
        print(f"Confidence Level: {result.result.confidence_level}")
        print(f"Performance: {result.performance}")

        # Check if we should proceed to next agent
        if result.result.move_next:
            print("\n✅ Enough context gathered, moving to next agent...")
            print(f"\nFinal Prompt: {result.result.final_prompt}")
            print(f"Research Parameters: {result.result.research_parameters}")
            break

        # If there are questions, ask the user and WAIT for complete input
        if result.result.questions:
            print("\n🤖 Clarification Questions:")
            for i, question in enumerate(result.result.questions, 1):
                print(f"{i}. {question}")

            # WAIT for complete user input here - no LLM calls until after this
            print("\nPlease provide answers to the above questions:")
            user_answers = input(
                "Your answers: "
            )  # This blocks until user presses Enter

            # Only AFTER getting the answer, update the query for next iteration
            user_query["answer_to_questions"] = user_answers
            print("✅ Got your answers, processing...")
        else:
            print(
                "\n⚠️ Agent didn't ask questions but also not ready to proceed. Breaking loop."
            )
            break

        iteration += 1

    if iteration >= max_question_iterations:
        print(
            f"\n⚠️ Reached maximum question iterations ({max_question_iterations}). Proceeding anyway."
        )


if __name__ == "__main__":
    asyncio.run(run_context_agent())
