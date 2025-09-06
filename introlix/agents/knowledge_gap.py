"""
Identifies gaps, inconsistencies, and quality issues in verified research data.
Acts as the system's quality controller and workflow director, determining
next steps based on completeness analysis.

Input Format:
==============================================================================
QUERY: <enriched prompt from Context Agent>
VERIFIED_RESULTS: <approved sources and metadata from Verifier Agent>
CONFLICTS_DETECTED: <conflict information from Verifier Agent>
RESEARCH_PARAMETERS: <original scope and depth requirements>
ITERATION_HISTORY: <previous gap-filling attempts and their outcomes>
==============================================================================

Output Format:
==============================================================================
GAP_ANALYSIS: {
    "completeness_score": <0.0-1.0>,
    "identified_gaps": [
        {
            "gap_id": "<unique_identifier>",
            "topic": "<subject area with insufficient coverage>",
            "gap_type": "<missing_information | conflicting_information | insufficient_detail | methodological_weakness | temporal_gap | geographic_gap>",
            "severity": "<critical | important | minor>",
            "details": "<specific explanation of what's missing or problematic>",
            "suggested_search_terms": ["<keyword1>", "<keyword2>"],
            "required_source_types": ["<academic | government | industry | expert_opinion>"],
            "estimated_effort": "<low | medium | high>"
        }
    ],
    "quality_concerns": [
        {
            "concern_type": "<bias | outdated_information | insufficient_sources | geographic_bias | methodology_issues>",
            "affected_topics": ["<topic1>", "<topic2>"],
            "impact_level": "<high | medium | low>",
            "mitigation_strategy": "<additional_sources | expert_review | acknowledge_limitation>"
        }
    ]
}
WORKFLOW_DECISION: {
    "next_agent": "<Planner Agent | Explorer Agent | Researcher Agent>",
    "action_required": "<new_search | refined_planning | proceed_with_synthesis | expert_consultation>",
    "confidence_in_decision": <0.0-1.0>,
    "stopping_criteria_met": <true | false>,
    "iteration_limit_reached": <true | false>
}
RESEARCH_STATUS: {
    "completion_percentage": <0-100>,
    "research_quality": "<excellent | good | acceptable | needs_improvement>",
    "ready_for_synthesis": <true | false>,
    "critical_gaps_remaining": <number>,
    "estimated_additional_time": "<minutes | hours>"
}
==============================================================================

Notes:
------
- Maximum 3 gap-filling iterations to prevent infinite loops
- Consider user's original research parameters when assessing adequacy
- Prioritize critical gaps that affect core research objectives
- Track iteration_history to avoid repeated unsuccessful searches
- Balance thoroughness with practical time constraints
- Flag when expert human consultation might be beneficial
"""