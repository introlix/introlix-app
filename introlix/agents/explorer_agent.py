"""
The Web Search Agent retrieves relevant information from the internet 
using SearXNG and web crawling. It operates on multiple topics in parallel
and generates structured summaries for efficient downstream processing.

Input Format:
==============================================================================
RESEARCH_PLAN: <structured plan from Planner Agent with topics and keywords>
EXECUTION_STRATEGY: <parallel | sequential | hybrid>
SEARCH_CONSTRAINTS: <optional limitations on sources, date ranges, languages>
==============================================================================

Output Format:
==============================================================================
SEARCH_RESULTS: [
    {
        "topic": "<research topic>",
        "sources_found": <number>,
        "summaries": [
            {
                "title": "<article title>",
                "url": "<source URL>",
                "summary": "<1-3 sentence summary>",
                "relevance_score": <0.0-1.0>,
                "publication_date": "<date>",
                "source_type": "<academic | news | blog | government | commercial>",
                "author": "<author if available>",
                "credibility_indicators": ["<peer_reviewed | established_publication | primary_source>"]
            }
        ]
    }
]
SEARCH_PERFORMANCE: {
    "total_sources_found": <number>,
    "average_relevance_score": <0.0-1.0>,
    "coverage_by_topic": {"<topic>": "<complete | partial | minimal>"},
    "search_time_seconds": <number>,
    "failed_searches": ["<topics or keywords that yielded poor results>"]
}
RECOMMENDATIONS: {
    "high_quality_sources": [<top 10 most relevant and credible sources>],
    "requires_verification": [<sources needing fact-checking>],
    "potential_duplicates": [<similar sources that might be redundant>]
}
==============================================================================

Notes:
------
- Implement relevance_score algorithm based on keyword matching and content quality
- Track credibility_indicators to assist Verifier Agent
- Include source_type to help categorize information types
- SEARCH_PERFORMANCE metrics help optimize future searches
- Limit summaries to essential information to reduce processing overhead
- Flag potential academic sources for priority verification
"""