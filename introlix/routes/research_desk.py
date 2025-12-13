"""
Research Desk Routes Module

This module provides REST API endpoints for managing research desk workflows within workspaces.
Research desks guide users through a multi-stage research process using AI agents.

Workflow Stages:
----------------
1. **initial** - Desk created, awaiting setup
2. **context_agent** - Gathering context and clarifying research scope
3. **planner_agent** - Creating research plan with topics and keywords
4. **approve_plan** - User review and approval of research plan
5. **explorer_agent** - Searching internet and gathering information
6. **complete** - Research data collected, ready for document creation

Endpoints:
----------
- POST /new - Create a new research desk
- PATCH /{desk_id}/setup - Initialize desk with title generation
- PATCH /{desk_id}/setup/context-agent - Gather context via AI agent
- PATCH /{desk_id}/setup/planner-agent - Generate research plan
- PATCH /{desk_id}/setup/planner-agent/edit - Edit/approve research plan
- PATCH /{desk_id}/setup/explorer-agent - Execute internet search
- PATCH /{desk_id}/docs - Add/update documents
- POST /{desk_id}/edit-doc - Edit document using AI
- POST /{desk_id}/chat - Chat about the research/document
- GET / - List all research desks in workspace
- GET /{desk_id} - Get specific research desk details

Features:
---------
- Multi-stage AI-guided research workflow
- Automatic title generation
- Context gathering with clarifying questions
- Research planning with topics and keywords
- Internet search integration
- Document editing with AI assistance
- Chat interface for Q&A about research
- Conversation history persistence
"""
import json
from datetime import datetime
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from pymongo import DESCENDING
from introlix.models import (
    ResearchDesk,
    ResearchDeskRequest,
    ResearchDeskContextAgentRequest,
    EditDocRequest,
    Message
)
from introlix.schemas import PaginatedResponse
from introlix.utils.title_gen import generate_title
from introlix.database import db, validate_object_id, serialize_doc
from introlix.agents.context_agent import ContextAgent, ContextOutput, AgentInput
from introlix.agents.planner_agent import PlannerAgent
from introlix.agents.explorer_agent import ExplorerAgent
from introlix.agents.chat_agent import ChatAgent
from introlix.agents.edit_agent import EditAgent
from introlix.config import AUTO_MODEL

logger = logging.getLogger(__name__)

research_desk_router = APIRouter(
    prefix="/workspace/{workspace_id}/research-desk", tags=["research_desk"]
)

explorer_agent = ExplorerAgent()

@research_desk_router.post("/new")
async def create_research_desk(workspace_id: str, request: ResearchDesk):
    """
    Creating a new research desk.

    Args:
        workspace_id (str): ID of the workspace containing the research desk
        request: (ResearchDesk): Data for new workspace.

    returns:
        message: Success message
        _id: Id for created research desk.

    Raises:
        HTTPException: 404 if Workspace not found
    """
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    request.workspace_id = workspace_id
    request.state = "initial"
    item_dict = request.model_dump()
    result = await db.research_desks.insert_one(item_dict)
    return {"message": "Research Desk created", "_id": str(result.inserted_id)}


@research_desk_router.patch("/{desk_id}/setup")
async def setup_research_desk(
    workspace_id: str, desk_id: str, request: ResearchDeskRequest
):
    """
    Preparing a already existing research desk by adding a new title based on the prompt.

    Args:
        workspace_id (str): ID of the workspace containing the research desk
        desk_id (str): ID of the research desk.
        request: (ResearchDeskRequest): Data for research desk setup.

    Return: 
        message: Success Message
    
    Raises:
        HTTPException: 404 if workspace not found
        HTTPException: 400 if desk is already setup
        HTTPException: 500 if setup fail
    """
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    research_desks = await db.research_desks.find_one(
        {"_id": validate_object_id(desk_id)}
    )

    if not research_desks:
        raise HTTPException(
            status_code=400, detail="Research Desk does not exists for this workspace"
        )

    if research_desks.get("state") != "initial":
        raise HTTPException(status_code=400, detail="Research Desk is already setup")

    # Create a title for the research desk if not provided
    title = research_desks.get("title")

    if not title or title == "":
        # Title is missing, set it
        try:
            new_title = await generate_title(request.prompt)

            await db.research_desks.update_one(
                {"_id": research_desks["_id"]}, {"$set": {"title": new_title}}
            )

            # Update the workspace's updated_at field
            await db.workspaces.update_one(
                {"_id": validate_object_id(workspace_id)},
                {"$set": {"updated_at": datetime.now()}},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail="Setup failed")

    # Move to context agent state
    await db.research_desks.update_one(
        {"_id": research_desks["_id"]}, {"$set": {"state": "context_agent"}}
    )

    return {"message": "Research Desk set up"}


@research_desk_router.patch("/{desk_id}/setup/context-agent")
async def setup_research_desk_context_agent(
    workspace_id: str, desk_id: str, request: ResearchDeskContextAgentRequest
):
    """
    Enhance user prompt using context agent before setting up research desk.
    
    The context agent asks clarifying questions to better understand the research
    scope and builds a more detailed prompt for the research process.
    
    Args:
        workspace_id (str): ID of the workspace containing the research desk
        desk_id (str): ID of the research desk to enhance
        request (ResearchDeskContextAgentRequest): Contains the user prompt, answers to previous questions, and model preference
        
    Returns:
        dict: Contains questions for user, move_next flag, confidence level,
              final prompt if ready, and updated state
              
    Raises:
        HTTPException: 404 if workspace/desk not found
        HTTPException: 400 if desk is not in 'context_agent' state
        HTTPException: 500 if context agent processing fails
    """

    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desk
    research_desk = await db.research_desks.find_one(
        {"_id": validate_object_id(desk_id)}
    )
    if not research_desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")

    # Validate state
    if research_desk.get("state") != "context_agent":
        raise HTTPException(
            status_code=400,
            detail=f"Research Desk is in '{research_desk.get('state')}' state, expected 'context_agent'",
        )

    if request.model == "auto":
        model = AUTO_MODEL
    else:
        model = request.model

    # Get conversation 
    conv_history = []

    if research_desk.get("context_agent"):
        if research_desk.get("context_agent"):
            conv_history = research_desk.get("context_agent").get("conv_history")

    # Process with context agent
    try:
        config = AgentInput(
            name="ContextAgent",
            description="Context gathering before research",
            output_type=ContextOutput,
        )

        context_agent = ContextAgent(config=config, conversation_history=conv_history, model=model)

        output = await context_agent.process(
            query=request.prompt,
            answers=request.answers,
            research_scope=request.research_scope,
            user_files=request.user_files,
        )
    except Exception as e:
        logger.error(f"Context agent failed for research desk {desk_id}: {e}")
        raise HTTPException(status_code=500, detail="Context agent processing failed")

    # Determine next state
    next_state = "planner_agent" if output.move_next and output.confidence_level > 0.7 and output.final_prompt else "context_agent"

    # Updating the conv_history
    conv_history.append({
        "role": "user",
        "content": request.prompt
    })

    if request.answers:
        conv_history.append({
            "role": "user", 
            "content": f"Answers to previous questions: {request.answers}"
        })

    conv_history.append({
        "role": "assistant",
        "content": json.dumps(output.model_dump())
    })


    # Update research desk
    update_data = {
        "context_agent": {
            "conv_history": conv_history,
            "final_prompt": output.final_prompt,
            "research_parameters": output.research_parameters.model_dump(),
            "confidence_level": output.confidence_level,
            "questions": output.questions,
            "move_next": output.move_next,
            "timestamp": datetime.now(),
        },
        "state": next_state,
        "updated_at": datetime.now(),
    }

    await db.research_desks.update_one(
        {"_id": research_desk["_id"]}, {"$set": update_data}
    )

    # Update workspace timestamp
    await db.workspaces.update_one(
        {"_id": validate_object_id(workspace_id)},
        {"$set": {"updated_at": datetime.now()}},
    )

    return {
        "questions": output.questions,
        "move_next": output.move_next,
        "confidence_level": output.confidence_level,
        "final_prompt": output.final_prompt if output.move_next else None,
        "research_parameters": (
            output.research_parameters.model_dump() if output.move_next else None
        ),
        "state": next_state,
    }


@research_desk_router.patch("/{desk_id}/setup/planner-agent")
async def setup_research_desk_planner_agent(
    workspace_id: str, desk_id: str, model: str
):
    """
    Creating a dedicated plan for the research.
    
    The planner agent creates plan with keywords that will be searched on interent to find better articles/paper for the desk.
    
    Args:
        workspace_id (str): ID of the workspace containing the research desk
        desk_id (str): ID of the research desk to enhance
        model (str): Model to be used
        
    Returns:
        dict: Contains topic, priority, estimated_sources_needed and keywords.
              
    Raises:
        HTTPException: 404 if workspace/desk not found
        HTTPException: 400 if desk is not in 'planner_agent' state
        HTTPException: 500 if planner agent processing fails
    """

    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desk
    research_desk = await db.research_desks.find_one(
        {"_id": validate_object_id(desk_id)}
    )
    if not research_desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")

    # Validate state
    if research_desk.get("state") != "planner_agent":
        raise HTTPException(
            status_code=400,
            detail=f"Research Desk is in '{research_desk.get('state')}' state, expected 'planner_agent'",
        )

    if model == "auto":
        model = AUTO_MODEL
    else:
        model = model

    # Getting enhanced  
    enriched_prompt = research_desk.get("context_agent").get("final_prompt")

    # Process with planner agent
    try:
        planner_agent = PlannerAgent(model)

        output = await planner_agent.create_research_plan(enriched_prompt)
    except Exception as e:
        logger.error(f"Planner agent failed for research desk {desk_id}: {e}")
        raise HTTPException(status_code=500, detail="Planner agent processing failed")

    # Determine next state
    next_state = "approve_plan"


    # Update research desk
    output_data = []
    for i in range(len(output.result.topics)):
        data = {
            "topic": output.result.topics[i].topic,
            "priority": output.result.topics[i].priority,
            "estimated_sources_needed": output.result.topics[i].estimated_sources_needed,
            "keywords": output.result.topics[i].keywords,
        }
        output_data.append(data)


    update_data = {
        "planner_agent": {
            "topics": output_data
        },
        "state": next_state,
        "updated_at": datetime.now(),
    }

    await db.research_desks.update_one(
        {"_id": research_desk["_id"]}, {"$set": update_data}
    )

    # Update workspace timestamp
    await db.workspaces.update_one(
        {"_id": validate_object_id(workspace_id)},
        {"$set": {"updated_at": datetime.now()}},
    )

    return {
        "topics": output_data,
        "state": next_state,
    }


@research_desk_router.patch("/{desk_id}/setup/planner-agent/edit")
async def edit_research_desk_planner_agent(
    workspace_id: str, 
    desk_id: str,
    topics: List[Dict[str, Any]] = Body(...)
):
    """
    Edits the plan generated by planner agent.

    This is also used for confirm plan generated by planner agent. When plan is generated then state will be approve_plan rather
    explorer_agent. So, user can confirm the plan for edit it and then confirm and then it will move to explorer_agent.

    Args:
        workspace_id (str): ID of the workspace containing the research desk
        desk_id (str): ID of the research desk to enhance
        topics: (List[Dict[str, Any]]): The edited data data will be saved in DB.

    Returns: 
        dict: contains topics, state and message.

    Raises:
        HTTPException: 404 if workspace/desk not found
        HTTPException: 400 if desk is not in 'planner_agent' state
        HTTPException: 404 if there is any missing keys
    """

    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desk
    research_desk = await db.research_desks.find_one(
        {"_id": validate_object_id(desk_id)}
    )
    if not research_desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")

    # Validate state - should be in approve_plan state
    if research_desk.get("state") != "approve_plan":
        raise HTTPException(
            status_code=400,
            detail=f"Research Desk is in '{research_desk.get('state')}' state, expected 'approve_plan'",
        )

    # Get existing topics
    existing_topics = research_desk.get("planner_agent", {}).get("topics", [])
    
    # Check if data has actually changed
    data_changed = existing_topics != topics

    # Determine next state based on whether data changed
    next_state = "explorer_agent"

    # Validate topics structure
    for topic in topics:
        if not all(key in topic for key in ["topic", "priority", "estimated_sources_needed", "keywords"]):
            raise HTTPException(
                status_code=400,
                detail="Each topic must have: topic, priority, estimated_sources_needed, and keywords"
            )

    # Update research desk
    update_data = {
        "planner_agent.topics": topics,
        "state": next_state,
        "updated_at": datetime.now(),
    }

    await db.research_desks.update_one(
        {"_id": research_desk["_id"]}, 
        {"$set": update_data}
    )

    # Update workspace timestamp
    await db.workspaces.update_one(
        {"_id": validate_object_id(workspace_id)},
        {"$set": {"updated_at": datetime.now()}},
    )

    return {
        "topics": topics,
        "state": next_state,
        "message": "Research plan updated successfully" if data_changed else "No changes detected, moving to explorer_agent"
    }


@research_desk_router.patch("/{desk_id}/setup/explorer-agent")
async def setup_research_desk_explorer_agent(
    workspace_id: str, desk_id: str, model: str
):
    """
    Getting data from internet based on the keywords.

    The explorer agent gets data from internet based on the keywords and then stores it in the database.
    
    Args:
        workspace_id (str): ID of the workspace containing the research desk
        desk_id (str): ID of the research desk to enhance
        model (str): Model to be used
        
    Returns:
        dict: Contains status, code and message.
        
    Raises:
        HTTPException: 404 if workspace/desk not found
        HTTPException: 400 if desk is not in 'explorer_agent' state
        HTTPException: 500 if explorer agent processing fails
    """
    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desk
    research_desk = await db.research_desks.find_one(
        {"_id": validate_object_id(desk_id)}
    )
    if not research_desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")
    
        # Validate state - should be in explorer_agent state
    if research_desk.get("state") != "explorer_agent":
        raise HTTPException(
            status_code=400,
            detail=f"Research Desk is in '{research_desk.get('state')}' state, expected 'explorer_agent'",
        )
    
    if model == "auto":
        model = AUTO_MODEL
    else:
        model = model

    # Getting keywords from plan to search
    keywords = []
    
    if research_desk.get("planner_agent"):
        topics = [x for x in research_desk.get("planner_agent", {}).get("topics", []) if x.get("priority") == "high"]
        for topic in topics:
            keywords.extend(topic.get("keywords", []))
    
    if len(keywords) == 0:
        raise HTTPException(status_code=400, detail="No keywords found in the plan")

    try:
        await explorer_agent.run(queries=keywords[:20], unique_id=workspace_id, get_answer=False, max_results=5)
    except Exception as e:
        logger.error(f"Explorer agent failed for research desk {desk_id}: {e}")
        raise HTTPException(status_code=500, detail="Explorer agent processing failed")

    # move to complete state
    await db.research_desks.update_one(
        {"_id": research_desk["_id"]}, {"$set": {"state": "complete"}}
    )

    # Update workspace timestamp
    await db.workspaces.update_one(
        {"_id": validate_object_id(workspace_id)},
        {"$set": {"updated_at": datetime.now()}},
    )
    
    return {"status": "success", "code": 200, "message": "Successfully got data from internet"}


@research_desk_router.patch("/{desk_id}/docs")
async def add_documents(workspace_id: str, desk_id: str, documents: dict):
    """
    Adding documents to the research desk.
    
    Args:
        workspace_id (str): ID of the workspace containing the research desk
        desk_id (str): ID of the research desk to enhance
        documents (dict): Contains the documents to be added
    """
    desk = await db.research_desks.find_one({"_id": validate_object_id(desk_id)})

    if not desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")

    await db.research_desks.update_one(
        {"_id": desk["_id"]}, {"$set": {"documents": documents}}
    )

    # Update the workspace's updated_at field
    await db.workspaces.update_one(
        {"_id": validate_object_id(workspace_id)},
        {"$set": {"updated_at": datetime.now()}},
    )

    return {"message": "Documents added to Research Desk"}


@research_desk_router.post("/{desk_id}/edit-doc")
async def edit_document(workspace_id: str, desk_id: str, request: EditDocRequest):
    """
    Edit a document using an AI agent.
    
    Args:
        workspace_id (str): ID of the workspace
        desk_id (str): ID of the research desk
        request (EditDocRequest): Contains prompt, model
        
    Returns:
        dict: Status message
    """
    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desk
    research_desk = await db.research_desks.find_one(
        {"_id": validate_object_id(desk_id)}
    )
    if not research_desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")

    if request.model == "auto":
        model = AUTO_MODEL
    else:
        model = request.model

    # Load chat history from database
    messages = research_desk.get("messages", [])

    # Getting the document written till now if written
    current_docs = research_desk.get("documents", {}) or {}
    if current_docs:
        currnet_content = current_docs["document"]["content"]
    else:
        currnet_content = ""

    # Getting final_prompt
    final_prompt = research_desk.get("context_agent", {}).get("final_prompt", "")

    # Initialize EditAgent
    edit_agent = EditAgent(
        unique_id=workspace_id,
        model=model,
        current_content=currnet_content,
        conversation_history=messages,
        final_prompt=final_prompt
    )

    try:
        # Run agent to get new content
        new_content = await edit_agent.run(request.prompt)
        
        # Update document in database
        if isinstance(current_docs, dict):
            current_docs["document"]["content"] = new_content

        # Create user message
        user_msg = Message(
            role="user",
            content=request.prompt,
            created_at=datetime.now()
        )

        if new_content:
            assistant_info = "I have updated the document based on your instructions."
        else:
            assistant_info = "Fail to update the document based on your instructions."

        # Create assistant message
        assistant_msg = Message(
            role="assistant",
            content=assistant_info,
            created_at=datetime.now(),
            model=model
        )

        await db.research_desks.update_one(
            {"_id": research_desk["_id"]},
            {
                "$set": {
                    "documents": current_docs,
                    "updated_at": datetime.now()
                },
                "$push": {
                    "messages": {"$each": [user_msg.model_dump(), assistant_msg.model_dump()]}
                }
            }
        )
        
        # Update workspace timestamp
        await db.workspaces.update_one(
            {"_id": validate_object_id(workspace_id)},
            {"$set": {"updated_at": datetime.now()}},
        )

        return {"status": "success", "message": "Document edited successfully"}

    except Exception as e:
        logger.error(f"Edit agent failed for research desk {desk_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Edit agent failed: {str(e)}")

@research_desk_router.post('/{desk_id}/chat')
async def chat(workspace_id: str, desk_id: str, request: ResearchDeskRequest):
    """
    Chat with AI about the research desk content.

    This endpoint provides an interactive chat interface where users can ask questions
    about their research desk and its documents. The AI has access to the document
    content and can provide informed responses.

    Workflow:
    1. Validates workspace and research desk
    2. Loads conversation history
    3. Includes document content in context if available
    4. Saves user message to database
    5. Streams AI response back to client
    6. Saves assistant response to database

    Args:
        workspace_id (str): The unique identifier of the workspace.
        desk_id (str): The unique identifier of the research desk.
        request (ResearchDeskRequest): The chat request containing:
            - prompt (str): The user's question/message
            - model (str): The model to use ("auto" or specific model name)

    Returns:
        StreamingResponse: A streaming response containing the AI's reply in real-time.

    Raises:
        HTTPException: 404 if workspace or research desk is not found.

    Features:
        - Document-aware responses (AI has access to desk documents)
        - Conversation history persistence
        - Real-time streaming responses
        - Automatic model selection when "auto" is specified

    Example:
        POST /workspace/123/research-desk/abc/chat
        Body: {"prompt": "Summarize the key findings", "model": "auto"}
        Response: Streaming text response from the AI
    """
    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desk
    research_desk = await db.research_desks.find_one(
        {"_id": validate_object_id(desk_id)}
    )
    if not research_desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")
    
    if request.model == "auto":
        model = AUTO_MODEL
    else:
        model = request.model

    # Load chat history from database
    messages = research_desk.get("messages", [])

    # Adding final_prompt from context_agent if it is first message only
    if not messages:
        final_prompt = research_desk.get("context_agent", {}).get("final_prompt", "")
        if final_prompt:
            request.prompt = f"Context: {final_prompt}\n\n{request.prompt}"

    # Adding document content to context if available on user prompt
    current_docs = research_desk.get("documents", {}) or {}
    if current_docs:
        doc_content = current_docs["document"]["content"]
        request.prompt = f"Document Content: {doc_content}\n\nUser Question: {request.prompt}"

    # Create user message
    user_message = Message(
        role="user",
        content=request.prompt,
        created_at=datetime.now()
    )

    # Add user message to database
    await db.research_desks.update_one(
        {"_id": research_desk["_id"]},
        {
            "$push": {"messages": user_message.model_dump()},
            "$set": {"updated_at": datetime.now()}
        }
    )

    # Initialize chat agent with history
    chat_agent = ChatAgent(
        unique_id=workspace_id, # This takes workspace_id as data are shared in between workspace
        model=model,
        conversation_history=messages
    )

    # Collect assistant response
    assistant_content = ""
    async def stream():
        nonlocal assistant_content
        async for chunk in chat_agent.arun(request.prompt):
            assistant_content += chunk
            yield chunk

        # After streaming completes, save assistant message
        assistant_message = Message(
            role="assistant",
            content=assistant_content,
            created_at=datetime.now(),
            model=model
        )

        await db.research_desks.update_one(
            {"_id": research_desk["_id"]},
            {
                "$push": {"messages": assistant_message.model_dump()},
                "$set": {"updated_at": datetime.now()}
            }
        )
            
    return StreamingResponse(stream(), media_type="text/plain")

@research_desk_router.get("/", response_model=PaginatedResponse)
async def get_desks(
    workspace_id: str, page: int = Query(1, ge=1), limit: int = Query(10, ge=1)
):
    """
    For getting list of research desks that exist in a workspace.

    Args:
        workspace_id (str): ID of the workspace containing the research desks
        page (int): Page number
        limit (int): Number of research desks per page
        
    Returns:
        dict: Contains items, total, page and limit.
        
    Raises:
        HTTPException: 404 if workspace not found
        HTTPException: 500 if getting research desks fails
    """
    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desks
    object_id = validate_object_id(workspace_id)

    desk_total = await db.research_desks.count_documents(
        {"workspace_id": str(object_id)}
    )
    desks = (
        db.research_desks.find(
            {"workspace_id": str(object_id)},
            {"_id": 1, "workspace_id": 1, "created_at": 1, "title": 1, "updated_at": 1},
        )
        .sort("updated_at", DESCENDING)
        .skip((page - 1) * limit)
        .limit(limit)
    )

    desks = [serialize_doc(desk) async for desk in desks]

    return {"items": desks, "total": desk_total, "page": page, "limit": limit}


@research_desk_router.get("/{desk_id}")
async def get_desk(workspace_id: str, desk_id: str):
    """
    For getting a specific research desk by its ID.
    
    Args:
        workspace_id (str): ID of the workspace containing the research desk
        desk_id (str): ID of the research desk to get
        
    Returns:
        dict: Contains research desk data.
        
    Raises:
        HTTPException: 404 if workspace/desk not found
    """
    # Validate workspace
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get research desk
    desk = await db.research_desks.find_one({"_id": validate_object_id(desk_id)})

    if not desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")

    return serialize_doc(desk)
