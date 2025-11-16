from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from introlix.models import ChatRequest
from introlix.agents.chat_agent import ChatAgent
from introlix.models import WorkspaceChat, Message
from introlix.database import db, serialize_doc, validate_object_id
from introlix.services.LLMState import LLMState

chat_router = APIRouter(prefix='/workspace/{workspace_id}/chat', tags=['chat'])
llm_state = LLMState()

@chat_router.post('/new')
async def create_chat(workspace_id: str, request: WorkspaceChat):
    workspace = await db.workspaces.find_one({"_id": validate_object_id(workspace_id)})

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    request.workspace_id = workspace_id
    item_dict = request.model_dump()
    result = await db.chats.insert_one(item_dict)
    return {"message": "Chat created", "_id": str(result.inserted_id)}

@chat_router.post('/{chat_id}/')
async def chat(workspace_id: str, chat_id: str, request: ChatRequest):
    chat = await db.chats.find_one({"_id": validate_object_id(chat_id)})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    title = chat.get("title")

    if not title:
        # Title is missing, set it
        messages = [
            {"role": "system", "content": "You are a title generator for chatbot. Your task is to generate best by seeing user prompt. Don't response with any exta token. Just give a simple title."},
            {"role": "user", "content": request.prompt}
        ]
        response = await llm_state.get_open_router(
            model_name="qwen/qwen3-235b-a22b:free", 
            messages=messages,
            stream=False
        )
        output = response.json()
        
        try:
            new_title = output["choices"][0]["message"]["content"]
        except:
            new_title = output

        await db.chats.update_one(
            {"_id": chat["_id"]},
            {"$set": {"title": new_title}}
        )

        # Update the workspace's updated_at field
        await db.workspaces.update_one(
            {"_id": validate_object_id(workspace_id)},
            {"$set": {"updated_at": datetime.now()}}
        )
    
    if request.model == "auto":
        model = "moonshotai/kimi-k2:free"
    else:
        model = request.model

    # Load chat history from database
    messages = chat.get("messages", [])

    # Create user message
    user_message = Message(
        role="user",
        content=request.prompt,
        created_at=datetime.now()
    )

    # Add user message to database
    await db.chats.update_one(
        {"_id": chat["_id"]},
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

    if request.search:
        user_prompt = f"{request.prompt}\nSearch on the internet."
    else:
        user_prompt = request.prompt

    # Collect assistant response
    assistant_content = ""
    async def stream():
        nonlocal assistant_content
        async for chunk in chat_agent.arun(user_prompt):
            assistant_content += chunk
            yield chunk

        # After streaming completes, save assistant message
        assistant_message = Message(
            role="assistant",
            content=assistant_content,
            created_at=datetime.now(),
            model=model
        )

        await db.chats.update_one(
            {"_id": chat["_id"]},
            {
                "$push": {"messages": assistant_message.model_dump()},
                "$set": {"updated_at": datetime.now()}
            }
        )
            
    return StreamingResponse(stream(), media_type="text/plain")

@chat_router.get('/{chat_id}/')
async def get_chat(chat_id: str):
    """Get all the messages from a chat"""
    result = await db.chats.find_one({"_id": validate_object_id(chat_id)})

    if not result:
        return "No Chat Found"
    return serialize_doc(result)
@chat_router.delete('/{chat_id}/')
async def delete_chat(chat_id: str):
    """Delete a chat and its history"""
    result = await db.chats.delete_one({"_id": validate_object_id(chat_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"message": "Chat deleted successfully"}