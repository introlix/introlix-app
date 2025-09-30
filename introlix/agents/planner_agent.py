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
from pydantic import BaseModel, Field
from introlix.config import PINECONE_KEY
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput

class PhaseOneAgent(BaseModel):
    topic: str = Field(description="The topic of the research")
    priority: str = Field(description="Priority level: high, medium, low")
    estimated_sources_needed: int = Field(description="Estimated number of sources needed")

class PhaseOneAgentOutput(BaseModel):
    topics: list[PhaseOneAgent] = Field(description="List of primary topics with details")

class PhaseTwoAgent(BaseModel):
    topic: str = Field(description="The topic of the research")
    priority: str = Field(description="Priority level: high, medium, low")
    estimated_sources_needed: int = Field(description="Estimated number of sources needed")
    keywords: list = Field(description="Keywords to that will be searched")

class PhaseTwoAgentOutput(BaseModel):
    topics: list[PhaseTwoAgent] = Field(description="List of topics with keywords")
    
PHASE_ONE_AGENT_INSTRUCTIONS = """
You are the Phase One Agent of the Planner Agent. Your task is to analyze the enriched prompt and
extract the primary research topics. For each topic, determine its priority (high, medium, low) and estimate
the number of sources needed to cover it comprehensively. Make sure the topics are distinct and relevant to the research objectives.
And it should cover the entire scope of the research task. Based on the enriched prompt, provide a list of primary topics with their details.

Respond in the following JSON format:
{
  "topics": [
    {
      "topic": "<research topic>",
      "priority": "<high | medium | low>",
      "estimated_sources_needed": <number>
    }
  ]
}

Make sure to only respond with the JSON format specified above and nothing else.
"""

PHASE_TWO_AGENT_INSTRUCTIONS = """
You are the Phase Two Agent of the Planner Agent. Your task is to analyze the Phase One Agent output
and generate a list of keywords for each topic. These keywords will be used by the Explorer Agent to
search for relevant information. Ensure that the keywords are specific, relevant, and cover various aspects
of the topic. Take topic and  priority into consideration when generating keywords.

Respond in the following JSON format:
{
  "topics": [
    {
      "topic": "<research topic>",
      "priority": "<high | medium | low>",
      "estimated_sources_needed": <number>,
      "keywords": ["<keyword1>", "<keyword2>"]
    }
  ]
}

Make sure to only respond with the JSON format specified above and nothing else.

"""

class PlannerAgent:
    def __init__(self):
        """
        Initializes the PlannerAgent with necessary configurations.
        """
        self.PHASE_ONE_AGENT_INSTRUCTIONS = PHASE_ONE_AGENT_INSTRUCTIONS
        self.PHASE_TWO_AGENT_INSTRUCTIONS = PHASE_TWO_AGENT_INSTRUCTIONS

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
            model="qwen/qwen3-235b-a22b:free",
            instruction=self.PHASE_ONE_AGENT_INSTRUCTIONS,
            output_model_class=PhaseOneAgentOutput,
            config=self.phase_one_config
        )

        self.phase_two_agent = Agent(
            model="qwen/qwen3-235b-a22b:free",
            instruction=self.PHASE_TWO_AGENT_INSTRUCTIONS,
            output_model_class=PhaseTwoAgentOutput,
            config=self.phase_two_config
        )

    async def create_research_plan(self, enriched_prompt: str) -> PhaseTwoAgentOutput:
        """
        Creates a structured research plan from the enriched prompt.

        Args:
            enriched_prompt (str): The enriched prompt provided by the Context Agent.
        Returns:
            PhaseTwoAgentOutput: The final research plan with topics and keywords.
        """
        # Phase One: Extract primary topics
        user_prompt = f"Enriched Prompt: {enriched_prompt}"
        phase_one_response = await self.phase_one_agent.run(user_prompt)
        primary_topics = phase_one_response.result

        # Prepare input for Phase Two
        user_prompt = f"Phase One Output: {primary_topics}"

        # Phase Two: Generate keywords for each topic
        phase_two_response = await self.phase_two_agent.run(user_prompt)
        
        return phase_two_response
    
if __name__ == "__main__":
    async def main():
        planner_agent = PlannerAgent()
        enriched_prompt = (
            "Research the impact of climate change on global agriculture. "
            "Focus on changes in crop yields, shifts in agricultural zones, "
            "and the socio-economic effects on farming communities worldwide."
        )
        research_plan = await planner_agent.create_research_plan(enriched_prompt)
        print(research_plan)

    asyncio.run(main())