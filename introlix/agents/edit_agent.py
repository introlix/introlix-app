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
    """Structured tool call from LLM"""

    name: str
    input: Dict[str, Any]


class AgentDecision(BaseModel):
    """LLM decision output"""

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
    "answer": "the fully edited document content",  // if type is "final". THIS MUST BE THE FULL DOCUMENT CONTENT, NOT JUST A SNIPPET.
    "needs_more_info": true/false  // whether you need another iteration
}}

Guidelines:
1. If the user asks to rewrite, summarize, or expand, do so while maintaining the document's tone unless asked otherwise.
2. If you need external information to fulfill the request (e.g., "Add a section about the latest GDP figures"), use the search tool.
3. When you are ready to provide the edited document, set type="final" and put the COMPLETE edited text in the "answer" field.
4. Do NOT output conversational text in the "answer" field (like "Here is the edited text"). ONLY output the document content itself.
5. If the user request is a question about the document that doesn't require editing, you should still "edit" it by returning the original content (maybe with a note? No, the user said "instead of answering questions it can edit documents"). Actually, if the user asks a question, maybe they want the answer inserted? Assume the user wants the document modified.
6. Always return the FULL document content in the final answer, even if only a small part changed.

Examples:

User Instruction: "Fix the typo in the first sentence."
CURRENT_CONTENT: "Thsi is a test."
Response: {{"type": "final", "thought": "Fixing typo 'Thsi' to 'This'", "answer": "This is a test."}}

User Instruction: "Add a paragraph about cats."
CURRENT_CONTENT: "Dogs are great."
Response: {{"type": "tool", "thought": "I can write about cats without search, or search if needed. I'll just write it.", "answer": "Dogs are great.\n\nCats are also popular pets, known for their independence and agility."}}
"""


class EditAgent(BaseAgent):
    def __init__(
        self,
        unique_id: str,
        model: str,
        current_content: str,
        config: Optional[AgentInput] = None,
        max_iterations=5,
        conversation_history: Optional[List[Dict]] = None,
    ):

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
        async def search(queries: List[str] = None, query: str = None) -> str:
            """Search tool that accepts both 'queries' and 'query' for flexibility"""
            print("Query is", queries)

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

            print(results)

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
        """Build messages array"""
        messages = [
            {"role": "system", "content": self.sys_prompt}
        ]
        
        # We don't necessarily need conversation history for editing, but maybe previous edits?
        # For now, let's stick to the current request context.
        
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

    async def _call_llm_with_messages(
        self, 
        messages: List[Dict], 
        stream: bool = False
    ):
        """Call LLM with messages array (ChatGPT style)"""
        from introlix.services.LLMState import LLMState
        
        llm_state = LLMState()
        response = await llm_state.get_open_router(
            model_name=self.model, 
            messages=messages,
            stream=stream
        )
        
        if stream:
            return response
        else:
            output = response.json()
            try:
                return output["choices"][0]["message"]["content"]
            except:
                return output

    def _build_prompt(self, user_prompt: str, state: Dict[str, Any]) -> PromptTemplate:
        pass

    async def run(self, user_prompt: str) -> str:
        """
        Run the agent and return the edited content.
        Note: This overrides the generator-based arun from ChatAgent/BaseAgent to return a single string.
        """
        state = {"history": [], "tool_results": {}}

        for iteration in range(self.max_iterations):
            messages = self._build_messages_array(user_prompt, state)

            # Call LLM (non-streaming for decision)
            raw_output = await self._call_llm_with_messages(messages=messages, stream=False)
            
            try:
                # Cleaning the raw_output
                raw_output = raw_output.strip()

                if '<｜begin of sentence｜>' in raw_output:
                    raw_output = raw_output.replace('<｜begin of sentence｜>', '')

                if '<｜end of sentence｜>' in raw_output:
                    raw_output = raw_output.replace('<｜end of sentence｜>', '')

                # Remove any trailing special characters
                raw_output = raw_output.strip().rstrip('<｜').rstrip(' ')

                # Extract JSON from markdown if present
                if "```json" in raw_output:
                    json_start = raw_output.find("```json") + 7
                    json_end = raw_output.find("```", json_start)
                    raw_output = raw_output[json_start:json_end].strip()
                elif "```" in raw_output:
                    json_start = raw_output.find("```") + 3
                    json_end = raw_output.find("```", json_start)
                    raw_output = raw_output[json_start:json_end].strip()
            except:
                pass
                
            # Parse decision
            try:
                decision = AgentDecision.model_validate_json(raw_output)
            except Exception as e:
                # Fallback parsing
                try:
                    decision_dict = json.loads(raw_output)
                    decision = AgentDecision(**decision_dict)
                except:
                    print(f"Error parsing decision: {raw_output}")
                    continue

            # Handle decision type
            if decision.type == "final":
                return decision.answer

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
