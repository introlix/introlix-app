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

logger = logging.getLogger(__name__)

research_desk_router = APIRouter(
    prefix="/workspace/{workspace_id}/research-desk", tags=["research_desk"]
)


@research_desk_router.post("/new")
async def create_research_desk(workspace_id: str, request: ResearchDesk):
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
    """Preparing a already existing research desk for a workspace."""
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
    """Enhance user prompt using context agent before setting up research desk."""

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
    """Build plan for research desk"""

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
            detail=f"Research Desk is in '{research_desk.get('state')}' state, expected 'context_agent'",
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
        logger.error(f"Context agent failed for research desk {desk_id}: {e}")
        raise HTTPException(status_code=500, detail="Context agent processing failed")

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
    """Edit the research plan topics"""

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
        "data_changed": data_changed,
        "message": "Research plan updated successfully" if data_changed else "No changes detected, moving to explorer_agent"
    }


@research_desk_router.patch("/{desk_id}/docs")
async def add_documents(workspace_id: str, desk_id: str, documents: dict):
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
    desk = await db.research_desks.find_one({"_id": validate_object_id(desk_id)})

    if not desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")

    return serialize_doc(desk)
