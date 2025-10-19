from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from introlix.config import MONGO_URI
from bson import ObjectId

client = AsyncIOMotorClient(MONGO_URI)
db = client["research_db"]

# Helper to convert ObjectId to string
def serialize_doc(doc):
    if doc is None: 
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

# Helper function to validate ObjectId
def validate_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")