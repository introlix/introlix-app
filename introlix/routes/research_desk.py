from datetime import datetime
from fastapi import APIRouter, HTTPException
from introlix.models import ResearchDesk
from introlix.database import db, validate_object_id, serialize_doc

research_desk_router = APIRouter(prefix='/workspace/{workspace_id}/research-desk', tags=['research_desk'])

@research_desk_router.post('/new')
async def create_research_desk(workspace_id: str, request: ResearchDesk):
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    request.workspace_id = workspace_id
    item_dict = request.model_dump()
    result = await db.research_desks.insert_one(item_dict)
    return {"message": "Research Desk created", "_id": str(result.inserted_id)}

@research_desk_router.patch('/{desk_id}/docs')
async def add_documents(workspace_id: str, desk_id: str, documents: dict):
    desk = await db.research_desks.find_one({"_id": validate_object_id(desk_id)})

    if not desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")
    
    await db.research_desks.update_one(
        {"_id": desk["_id"]},
        {"$set": {"documents": documents}}
    )

    # Update the workspace's updated_at field
    await db.workspaces.update_one(
        {"_id": validate_object_id(workspace_id)},
        {"$set": {"updated_at": datetime.now()}}
    )
    
    return {"message": "Documents added to Research Desk"}

@research_desk_router.get('/{desk_id}/docs')
async def get_desk(workspace_id: str, desk_id: str):
    desk = await db.research_desks.find_one({"_id": validate_object_id(desk_id)})

    if not desk:
        raise HTTPException(status_code=404, detail="Research Desk not found")
    
    return serialize_doc(desk)