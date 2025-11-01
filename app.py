from pinecone import Pinecone
from introlix.config import PINECONE_KEY
from fastapi import FastAPI, HTTPException, Query
from introlix.database import db, serialize_doc, validate_object_id
from introlix.models import Workspace
from introlix.schemas import PaginatedResponse
from introlix.routes.chat import chat_router
from introlix.routes.research_desk import research_desk_router
from fastapi.middleware.cors import CORSMiddleware
from pymongo import DESCENDING

app = FastAPI(title="Introlix OS", openapi_prefix='/api/v1')
pc = Pinecone(api_key=PINECONE_KEY)

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
    cursor = db.workspaces.find().sort("updated_at", DESCENDING).skip(skip).limit(limit)
    workspaces = [serialize_doc(w) async for w in cursor]
    return {"items": workspaces, "total": total, "page": page, "limit": limit}

# Get all items in every workspaces (chats, deep research, research desk, etc.)
@app.get("/workspaces/items", response_model=PaginatedResponse, tags=["workspace"])
async def get_all_workspace_items(page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    # get chats related to the workspace
    chat_total = await db.chats.count_documents({})
    chats = db.chats.find(
        {},
        {"_id": 1, "workspace_id": 1, "created_at": 1, "title": 1, "updated_at": 1}
    ).sort("updated_at", DESCENDING).skip((page - 1) * limit).limit(limit)
    chat_list = [serialize_doc(chat) async for chat in chats]

    for chat in chat_list:
        chat["type"] = "chat"

    # TODO: After getting chats, get other items like deep research add research desk and mix it with chat_list
    items = chat_list  # currently only chats
    return {"items": items, "total": chat_total, "page": page, "limit": limit}

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
    
    # Delete Search Data
    try:
        index = pc.Index("explored-data-index")
        index.delete(namespace="Search", filter = {"unique_id": id})
    except:
        pass # No data to delete
    
    # Now delete workspace items
    # Delete chats
    await db.chats.delete_many({"workspace_id": str(object_id)})
    # TODO: Delete other related items like deep research, research desk, etc.

    return {"message": "Workspace and related items deleted"}

# Get all items related to a workspace (chats, deep research, research desk, etc.)
@app.get("/workspaces/{id}/items", response_model=PaginatedResponse, tags=["workspace"])
async def get_workspace_items(id: str, page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    object_id = validate_object_id(id)
    # get chats related to the workspace
    chat_total = await db.chats.count_documents({"workspace_id": str(object_id)})
    chats = db.chats.find(
        {"workspace_id": str(object_id)},
        {"_id": 1, "workspace_id": 1, "created_at": 1, "title": 1, "updated_at": 1}
    ).sort("updated_at", DESCENDING).skip((page - 1) * limit).limit(limit)
    chat_list = [serialize_doc(chat) async for chat in chats]

    # TODO: After getting chats, get other items like deep research add research desk and mix it with chat_list
    items = chat_list  # currently only chats
    return {"items": items, "total": chat_total, "page": page, "limit": limit}

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# basic routes

app.include_router(chat_router)
app.include_router(research_desk_router)