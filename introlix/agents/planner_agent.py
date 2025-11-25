"""
The Planner Agent creates a structured research plan from the enriched prompt provided
by the Context Agent. It breaks down the research task into discrete topics and decides
which agent should handle the next step.

Input Format:
==============================================================================
QUERY: <enriched prompt from Context Agent>
PREVIOUS_AGENT: <name of the previous agent that called Planner Agent>
PREVIOUS_AGENT_OUTPUT: <output from previous agent, e.g., gap notes, corrections>
RESEARCH_HISTORY: <list of previously researched topics, if this is a repeated cycle>
RESEARCH_PARAMETERS: <parameters from Context Agent about scope, depth, etc.>
ITERATION_COUNT: <number indicating how many planning cycles have occurred>
==============================================================================

Output Format:
==============================================================================
RESEARCH_PLAN: {
    "primary_topics": [
        {
            "topic": "<research topic>",
            "priority": "<high | medium | low>",
            "estimated_sources_needed": <number>,
            "search_keywords": ["<keyword1>", "<keyword2>"]
        }
    ],
    "secondary_topics": ["<optional subtopics for comprehensive research>"],
    "research_questions": ["<specific questions to guide exploration>"],
    "success_criteria": ["<measurable outcomes that indicate completion>"]
}
NEXT_AGENT_NAME: <Explorer Agent | Researcher Agent | Knowledge-Gap Agent>
EXECUTION_STRATEGY: <parallel | sequential | hybrid>
ESTIMATED_COMPLETION: <percentage of total research this plan should accomplish>
FALLBACK_PLAN: <alternative approach if primary plan fails>
==============================================================================

Notes:
------
- Prioritize topics based on user requirements and research objectives
- Include search_keywords to guide Explorer Agent optimization
- EXECUTION_STRATEGY determines if topics can be researched simultaneously
- Track ITERATION_COUNT to prevent infinite planning loops (max 3 iterations)
- Consider RESEARCH_HISTORY to avoid redundant planning
"""

import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput

class PhaseOneAgent(BaseModel):
    """
    Represents a primary research topic identified in Phase One of planning.

    Attributes:
        topic (str): The research topic to investigate.
        priority (str): Priority level - 'high', 'medium', or 'low'.
        estimated_sources_needed (int): Estimated number of sources required for this topic.
    """
    topic: str = Field(description="The topic of the research")
    priority: str = Field(description="Priority level: high, medium, low")
    estimated_sources_needed: int = Field(description="Estimated number of sources needed")

class PhaseOneAgentOutput(BaseModel):
    """
    Output from Phase One of the planning process.

    Attributes:
        topics (list[PhaseOneAgent]): List of identified primary research topics with priorities.
    """
    topics: list[PhaseOneAgent] = Field(description="List of primary topics with details")

class PhaseTwoAgent(BaseModel):
    """
    Represents a research topic with associated search keywords from Phase Two.

    Attributes:
        topic (str): The research topic.
        priority (str): Priority level - 'high', 'medium', or 'low'.
        estimated_sources_needed (int): Estimated number of sources required.
        keywords (list): Search keywords to guide the Explorer Agent.
    """
    topic: str = Field(description="The topic of the research")
    priority: str = Field(description="Priority level: high, medium, low")
    estimated_sources_needed: int = Field(description="Estimated number of sources needed")
    keywords: list = Field(description="Keywords to that will be searched")

class PhaseTwoAgentOutput(BaseModel):
    """
    Final output from the Planner Agent containing topics with search keywords.

    Attributes:
        topics (list[PhaseTwoAgent]): List of topics with associated keywords for research.
    """
    topics: list[PhaseTwoAgent] = Field(description="List of topics with keywords")
    
PHASE_ONE_AGENT_INSTRUCTIONS = f"""
You are the Phase One Agent of the Planner Agent. Your task is to analyze the enriched prompt and
extract the primary research topics. For each topic, determine its priority (high, medium, low) and estimate
the number of sources needed to cover it comprehensively. Make sure the topics are distinct and relevant to the research objectives.
And it should cover the entire scope of the research task. Based on the enriched prompt, provide a list of primary topics with their details.

Today's date is {datetime.now().strftime("%Y-%m-%d")}

Respond in the following JSON format:
{{
  "topics": [
    {{
      "topic": "<research topic>",
      "priority": "<high | medium | low>",
      "estimated_sources_needed": <number>
    }}
  ]
}}

Make sure to only respond with the JSON format specified above and nothing else.
"""

PHASE_TWO_AGENT_INSTRUCTIONS = f"""
You are the Phase Two Agent of the Planner Agent. Your task is to analyze the Phase One Agent output
and generate a list of keywords for each topic. These keywords will be used by the Explorer Agent to
search for relevant information. Ensure that the keywords are specific, relevant, and cover various aspects
of the topic. Take topic and  priority into consideration when generating keywords.

Today's date is {datetime.now().strftime("%Y-%m-%d")}

Respond in the following JSON format:
{{
  "topics": [
    {{
      "topic": "<research topic>",
      "priority": "<high | medium | low>",
      "estimated_sources_needed": <number>,
      "keywords": ["<keyword1>", "<keyword2>"]
    }}
  ]
}}

Make sure to only respond with the JSON format specified above and nothing else.

"""

class PlannerAgent:
    """
    The Planner Agent creates structured research plans from enriched prompts.

    This agent operates in two phases:
    1. **Phase One**: Analyzes the enriched prompt to extract primary research topics,
       assigns priorities, and estimates source requirements.
    2. **Phase Two**: Generates specific search keywords for each topic to guide
       the Explorer Agent's information gathering.

    The Planner Agent is a critical component in the research pipeline, breaking down
    complex research tasks into manageable, searchable topics with clear priorities.

    Attributes:
        model (str): The LLM model identifier to use for planning.
        phase_one_agent (Agent): Agent responsible for topic extraction.
        phase_two_agent (Agent): Agent responsible for keyword generation.
        PHASE_ONE_AGENT_INSTRUCTIONS (str): System prompt for Phase One.
        PHASE_TWO_AGENT_INSTRUCTIONS (str): System prompt for Phase Two.
    """

    def __init__(self, model: str):
        """
        Initializes the PlannerAgent with the specified LLM model.

        Args:
            model (str): The name/identifier of the LLM model to use for planning.
        """
        self.PHASE_ONE_AGENT_INSTRUCTIONS = PHASE_ONE_AGENT_INSTRUCTIONS
        self.PHASE_TWO_AGENT_INSTRUCTIONS = PHASE_TWO_AGENT_INSTRUCTIONS

        self.model = model

        self.phase_one_config = AgentInput(
            name="Phase One Agent",
            description="Extracts primary research topics with priority and estimated sources needed.",
            output_type=PhaseOneAgentOutput
        )

        self.phase_two_config = AgentInput(
            name="Phase Two Agent",
            description="Generates keywords for each primary research topic.",
            output_type=PhaseTwoAgentOutput
        )

        self.phase_one_agent = Agent(
            model=model,
            instruction=self.PHASE_ONE_AGENT_INSTRUCTIONS,
            output_model_class=PhaseOneAgentOutput,
            config=self.phase_one_config
        )

        self.phase_two_agent = Agent(
            model=model,
            instruction=self.PHASE_TWO_AGENT_INSTRUCTIONS,
            output_model_class=PhaseTwoAgentOutput,
            config=self.phase_two_config
        )

    async def create_research_plan(self, enriched_prompt: str) -> PhaseTwoAgentOutput:
        """
        Creates a comprehensive research plan from an enriched prompt.

        This method orchestrates the two-phase planning process:
        1. Calls Phase One Agent to extract primary topics with priorities
        2. Calls Phase Two Agent to generate search keywords for each topic

        Args:
            enriched_prompt (str): The detailed, enriched prompt from the Context Agent
                                   containing the research objectives and scope.

        Returns:
            PhaseTwoAgentOutput: The complete research plan with topics, priorities,
                                 source estimates, and search keywords.

        Example:
            >>> planner = PlannerAgent(model="gpt-4")
            >>> prompt = "Research climate change impact on agriculture"
            >>> plan = await planner.create_research_plan(prompt)
            >>> for topic in plan.result.topics:
            ...     print(f"{topic.topic}: {topic.keywords}")
        """
        # Phase One: Extract primary topics with priorities and source estimates
        user_prompt = f"Enriched Prompt: {enriched_prompt}"
        phase_one_response = await self.phase_one_agent.run(user_prompt)
        primary_topics = phase_one_response.result

        # Phase Two: Generate search keywords for each identified topic
        user_prompt = f"Phase One Output: {primary_topics}"
        phase_two_response = await self.phase_two_agent.run(user_prompt)
        
        return phase_two_response
    
if __name__ == "__main__":
    async def main():
        planner_agent = PlannerAgent(model="moonshotai/kimi-k2:free")
        enriched_prompt = (
            "Research the impact of climate change on global agriculture. "
            "Focus on changes in crop yields, shifts in agricultural zones, "
            "and the socio-economic effects on farming communities worldwide."
        )
        research_plan = await planner_agent.create_research_plan(enriched_prompt)

        for i in range(len(research_plan.result.topics)):
            print(research_plan.result.topics[i])

    asyncio.run(main())