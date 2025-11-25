"""
Synthesizes verified information into comprehensive research outputs.
Acts as the final synthesis engine, creating structured, well-referenced
research documents from validated data.

Input Format:
==============================================================================
QUERY: <enriched prompt from Context Agent>
VERIFIED_RESULTS: <all approved sources and verification metadata>
RESEARCH_PARAMETERS: <scope, depth, and format requirements>
OUTPUT_FORMAT: <research_report | academic_paper | executive_summary | presentation | custom>
SYNTHESIS_INSTRUCTIONS: <specific formatting or structural requirements>
==============================================================================

Output Format:
==============================================================================
RESEARCH_OUTPUT: {
    "executive_summary": "<concise overview of key findings>",
    "main_content": {
        "introduction": "<research context and objectives>",
        "methodology": "<approach used for information gathering and analysis>",
        "key_findings": [
            {
                "finding": "<specific research result>",
                "evidence": ["<supporting source citations>"],
                "confidence_level": "<high | medium | low>",
                "implications": "<what this finding means>"
            }
        ],
        "analysis": "<interpretation and synthesis of findings>",
        "limitations": "<acknowledged gaps or constraints>",
        "conclusions": "<final assessments and answers to research questions>",
        "recommendations": ["<actionable suggestions based on findings>"]
    },
    "appendices": {
        "source_bibliography": [<complete source references>],
        "methodology_details": "<detailed explanation of research process>",
        "conflicting_information": [<unresolved conflicts with explanations>],
        "areas_for_further_research": ["<suggested follow-up investigations>"]
    }
}
OUTPUT_METADATA: {
    "word_count": <number>,
    "source_count": <number>,
    "confidence_score": <0.0-1.0>,
    "research_depth": "<surface | detailed | comprehensive>",
    "completion_time": "<total research duration>",
    "quality_indicators": {
        "source_diversity": "<high | medium | low>",
        "evidence_strength": "<strong | moderate | weak>",
        "coverage_completeness": "<complete | mostly_complete | partial>"
    }
}
CITATION_FORMAT: "<APA | MLA | Chicago | IEEE | custom>"
REVISION_SUGGESTIONS: [
    {
        "section": "<specific section needing improvement>",
        "suggestion": "<recommended enhancement>",
        "priority": "<high | medium | low>"
    }
]
==============================================================================

Notes:
------
- Maintain clear traceability between claims and sources
- Acknowledge limitations and conflicting information transparently
- Structure content according to specified OUTPUT_FORMAT requirements
- Include confidence levels to help users assess information reliability
- Provide actionable recommendations when appropriate
- Generate multiple output formats if requested (summary + detailed report)
- Ensure proper citation formatting throughout the document
"""

import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput

class ResearcherAgentOutput(BaseModel):
    """
    Output structure from the Researcher Agent's synthesis process.

    Attributes:
        result (str): The final synthesized research output with structured content.
        references (list): List of all sources cited in the research output.
    """
    result: str = Field(description="The final synthesized research output")
    references: list = Field(description="List of all sources cited in the research output")

INSTRUCTIONS = f"""
You are the Researcher Agent. Your task is to synthesize verified information into a comprehensive research
output. You will create a structured, well-referenced document based on the provided verified results and
research parameters. Ensure clarity, coherence, and proper citation throughout the document. You should also address any conflicting information transparently
and acknowledge the limitations of the research. The final output should meet the specified format and quality standards.

Today's date is {datetime.now().strftime("%Y-%m-%d")}

You will be given:
1. QUERY: The enriched prompt from the Context Agent that outlines the research topic and objectives.
2. VERIFIED_RESULTS: A collection of all approved sources and verification metadata that you can use to
   support your synthesis.
3. RESEARCH_PARAMETERS: Details about the scope, depth, and format requirements for the research.

Based on this information, produce a research output that includes:
- An executive summary that provides a concise overview of the key findings.
- Main content sections including introduction, methodology, key findings, analysis,
  limitations, conclusions, and recommendations.
- Appendices with source bibliography, methodology details, conflicting information,
  and areas for further research.

Note: You will not have access to the all VERIFIED_RESULTS at once. So, don't think if anything is missing. Just work with what you have.

Your response should be in the following JSON format:
{{
    "result": "<the final synthesized research output>",
    "references": ["<list of all sources cited in the research output>"]
}}
Make sure to only respond with the JSON format specified above and nothing else.
"""

class ResearcherAgent:
    """
    The Researcher Agent synthesizes verified information into comprehensive research outputs.

    This agent acts as the final synthesis engine in the research pipeline, creating
    structured, well-referenced research documents from validated data. It produces
    professional research outputs with proper citations, analysis, and recommendations.

    Key Responsibilities:
    1. Synthesize verified information into coherent narratives
    2. Create structured research documents with multiple sections
    3. Ensure proper citation and source attribution
    4. Acknowledge limitations and conflicting information
    5. Provide actionable recommendations based on findings

    Output Sections:
    - Executive summary
    - Introduction and methodology
    - Key findings with evidence
    - Analysis and conclusions
    - Recommendations
    - Bibliography and appendices

    Attributes:
        INSTRUCTIONS (str): The system prompt defining agent behavior.
        agent_config (AgentInput): Configuration for the agent.
        researcher_agent (Agent): The underlying LLM agent for synthesis.
    """

    def __init__(self):
        """
        Initializes the ResearcherAgent with default configuration.
        """
        self.INSTRUCTIONS = INSTRUCTIONS
        
        self.agent_config = AgentInput(
            name="Researcher Agent",
            description="Synthesizes verified information into comprehensive research outputs.",
            output_type=ResearcherAgentOutput
        )

        self.researcher_agent = Agent(
            model="qwen/qwen3-235b-a22b:free",
            instruction=self.INSTRUCTIONS,
            output_model_class=ResearcherAgentOutput,
            config=self.agent_config
        )

    async def synthesize_research(self, query: str, verified_results: str, research_parameters: str) -> ResearcherAgentOutput:
        """
        Synthesizes verified information into a comprehensive research output.

        Args:
            query (str): The enriched prompt from the Context Agent.
            verified_results (str): All approved sources and verification metadata.
            research_parameters (str): Scope, depth, and format requirements for the research.

        Returns:
            ResearcherAgentOutput: The final synthesized research output with references.
        """
        user_prompt = (
            f"QUERY: {query}\n"
            f"VERIFIED_RESULTS: {verified_results}\n"
            f"RESEARCH_PARAMETERS: {research_parameters}\n"
        )

        response = await self.researcher_agent.run(user_prompt)
        return response.result
    
if __name__ == "__main__":
    async def main():
        researcher = ResearcherAgent()
        query = "What are the latest advancements in renewable energy technologies?"
        verified_results = "Source 1: ...; Source 2: ...; Source 3: ..."
        research_parameters = "Format: detailed report; Depth: comprehensive; Audience: academic"
        
        output = await researcher.synthesize_research(query, verified_results, research_parameters)
        print(output)

    asyncio.run(main())