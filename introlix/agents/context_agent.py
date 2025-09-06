"""
The Context Agent is responsible for gathering all necessary information from the user
before research begins. It expands vague or incomplete queries into detailed, 
well-scoped prompts by asking clarification questions when required.

Input Format:
==============================================================================
QUERY: <original user query>
ANSWER_TO_QUESTIONS: <user's answers to previous clarification questions>
USER_FILES: <list of uploaded file metadata and extracted content summaries>
RESEARCH_SCOPE: <narrow | medium | comprehensive>
==============================================================================

Output Format:
==============================================================================
QUESTIONS: <list of clarification questions to ask the user, if more context is needed>
MOVE_NEXT: <true | false>
CONFIDENCE_LEVEL: <0.0-1.0 score indicating certainty about having enough context>
FINAL_PROMPT: <detailed and enriched prompt consolidating user query and answers>
RESEARCH_PARAMETERS: {
    "estimated_duration": "<short | medium | long>",
    "complexity_level": "<basic | intermediate | advanced>",
    "required_sources": "<academic | news | mixed | technical>",
    "research_depth": "<surface | detailed | comprehensive>"
}
==============================================================================

Notes:
------
- Maximum 5 clarification questions per iteration to avoid user fatigue
- CONFIDENCE_LEVEL helps determine if borderline cases should proceed
- RESEARCH_PARAMETERS guide downstream agent behavior and resource allocation
- If uploaded files contain relevant context, integrate them into FINAL_PROMPT
- Track conversation history to avoid repeating questions
"""