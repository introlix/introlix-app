"""
Research Desk API endpoints for managing research workflows.

This module handles the lifecycle of research desks including:
- Creation and setup
- Context gathering via AI agents
- Research planning
- Document management
"""
import json
from datetime import datetime
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pymongo import DESCENDING
from introlix.models import (
    ResearchDesk,
    ResearchDeskRequest,
    ResearchDeskContextAgentRequest,
)
from introlix.schemas import PaginatedResponse
from introlix.utils.title_gen import generate_title
from introlix.database import db, validate_object_id, serialize_doc
from introlix.agents.context_agent import ContextAgent, ContextOutput, AgentInput
from introlix.agents.planner_agent import PlannerAgent
from introlix.agents.explorer_agent import ExplorerAgent

logger = logging.getLogger(__name__)

research_desk_router = APIRouter(
    prefix="/workspace/{workspace_id}/research-desk", tags=["research_desk"]
)


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
        model = "moonshotai/kimi-k2:free"
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
        model = "moonshotai/kimi-k2:free"
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
        model = "moonshotai/kimi-k2:free"
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
        explorer_agent = ExplorerAgent(queries=keywords[:20], unique_id=workspace_id, get_answer=False, get_multiple_answer=False, max_results=5, model=model)
        await explorer_agent.run()
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
