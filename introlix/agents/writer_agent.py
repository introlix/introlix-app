"""
Writer Agent Module

This module provides the WriterAgent class, which transforms synthesized research
outputs into polished, well-structured written documents. Key capabilities include:

- Transform research data into coherent narratives
- Adapt writing style to target audience (academic, professional, general)
- Ensure proper citation of all sources
- Create structured documents with logical flow
- Support multiple output formats (research papers, summaries, reports)

The WriterAgent is the final step in the research pipeline, taking verified
information and creating publication-ready documents.
"""

import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput

class WriterAgentOutput(BaseModel):
    """
    Output structure from the Writer Agent's content creation process.

    Attributes:
        content (str): The final written document content.
        format (str): The format of the output (e.g., 'summary', 'detailed report', 'research paper').
        citations (list): List of all sources cited in the written content.
    """
    content: str = Field(description="The final written content")
    format: str = Field(description="The format of the output, e.g., 'summary', 'detailed report'")
    citations: list = Field(description="List of all sources cited in the written content")

INSTRUCTIONS = f"""
You are the Writer Agent. Your task is to take the synthesized research output and transform it into
a well-structured, coherent, and engaging written document. The document should be tailored to the
specified audience and purpose, ensuring clarity and readability. You should also ensure that all claims
are properly cited with the provided sources. The writing style should be appropriate for the intended audience,
whether it's academic, professional, or general public.

Today's date is {datetime.now().strftime("%Y-%m-%d")}

You will be given:
1. The original enriched prompt that outlines the research objectives and parameters.
2. The synthesized research output from the Researcher Agent, which includes verified information and references. (This will be in list format containg multiple parts of the research output)

OBJECTIVES:
1. You will create a structured final document that includes:
   - An introduction that sets the context and objectives.
   - Main content sections that present the findings in a logical flow.
   - A conclusion that summarizes key insights and implications.
2. Ensure that all information is clearly cited with the provided references.

Note: You will write this document in exact format as requested (e.g., summary, detailed report, research paper).

Your response should be in the following JSON format:
{{
    "content": "<the final written content>",
    "format": "<the format of the output, e.g., 'summary', 'detailed report'>",
    "citations": ["<list of all sources cited in the written content>"]
}}
Make sure to only respond with the JSON format specified above and nothing else.
"""

class WriterAgent:
    """
    The Writer Agent transforms synthesized research into polished written documents.

    This agent takes verified research outputs and creates well-structured, coherent,
    and engaging documents tailored to specific audiences and purposes. It ensures
    proper citation, clarity, and appropriate writing style.

    Key Responsibilities:
    1. Transform research outputs into structured documents
    2. Ensure proper citation of all sources
    3. Adapt writing style to target audience
    4. Create logical content flow and organization
    5. Maintain clarity and readability

    Output Formats:
    - Academic research papers
    - Executive summaries
    - Detailed reports
    - General audience articles
    - Custom formats as requested

    Attributes:
        INSTRUCTIONS (str): The system prompt defining agent behavior.
        agent_config (AgentInput): Configuration for the agent.
        writer_agent (Agent): The underlying LLM agent for content creation.
    """

    def __init__(self):
        """
        Initializes the WriterAgent with default configuration.
        """
        self.INSTRUCTIONS = INSTRUCTIONS
        
        self.agent_config = AgentInput(
            name="Writer Agent",
            description="Synthesizes verified information into comprehensive research outputs.",
            output_type=WriterAgentOutput
        )

        self.writer_agent = Agent(
            model="qwen/qwen3-235b-a22b:free",
            instruction=self.INSTRUCTIONS,
            output_model_class=WriterAgentOutput,
            config=self.agent_config
        )
    
    async def write_content(self, enriched_prompt: str, research_outputs: list) -> WriterAgentOutput:
        """
        Uses the Writer Agent to create a well-structured written document based on the research outputs.

        Args:
            enriched_prompt (str): The enriched prompt outlining the research objectives and parameters.
            research_outputs (list): A list of synthesized research outputs from the Researcher Agent.
        Returns:
            WriterAgentOutput: The final written content with citations.
        """
        research_outputs_str = "\n\n".join(research_outputs)

        user_prompt = f"enriched_prompt: {enriched_prompt}\n\n research_outputs: {research_outputs_str}"

        response = await self.writer_agent.run(
            user_prompt=user_prompt
        )

        return response.result
    
if __name__ == "__main__":
    import asyncio

    async def main():
        writer_agent = WriterAgent()
        enriched_prompt = "The impact of climate change on coastal cities. Make it in research paper"
        research_outputs = [
            '{"result": "Climate change is causing sea levels to rise, which threatens coastal cities with flooding and erosion.", "references": ["Source A", "Source B"]}',
            '{"result": "Adaptation strategies include building sea walls, restoring wetlands, and implementing early warning systems.", "references": ["Source C"]}'
        ]
        final_output = await writer_agent.write_content(enriched_prompt, research_outputs)
        print(final_output)

    asyncio.run(main())