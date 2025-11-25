"""
Document Editing Agent Module

This module provides the EditAgent class, a specialized agent for editing and writing
documents with internet search capabilities. Key features include:

- Document content modification based on user instructions
- Internet search integration for fact verification and new information
- Maintains complete document structure (returns full documents, not diffs)
- Special output format using <<<DOC_CONTENT>>> markers to avoid JSON parsing issues
- Support for various editing operations (rewriting, summarizing, expanding)

The EditAgent uses a unique approach where the JSON decision and document content
are separated, allowing it to handle large text blocks without JSON parsing errors.
"""

import json
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator
from introlix.agents.baseclass import (
    AgentInput,
    BaseAgent,
    PromptTemplate,
    Tool,
)
from introlix.agents.explorer_agent import ExplorerAgent


class ToolCall(BaseModel):
    """
    Represents a structured tool call request from the LLM.

    Attributes:
        name (str): The name of the tool to call.
        input (Dict[str, Any]): The input parameters for the tool.
    """

    name: str
    input: Dict[str, Any]


class AgentDecision(BaseModel):
    """
    Represents the LLM's decision output for document editing.

    This model structures the agent's reasoning and next actions, including
    whether to use tools, continue processing, or finalize the edited document.

    Attributes:
        type (str): Action type - 'tool' (use a tool), 'final' (complete), or 'continue'.
        thought (Optional[str]): The agent's reasoning process.
        tool_calls (Optional[List[ToolCall]]): Tools to call in parallel if type is 'tool'.
        answer (Optional[str]): Final answer or placeholder if type is 'final'.
        needs_more_info (bool): Whether another iteration is needed for more information.
    """

    type: str = Field(description="Action type: 'tool', 'final', or 'continue'")
    thought: Optional[str] = Field(default=None, description="Agent's reasoning")
    tool_calls: Optional[List[ToolCall]] = Field(
        default=None, description="Tools to call in parallel"
    )
    answer: Optional[str] = Field(
        default=None, description="Final answer if type is 'final'"
    )
    needs_more_info: Optional[bool] = Field(
        default=False, description="Whether more information is needed"
    )


INSTRUCTION = """
You are Introlix Edit Agent, a specialized AI for editing and writing documents.
Your task is to modify the provided document content based on the user's instructions.
You have access to internet search using the search tool if you need to verify facts or gather new information to include in the document.

You will be provided with:
1. The current content of the document (labeled as CURRENT_CONTENT).
2. The user's request/instruction (labeled as USER_INSTRUCTION).

Your goal is to produce the NEW_CONTENT of the document.

Decision format (respond in JSON):
{{
    "type": "tool" | "final",
    "thought": "your reasoning",
    "tool_calls": [{{"name": "tool_name", "input": {{...}}}}],  // if type is "tool"
    "answer": "See below",  // if type is "final", put the content OUTSIDE the JSON wrapped in <<<DOC_CONTENT>>> markers.
    "needs_more_info": true/false  // whether you need another iteration
}}

Guidelines:
1. If the user asks to rewrite, summarize, or expand, do so while maintaining the document's tone unless asked otherwise.
2. If you need external information to fulfill the request (e.g., "Add a section about the latest GDP figures"), use the search tool.
3. When you are ready to provide the edited document, set type="final".
4. IMPORTANT: To avoid JSON parsing errors with large text, DO NOT put the document content inside the JSON "answer" field. Instead, output the JSON decision first, and then output the document content wrapped in <<<DOC_CONTENT>>> markers.
5. Always return the FULL document content in the final answer, even if only a small part changed.
6. DOC_CONTENT always should be in markdown format. Also ensure proper JSON formatting to avoid parsing issues.

Examples:

User Instruction: "Fix the typo in the first sentence."
CURRENT_CONTENT: "Thsi is a test."
Response: 
{{"type": "final", "thought": "Fixing typo 'Thsi' to 'This'"}}
<<<DOC_CONTENT>>>
This is a test.
<<<DOC_CONTENT>>>

User Instruction: "Add a paragraph about cats."
CURRENT_CONTENT: "Dogs are great."
Response: 
{{"type": "tool", "thought": "I can write about cats without search, or search if needed. I'll just write it.", "tool_calls": []}}
<<<DOC_CONTENT>>>
Dogs are great.

Cats are also popular pets, known for their independence and agility.
<<<DOC_CONTENT>>>

User Instruction: "Add a paragraph about best llm."
CURRENT_CONTENT: "Dogs are great."
Response: 
{{"type": "tool", "thought": "I need to search about best llm", "tool_calls": [{{"name": "search", "input": {{"queries": ["Best LLM in the world"]}}}}]}}
<<<DOC_CONTENT>>>
About Best LLM content
<<<DOC_CONTENT>>>

NOTE:
When editing documents, always return the COMPLETE document with all changes applied:

1. **Include all content**: The returned document must contain both:
   - The modified sections with your edits
   - All unchanged sections from the original document

2. **Avoid content loss**: Never replace the full document with only:
   - Just the changed portions
   - Just the previous version
   - A summary or abbreviated version

3. **Preserve structure**: Maintain the original document's:
   - Formatting
   - Section order
   - Unchanged paragraphs and content

4. **Example workflow**:
   - Original document has sections A, B, C, D
   - User requests changes to section B
   - Return: Complete document with sections A, B (edited), C, D

**In summary**: Think of document editing as creating a new complete version, not a patch or diff. The output should be ready to use as a standalone document with all original content preserved except where explicitly modified.
"""


class EditAgent(BaseAgent):
    """
    An intelligent agent specialized for editing and writing documents.

    The EditAgent modifies document content based on user instructions, with the ability
    to search the internet for facts or additional information when needed. It maintains
    the complete document structure and returns the full edited content.

    Key Features:
    1. Document editing (rewriting, summarizing, expanding)
    2. Internet search integration for fact verification
    3. Maintains document structure and formatting
    4. Returns complete documents (not diffs or patches)
    5. Supports iterative refinement with tool usage

    The agent uses a special output format with <<<DOC_CONTENT>>> markers to separate
    the JSON decision from the actual document content, avoiding JSON parsing issues
    with large text blocks.

    Attributes:
        unique_id (str): Unique identifier for the session/user.
        current_content (str): The current content of the document being edited.
        tools (List[Dict]): Available tools (primarily search).
        sys_prompt (str): The system prompt defining agent behavior.
        conversation_history (List[Dict]): History of the conversation for context.
    """

    def __init__(
        self,
        unique_id: str,
        model: str,
        current_content: str,
        config: Optional[AgentInput] = None,
        max_iterations=5,
        conversation_history: Optional[List[Dict]] = None,
    ):
        """
        Initialize the EditAgent.

        Args:
            unique_id (str): Unique identifier for the session/user.
            model (str): The name of the LLM model to use.
            current_content (str): The current document content to be edited.
            config (Optional[AgentInput]): Configuration for the agent. If None, a default config
                                           with search tools is created.
            max_iterations (int): Maximum number of reasoning/tool-use steps. Defaults to 5.
            conversation_history (Optional[List[Dict]]): Existing conversation history. Defaults to None.
        """

        if config is None:
            config = AgentInput(
                name="EditAgent",
                description="An intelligent agent that can edit documents",
                tools=self._create_tools(),
            )
        super().__init__(model, config, max_iterations)

        self.unique_id = unique_id
        self.current_content = current_content
        self.tools = [{"name": "search", "description": "Search on internet."}]

        self.sys_prompt = INSTRUCTION.format(tools=self.tools)
        self.conversation_history = conversation_history or []

    def _create_tools(self):
        """
        Creates the default tools for the agent, specifically the search tool.

        The search tool uses the ExplorerAgent to perform internet searches and
        format results with topics, summaries, sources, and relevance scores.

        Returns:
            List[Tool]: A list of Tool objects available to the agent.
        """
        async def search(queries: List[str] = None, query: str = None) -> str:
            """
            Search tool that accepts both 'queries' (list) and 'query' (single string) for flexibility.

            Args:
                queries (List[str], optional): List of search queries to execute.
                query (str, optional): Single search query (converted to list internally).

            Returns:
                str: Formatted search results with topics, summaries, sources, and relevance scores.
            """

            # Handle query format
            if query is not None and queries is None:
                queries = [query]
            elif queries is None:
                return "Error: No search queries provided"
            
            explorer = ExplorerAgent(
                queries=queries,
                unique_id=self.unique_id,
                get_answer=True,
                get_multiple_answer=False,
                max_results=2,
                model=self.model,
            )

            results = await explorer.run()

            formatted = []
            for result in results:
                try:
                    if hasattr(result, 'summary'):
                        # It's an object
                        formatted.append(
                            f"Topic: {result.topic}\n"
                            f"Summary: {result.summary}\n"
                            f"Sources: {', '.join(result.urls)}\n"
                            f"Relevance: {result.relevance_score}"
                        )
                    elif isinstance(result, dict):
                        # It's a dict
                        formatted.append(
                            f"Topic: {result.get('topic', 'N/A')}\n"
                            f"Summary: {result.get('summary', 'N/A')}\n"
                            f"Sources: {', '.join(result.get('urls', []))}\n"
                            f"Relevance: {result.get('relevance_score', 'N/A')}"
                        )
                    else:
                        # Unknown format, convert to string
                        formatted.append(f"Result: {str(result)}")
                except Exception as e:
                    formatted.append(f"Error processing result: {str(e)}")

            if not formatted:
                return "No results found"
            
            return "\n\n---\n\n".join(formatted)

        return [
            Tool(
                name="search",
                description="Search the internet for information. Use this tool when you need current data or facts you don't know. IMPORTANT: Input must be a dictionary with 'queries' key containing a list of search queries. For single searches, pass one query in the list; for multiple searches, pass multiple queries. Examples: Single search: {'queries': ['weather in Paris']} | Multiple searches: {'queries': ['GPT-5 features', 'Gemini 2.5 features']} | Always use 'queries' (plural) not 'query'.",
                function=search
            )
        ]

    def _build_messages_array(self, user_prompt: str, state: Dict[str, Any]) -> List[Dict]:
        """
        Constructs the message array for the LLM, including system prompt and conversation history.

        This method:
        1. Adds the system prompt with editing instructions
        2. Includes recent conversation history (last 10 messages)
        3. Formats the current document content and user instruction
        4. Adds any tool results from previous iterations

        Args:
            user_prompt (str): The user's editing instruction.
            state (Dict[str, Any]): Current execution state including tool results and history.

        Returns:
            List[Dict]: A list of message dictionaries formatted for the LLM.
        """
        messages = [
            {"role": "system", "content": self.sys_prompt}
        ]
        
        # Add conversation history (last 10 messages to manage tokens)
        recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        
        for msg in recent_history:
            role = msg.get("role")
            content = msg.get("content")
            if role in ["user", "assistant"] and content:
                messages.append({"role": role, "content": content})
        
        # Build current user prompt with tool results if any
        current_prompt_parts = [
            f"CURRENT_CONTENT:\n{self.current_content}\n",
            f"USER_INSTRUCTION: {user_prompt}"
        ]
        
        if state.get("tool_results"):
            current_prompt_parts.append("\nTool Results:")
            for tool_name, result in state["tool_results"].items():
                current_prompt_parts.append(f"\n{tool_name}:\n{result}")
        
        if state.get("history"):
            last_step = state["history"][-1]
            if last_step.get("parsed"):
                parsed = last_step["parsed"]
                if isinstance(parsed, dict) and parsed.get("needs_more_info"):
                    current_prompt_parts.append(
                        "\n\nYou indicated you need more info. What do you need next?"
                    )
        
        current_prompt_parts.append("\n\nYour decision (respond in JSON):")
        
        messages.append({
            "role": "user",
            "content": "\n".join(current_prompt_parts)
        })
        
        return messages

    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        """
        Legacy method required by BaseAgent but not used in this implementation.
        
        The EditAgent uses `_build_messages_array` instead to support conversation history.
        """
        pass

    async def run(self, user_prompt: str) -> str:
        """
        Executes the editing agent and returns the edited document content.

        This method orchestrates the entire editing workflow:
        1. Iterates up to `max_iterations` times
        2. Builds messages and calls the LLM for decisions
        3. Parses the response, extracting both JSON decision and document content
        4. Executes tools (search) if requested
        5. Returns the final edited document when type='final'

        The agent uses a special format where the document content is wrapped in
        <<<DOC_CONTENT>>> markers to avoid JSON parsing issues with large text.

        Args:
            user_prompt (str): The user's editing instruction.

        Returns:
            str: The complete edited document content in markdown format.

        Note:
            This overrides the generator-based arun from ChatAgent/BaseAgent to return
            a single string instead of streaming chunks.
        """
        state = {"history": [], "tool_results": {}}

        for iteration in range(self.max_iterations):
            messages = self._build_messages_array(user_prompt, state)

            # Call LLM (non-streaming for decision)
            raw_output = await self._call_llm_with_messages(messages=messages, stream=False)
            
            # Check for DOC_CONTENT block
            doc_content = None
            raw_output_json = raw_output
            
            if "<<<DOC_CONTENT>>>" in raw_output:
                parts = raw_output.split("<<<DOC_CONTENT>>>")
                if len(parts) >= 2:
                    # parts[0] is the JSON (hopefully)
                    # parts[1] is the content
                    raw_output_json = parts[0]
                    doc_content = parts[1].strip()
                    # If there's a closing tag, ignore what's after
                    if len(parts) > 2:
                         doc_content = parts[1].strip() # Take the middle part
            
            try:
                # Cleaning the raw_output_json
                raw_output_json = raw_output_json.strip()

                if '<｜begin of sentence｜>' in raw_output_json:
                    raw_output_json = raw_output_json.replace('<｜begin of sentence｜>', '')

                if '<｜end of sentence｜>' in raw_output_json:
                    raw_output_json = raw_output_json.replace('<｜end of sentence｜>', '')

                # Remove any trailing special characters
                raw_output_json = raw_output_json.strip().rstrip('<｜').rstrip(' ')

                # Extract JSON from markdown if present
                if "```json" in raw_output_json:
                    json_start = raw_output_json.find("```json") + 7
                    json_end = raw_output_json.find("```", json_start)
                    raw_output_json = raw_output_json[json_start:json_end].strip()
                elif "```" in raw_output_json:
                    json_start = raw_output_json.find("```") + 3
                    json_end = raw_output_json.find("```", json_start)
                    raw_output_json = raw_output_json[json_start:json_end].strip()
            except:
                pass
                
            # Parse decision
            try:
                decision = AgentDecision.model_validate_json(raw_output_json)
            except Exception as e:
                # Fallback parsing
                try:
                    decision_dict = json.loads(raw_output_json)
                    decision = AgentDecision(**decision_dict)
                except:
                    print(f"Error parsing decision: {raw_output_json}")
                    # If we found doc_content, maybe we can assume it's final?
                    if doc_content:
                         return doc_content
                    continue

            # Handle decision type
            if decision.type == "final":
                if doc_content:
                    return doc_content
                elif decision.answer and decision.answer != "See below":
                    return decision.answer
                else:
                    # Fallback if answer is missing or "See below" but no content block found
                    return self.current_content

            elif decision.type == "tool" and decision.tool_calls:
                for tc in decision.tool_calls:
                    tool = next(
                        (t for t in self.config.tools if t.name == tc.name), None
                    )
                    if not tool:
                        state["tool_results"][tc.name] = f"Tool {tc.name} not found"
                        continue

                    try:
                        result = await tool.execute(tc.input)
                        state["tool_results"][tc.name] = result
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        state["tool_results"][tc.name] = error_msg

            # If no more information needed but not final? Should not happen if logic is correct.
            if not decision.needs_more_info and decision.type != "final":
                 # Force final answer generation if it gets stuck?
                 pass
        
        return self.current_content # Fallback to original if failed
