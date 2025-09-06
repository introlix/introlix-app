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