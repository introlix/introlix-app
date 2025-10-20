from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query
from introlix.database import db, serialize_doc, validate_object_id
from introlix.models import Workspace, WorkspaceItem
from introlix.schemas import PaginatedResponse
from introlix.routes.chat import chat_router
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Introlix OS", openapi_prefix='/api/v1')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# workspace endpoints
@app.post("/workspaces", tags=["workspace"])
async def create_workspace(workspace: Workspace):
    workspace_dict = workspace.model_dump()
    result = await db.workspaces.insert_one(workspace_dict)
    created_workspace = await db.workspaces.find_one({"_id": result.inserted_id})
    return {"message": "Workspace created", "workspace": serialize_doc(created_workspace)}

@app.get("/workspaces", response_model=PaginatedResponse, tags=["workspace"])
async def get_workspaces(page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    skip = (page - 1) * limit
    total = await db.workspaces.count_documents({})
    cursor = db.workspaces.find().skip(skip).limit(limit)
    workspaces = [serialize_doc(w) async for w in cursor]
    return {"items": workspaces, "total": total, "page": page, "limit": limit}

@app.get("/workspaces/{id}", tags=["workspace"])
async def get_workspace(id: str):
    workspace = await db.workspaces.find_one({"_id": validate_object_id(id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return serialize_doc(workspace)

@app.delete("/workspaces/{id}", tags=["workspace"])
async def delete_workspace(id: str):
    object_id = validate_object_id(id)
    result = await db.workspaces.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workspace not found")
    # Get the workspace id field if it exists, otherwise use the _id
    workspace = await db.workspaces.find_one({"_id": object_id})
    workspace_id = workspace.get("id", str(object_id)) if workspace else str(object_id)
    await db.workspace_items.delete_many({"workspace_id": workspace_id})
    return {"message": "Workspace and related items deleted"}

# workspace items
@app.post("/workspaces/{workspace_id}/items", tags=["workspace_item"])
async def create_workspace_item(workspace_id: str, item: WorkspaceItem):
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    item.workspace_id = workspace_id
    item_dict = item.model_dump()
    result = await db.workspace_items.insert_one(item_dict)
    created_item = await db.workspace_items.find_one({"_id": result.inserted_id})
    return {"message": "Workspace item created", "item": serialize_doc(created_item)}

@app.get("/workspaces/{workspace_id}/items", response_model=PaginatedResponse, tags=["workspace_item"])
async def get_workspace_items(
    workspace_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    skip = (page - 1) * limit
    total = await db.workspace_items.count_documents({"workspace_id": workspace_id})
    cursor = db.workspace_items.find({"workspace_id": workspace_id}).skip(skip).limit(limit)
    items = [serialize_doc(i) async for i in cursor]

    return {"items": items, "total": total, "page": page, "limit": limit}

@app.get("/workspaces/{workspace_id}/items/{item_id}", tags=["workspace_item"])
async def get_workspace_item(workspace_id: str, item_id: str):
    item = await db.workspace_items.find_one({"_id": validate_object_id(item_id), "workspace_id": workspace_id})
    if not item:
        raise HTTPException(status_code=404, detail="Workspace item not found")
    return serialize_doc(item)

@app.put("/workspaces/{workspace_id}/items/{item_id}", tags=["workspace_item"])
async def update_workspace_item(workspace_id: str, item_id: str, item: WorkspaceItem):
    update_data = item.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now()
    result = await db.workspace_items.update_one(
        {"_id": validate_object_id(item_id), "workspace_id": workspace_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Workspace item not found")
    return {"message": "Workspace item updated"}

@app.delete("/workspaces/{workspace_id}/items/{item_id}", tags=["workspace_item"])
async def delete_workspace_item(workspace_id: str, item_id: str):
    result = await db.workspace_items.delete_one(
        {"_id": validate_object_id(item_id), "workspace_id": workspace_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workspace item not found")
    return {"message": "Workspace item deleted"}

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# basic routes

app.include_router(chat_router)