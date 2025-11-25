"""
The Verifier Agent validates information quality, checks for conflicts,
and ensures source credibility. It operates as a critical quality gate
before information reaches the synthesis phase.

Input Format:
==============================================================================
SEARCH_RESULTS: <structured results from Explorer Agent>
VERIFICATION_CRITERIA: <strict | moderate | lenient>
CONFLICT_TOLERANCE: <low | medium | high>
==============================================================================

Output Format:
==============================================================================
VERIFIED_RESULTS: {
    "approved_sources": [
        {
            "original_source": <source object from Explorer Agent>,
            "verification_score": <0.0-1.0>,
            "verification_notes": "<reasons for approval>",
            "fact_check_status": "<verified | partially_verified | unverified>",
            "cross_reference_count": <number of confirming sources>
        }
    ],
    "rejected_sources": [
        {
            "original_source": <source object>,
            "rejection_reason": "<low_quality | outdated | unreliable | duplicate>",
            "rejection_details": "<specific explanation>"
        }
    ]
}
QUALITY_ASSESSMENT: {
    "overall_confidence": <0.0-1.0>,
    "source_diversity": "<high | medium | low>",
    "temporal_coverage": "<current | recent | mixed | outdated>",
    "geographic_representation": ["<regions/countries represented>"],
    "source_type_distribution": {"academic": <count>, "news": <count>, "other": <count>}
}
CONFLICTS_DETECTED: [
    {
        "topic": "<specific subject of conflict>",
        "conflict_type": "<factual_disagreement | methodological_difference | temporal_discrepancy>",
        "conflicting_sources": [<source objects>],
        "severity": "<high | medium | low>",
        "resolution_suggestion": "<additional_research | expert_consultation | acknowledge_uncertainty>"
    }
]
VERIFICATION_METADATA: {
    "sources_processed": <number>,
    "approval_rate": <percentage>,
    "processing_time": <seconds>,
    "manual_review_required": [<sources needing human verification>]
}
==============================================================================

Notes:
------
- Cross-reference facts across multiple sources when possible
- Flag sources requiring manual expert review for complex technical topics
- Consider publication date relevance based on research topic (recent for current events, broader for historical)
- Implement bias detection for politically sensitive topics
- Track verification_score methodology for transparency
- Escalate high-severity conflicts to Knowledge Gap Agent
"""
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput

class VerifiedResult(BaseModel):
    """
    Represents an approved source with verification details.

    Attributes:
        original_source (dict): The original source object from Explorer Agent.
        verification_score (float): Score between 0.0 and 1.0 indicating verification confidence.
        verification_notes (str): Explanation of why the source was approved.
        fact_check_status (str): Status - 'verified', 'partially_verified', or 'unverified'.
        cross_reference_count (int): Number of other sources confirming this information.
    """
    original_source: dict = Field(description="The original source object from Explorer Agent")
    verification_score: float = Field(description="Verification score between 0.0 and 1.0")
    verification_notes: str = Field(description="Reasons for approval")
    fact_check_status: str = Field(description="Fact check status: verified, partially_verified, unverified")
    cross_reference_count: int = Field(description="Number of confirming sources")

class RejectedSource(BaseModel):
    """
    Represents a rejected source with rejection details.

    Attributes:
        original_source (dict): The original source object.
        rejection_reason (str): Reason - 'low_quality', 'outdated', 'unreliable', or 'duplicate'.
        rejection_details (str): Specific explanation for why the source was rejected.
    """
    original_source: dict = Field(description="The original source object")
    rejection_reason: str = Field(description="Rejection reason: low_quality, outdated, unreliable, duplicate")
    rejection_details: str = Field(description="Specific explanation for rejection")

class VerifierAgentOutput(BaseModel):
    """
    Complete output from the Verifier Agent's validation process.

    This model contains approved and rejected sources, quality assessments,
    detected conflicts, and verification metadata.

    Attributes:
        approved_sources (list[VerifiedResult]): Sources that passed verification.
        rejected_sources (list[RejectedSource]): Sources that failed verification.
        overall_confidence (float): Overall confidence in the information set (0.0-1.0).
        source_diversity (str): Diversity of sources - 'high', 'medium', or 'low'.
        temporal_coverage (str): Time coverage - 'current', 'recent', 'mixed', or 'outdated'.
        geographic_representation (list): Regions/countries represented in sources.
        source_type_distribution (dict): Count of each source type (academic, news, etc.).
        conflicts_detected (list): Detected conflicts between sources.
        verification_metadata (dict): Metadata about the verification process.
    """
    approved_sources: list[VerifiedResult] = Field(description="List of approved sources with verification details")
    rejected_sources: list[RejectedSource] = Field(description="List of rejected sources with reasons")
    overall_confidence: float = Field(description="Overall confidence score between 0.0 and 1.0")
    source_diversity: str = Field(description="Source diversity: high, medium, low")
    temporal_coverage: str = Field(description="Temporal coverage: current, recent, mixed, outdated")
    geographic_representation: list = Field(description="List of regions/countries represented")
    source_type_distribution: dict = Field(description="Distribution of source types with counts")
    conflicts_detected: list = Field(description="List of detected conflicts with details")
    verification_metadata: dict = Field(description="Metadata about the verification process")

INSTRUCTIONS = f"""
You are the Verifier Agent. Your task is to validate the quality and reliability of information
sourced by the Explorer Agent. You will assess each source based on predefined verification criteria,
check for conflicting information, and ensure that the sources meet the required standards for credibility
and relevance. Your output will include a list of approved sources with verification details, rejected sources
with reasons for rejection, and an overall quality assessment of the information set.

Today's date is {datetime.now().strftime("%Y-%m-%d")}

You will be given:
1. SEARCH_RESULTS: Structured results from the Explorer Agent, including source details and content.
2. VERIFICATION_CRITERIA: The strictness level for verification (strict, moderate, lenient).
3. CONFLICT_TOLERANCE: The level of tolerance for conflicting information (low, medium, high).

OBJECTIVES:
1. Evaluate each source against the VERIFICATION_CRITERIA, considering factors such as credibility,
   relevance, publication date, and potential biases.
2. Identify and document any conflicting information, categorizing conflicts by type and severity.
3. Provide a comprehensive output that includes:
   - A list of approved sources with verification scores and notes.
   - A list of rejected sources with specific reasons for rejection.
   - An overall quality assessment of the information set, including confidence levels and source diversity.
   - Detailed metadata about the verification process, including processing time and sources needing manual review.

Your response should be in the following JSON format:
{{
    "approved_sources": [
        {{
            "original_source": <source object from Explorer Agent>,
            "verification_score": <0.0-1.0>,
            "verification_notes": "<reasons for approval>",
            "fact_check_status": "<verified | partially_verified | unverified>",
            "cross_reference_count": <number of confirming sources>
        }}
    ],
    "rejected_sources": [
        {{
            "original_source": <source object>,
            "rejection_reason": "<low_quality | outdated | unreliable | duplicate>",
            "rejection_details": "<specific explanation>"
        }}
    ],
    "overall_confidence": <0.0-1.0>,
    "source_diversity": "<high | medium | low>",
    "temporal_coverage": "<current | recent | mixed | outdated>",
    "geographic_representation": ["<regions/countries represented>"],
    "source_type_distribution": {{"academic": <count>, "news": <count>, "other": <count>}},
    "conflicts_detected": [
        {{
            "topic": "<specific subject of conflict>",
            "conflict_type": "<factual_disagreement | methodological_difference | temporal_discrepancy>",
            "conflicting_sources": [<source objects>],
            "severity": "<high | medium | low>",
            "resolution_suggestion": "<additional_research | expert_consultation | acknowledge_uncertainty>"
        }}
    ],
    "verification_metadata": {{
        "sources_processed": <number>,
        "approval_rate": <percentage>,
        "processing_time": <seconds>,
        "manual_review_required": [<sources needing human verification>]
    }}
}}
Make sure to only respond with the JSON format specified above and nothing else.
"""

class VerifierAgent:
    """
    The Verifier Agent validates information quality and ensures source credibility.

    This agent acts as a critical quality gate before information reaches the synthesis
    phase. It evaluates sources based on credibility, relevance, and temporal validity,
    detects conflicts between sources, and provides comprehensive quality assessments.

    Key Responsibilities:
    1. Validate source quality and credibility
    2. Cross-reference facts across multiple sources
    3. Detect and categorize conflicts in information
    4. Assess source diversity and temporal coverage
    5. Flag sources requiring manual expert review
    6. Provide verification scores and detailed notes

    Verification Criteria:
    - Source credibility and authority
    - Publication date relevance
    - Potential biases
    - Cross-reference availability
    - Content quality and depth

    Attributes:
        INSTRUCTIONS (str): The system prompt defining agent behavior.
        agent_config (AgentInput): Configuration for the agent.
        verifier_agent (Agent): The underlying LLM agent for verification.
    """

    def __init__(self):
        """
        Initializes the VerifierAgent with default configuration.
        """
        self.INSTRUCTIONS = INSTRUCTIONS
        
        self.agent_config = AgentInput(
            name="Verifier Agent",
            description="Validates information quality, checks for conflicts, and ensures source credibility.",
            output_type=VerifierAgentOutput
        )

        self.verifier_agent = Agent(
            model="qwen/qwen3-235b-a22b:free",
            instruction=self.INSTRUCTIONS,
            output_model_class=VerifierAgentOutput,
            config=self.agent_config
        )
    
    async def verify_sources(self, search_results: list, verification_criteria: str, conflict_tolerance: str) -> VerifierAgentOutput:
        """
        Uses the Verifier Agent to validate the quality and reliability of information sourced by the Explorer Agent.

        Args:
            search_results (str): Structured results from the Explorer Agent.
            verification_criteria (str): The strictness level for verification (strict, moderate, lenient).
            conflict_tolerance (str): The level of tolerance for conflicting information (low, medium, high).
        Returns:
            VerifierAgentOutput: The verified results with quality assessment and conflicts detected.
        """
        user_prompt = (
            f"SEARCH_RESULTS: {search_results}\n"
            f"VERIFICATION_CRITERIA: {verification_criteria}\n"
            f"CONFLICT_TOLERANCE: {conflict_tolerance}\n"
        )

        response = await self.verifier_agent.run(
            user_prompt=user_prompt
        )

        return response.result
    
if __name__ == "__main__":
    async def main():
        verifier = VerifierAgent()
        search_results = [
            {"source_id": 1, "content": "Coding is dying out.", "source_type": "news", "publication_date": "2023-10-01", "credibility_score": 0.8},
            {"source_id": 2, "content": "AI will replace all jobs.", "source_type": "academic", "publication_date": "2022-05-15", "credibility_score": 0.9},
            {"source_id": 3, "content": "Programming is evolving.", "source_type": "blog", "publication_date": "2021-0820", "credibility_score": 0.6}
        ]
        verification_criteria = "strict"
        conflict_tolerance = "low"
        
        output = await verifier.verify_sources(search_results, verification_criteria, conflict_tolerance)
        print(output)
    
    asyncio.run(main())