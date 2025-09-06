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