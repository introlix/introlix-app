from motor.motor_asyncio import AsyncIOMotorClient
from introlix.config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["research_db"]

# Helper to convert ObjectId to string
def serialize_doc(doc):
    if doc is None: 
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc
