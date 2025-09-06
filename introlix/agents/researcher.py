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