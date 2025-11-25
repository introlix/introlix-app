# API Documentation

This document provides comprehensive documentation for the Introlix REST API.

## Base URL

```
http://localhost:8000
```

In production, replace with your deployed API URL.

## Authentication

Currently, the API does not require authentication. This will be added in future versions.

---

## Table of Contents

- [Workspace Endpoints](#workspace-endpoints)
- [Chat Endpoints](#chat-endpoints)
- [Research Desk Endpoints](#research-desk-endpoints)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)

---

## Workspace Endpoints

### Create Workspace

Create a new workspace for organizing research and chats.

**Endpoint:** `POST /workspaces`

**Request Body:**
```json
{
  "name": "My Research Project",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "message": "Workspace created",
  "workspace": {
    "id": "507f1f77bcf86cd799439011",
    "name": "My Research Project",
    "user_id": "user123",
    "created_at": "2025-11-25T10:30:00Z",
    "updated_at": "2025-11-25T10:30:00Z"
  }
}
```

---

### Get All Workspaces

Retrieve a paginated list of all workspaces.

**Endpoint:** `GET /workspaces`

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 10) - Items per page

**Example:**
```
GET /workspaces?page=1&limit=10
```

**Response:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "My Research Project",
      "user_id": "user123",
      "created_at": "2025-11-25T10:30:00Z",
      "updated_at": "2025-11-25T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

---

### Get Workspace by ID

Retrieve a specific workspace by its ID.

**Endpoint:** `GET /workspaces/{id}`

**Parameters:**
- `id` (string) - Workspace ID

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "My Research Project",
  "user_id": "user123",
  "created_at": "2025-11-25T10:30:00Z",
  "updated_at": "2025-11-25T10:30:00Z"
}
```

---

### Get Workspace Items

Get all items (chats and research desks) in a workspace.

**Endpoint:** `GET /workspaces/{id}/items`

**Query Parameters:**
- `page` (integer, default: 1)
- `limit` (integer, default: 10)

**Response:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439012",
      "workspace_id": "507f1f77bcf86cd799439011",
      "type": "chat",
      "title": "AI Discussion",
      "created_at": "2025-11-25T10:30:00Z",
      "updated_at": "2025-11-25T10:30:00Z"
    },
    {
      "id": "507f1f77bcf86cd799439013",
      "workspace_id": "507f1f77bcf86cd799439011",
      "type": "desk",
      "title": "Machine Learning Research",
      "created_at": "2025-11-25T11:00:00Z",
      "updated_at": "2025-11-25T11:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 10
}
```

---

### Delete Workspace

Delete a workspace and all its associated items.

**Endpoint:** `DELETE /workspaces/{id}`

**Response:**
```json
{
  "message": "Workspace and related items deleted"
}
```

---

## Chat Endpoints

### Create Chat

Create a new chat session in a workspace.

**Endpoint:** `POST /workspace/{workspace_id}/chat`

**Request Body:**
```json
{
  "title": "AI Discussion"
}
```

**Response:**
```json
{
  "message": "Chat created",
  "id": "507f1f77bcf86cd799439012"
}
```

---

### Send Chat Message (Streaming)

Send a message to the chat and receive a streaming response.

**Endpoint:** `POST /workspace/{workspace_id}/chat/{chat_id}`

**Request Body:**
```json
{
  "prompt": "What is machine learning?",
  "model": "auto",
  "search": true,
  "agent": "chat"
}
```

**Parameters:**
- `prompt` (string) - User's message
- `model` (string) - LLM model to use ("auto" for default)
- `search` (boolean) - Enable internet search
- `agent` (string) - Agent type ("chat")

**Response:** Server-Sent Events (SSE) stream

```
data: {"type": "thought", "content": "I need to search for information about machine learning"}

data: {"type": "tool", "name": "search", "status": "running"}

data: {"type": "tool", "name": "search", "status": "complete", "result": "Found 10 results"}

data: {"type": "answer", "content": "Machine learning is..."}

data: {"type": "done"}
```

---

### Get Chat

Retrieve a specific chat with its message history.

**Endpoint:** `GET /workspace/{workspace_id}/chat/{chat_id}`

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "workspace_id": "507f1f77bcf86cd799439011",
  "title": "AI Discussion",
  "messages": [
    {
      "id": "msg1",
      "role": "user",
      "content": "What is machine learning?",
      "created_at": "2025-11-25T10:30:00Z"
    },
    {
      "id": "msg2",
      "role": "assistant",
      "content": "Machine learning is...",
      "created_at": "2025-11-25T10:30:05Z",
      "model": "gemini-2.5-flash"
    }
  ],
  "created_at": "2025-11-25T10:30:00Z",
  "updated_at": "2025-11-25T10:30:05Z"
}
```

---

### Get All Chats

Get all chats in a workspace.

**Endpoint:** `GET /workspace/{workspace_id}/chat`

**Query Parameters:**
- `page` (integer, default: 1)
- `limit` (integer, default: 10)

**Response:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439012",
      "workspace_id": "507f1f77bcf86cd799439011",
      "title": "AI Discussion",
      "created_at": "2025-11-25T10:30:00Z",
      "updated_at": "2025-11-25T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

---

## Research Desk Endpoints

### Create Research Desk

Create a new research desk in a workspace.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk`

**Request Body:**
```json
{
  "title": "Machine Learning Research"
}
```

**Response:**
```json
{
  "message": "Research desk created",
  "id": "507f1f77bcf86cd799439013"
}
```

---

### Setup Research Desk (Initial)

Initialize a research desk with a topic and generate a title.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk/{desk_id}/setup`

**Request Body:**
```json
{
  "prompt": "I want to research the latest developments in transformer models",
  "model": "auto"
}
```

**Response:**
```json
{
  "message": "Research desk setup complete",
  "title": "Latest Developments in Transformer Models",
  "state": "context_agent"
}
```

---

### Context Agent

Enhance the research prompt by answering clarifying questions.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk/{desk_id}/context-agent`

**Request Body:**
```json
{
  "prompt": "I want to research transformer models",
  "model": "auto",
  "answers": "I'm interested in recent architectures from 2023-2025, focusing on efficiency improvements",
  "research_scope": "broad",
  "user_files": []
}
```

**Parameters:**
- `prompt` (string) - Original research topic
- `model` (string) - LLM model
- `answers` (string, optional) - Answers to previous questions
- `research_scope` (string) - "narrow", "broad", or "comprehensive"
- `user_files` (array, optional) - User-uploaded files

**Response (Streaming):**

If more questions needed:
```
data: {"type": "questions", "questions": ["What specific aspects interest you?", "What time period?"]}
```

If ready to proceed:
```
data: {"type": "complete", "final_prompt": "Research recent transformer architectures...", "state": "planner_agent"}
```

---

### Planner Agent

Generate a research plan with topics and keywords.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk/{desk_id}/planner-agent`

**Query Parameters:**
- `model` (string) - LLM model to use

**Response (Streaming):**
```
data: {"type": "plan", "topics": [...]}

data: {"type": "complete", "state": "approve_plan"}
```

**Plan Structure:**
```json
{
  "topics": [
    {
      "topic": "Efficient Transformer Architectures",
      "keywords": [
        "FlashAttention",
        "Linear attention mechanisms",
        "Sparse transformers"
      ]
    }
  ]
}
```

---

### Edit Research Plan

Modify the generated research plan.

**Endpoint:** `PUT /workspace/{workspace_id}/research-desk/{desk_id}/planner-agent`

**Request Body:**
```json
{
  "topics": [
    {
      "topic": "Efficient Transformer Architectures",
      "keywords": ["FlashAttention", "Linear attention"]
    }
  ]
}
```

**Response:**
```json
{
  "message": "Plan updated successfully",
  "state": "explorer_agent"
}
```

---

### Explorer Agent

Execute the research plan by searching the internet.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk/{desk_id}/explorer-agent`

**Query Parameters:**
- `model` (string) - LLM model to use

**Response (Streaming):**
```
data: {"type": "status", "message": "Searching for: FlashAttention"}

data: {"type": "progress", "current": 1, "total": 5}

data: {"type": "result", "title": "FlashAttention Paper", "url": "..."}

data: {"type": "complete", "state": "complete", "results_count": 25}
```

---

### Add Documents

Manually add documents to a research desk.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk/{desk_id}/documents`

**Request Body:**
```json
{
  "documents": {
    "doc1": {
      "title": "My Document",
      "content": "Document content here..."
    }
  }
}
```

**Response:**
```json
{
  "message": "Documents added successfully"
}
```

---

### Edit Document with AI

Use AI to edit a research desk document.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk/{desk_id}/edit`

**Request Body:**
```json
{
  "prompt": "Add a section about FlashAttention with examples",
  "model": "auto"
}
```

**Response (Streaming):**
```
data: {"type": "status", "message": "Analyzing document..."}

data: {"type": "edit", "content": "Updated content..."}

data: {"type": "complete"}
```

---

### Chat with Research Desk

Ask questions about the research desk content.

**Endpoint:** `POST /workspace/{workspace_id}/research-desk/{desk_id}/chat`

**Request Body:**
```json
{
  "prompt": "What are the main findings about FlashAttention?",
  "model": "auto"
}
```

**Response (Streaming):**
```
data: {"type": "thought", "content": "Searching through research documents..."}

data: {"type": "answer", "content": "Based on the research, FlashAttention..."}

data: {"type": "done"}
```

---

### Get Research Desk

Retrieve a specific research desk with all its data.

**Endpoint:** `GET /workspace/{workspace_id}/research-desk/{desk_id}`

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "workspace_id": "507f1f77bcf86cd799439011",
  "state": "complete",
  "title": "Latest Developments in Transformer Models",
  "documents": {
    "doc1": {
      "title": "Research Document",
      "content": "..."
    }
  },
  "context_agent": {
    "final_prompt": "...",
    "confidence_level": 0.95
  },
  "planner_agent": {
    "topics": [...]
  },
  "messages": [],
  "created_at": "2025-11-25T11:00:00Z",
  "updated_at": "2025-11-25T12:00:00Z"
}
```

---

### Get All Research Desks

Get all research desks in a workspace.

**Endpoint:** `GET /workspace/{workspace_id}/research-desk`

**Query Parameters:**
- `page` (integer, default: 1)
- `limit` (integer, default: 10)

**Response:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439013",
      "workspace_id": "507f1f77bcf86cd799439011",
      "title": "Latest Developments in Transformer Models",
      "state": "complete",
      "created_at": "2025-11-25T11:00:00Z",
      "updated_at": "2025-11-25T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

---

## Response Formats

### Paginated Response

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 10
}
```

### Streaming Response (SSE)

Server-Sent Events format:

```
data: {"type": "...", "content": "..."}

data: {"type": "done"}
```

**Event Types:**
- `thought` - Agent's reasoning
- `tool` - Tool execution status
- `answer` - Final answer chunk
- `status` - Status update
- `progress` - Progress indicator
- `complete` - Operation complete
- `done` - Stream finished

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Common Errors

**404 Not Found:**
```json
{
  "detail": "Workspace not found"
}
```

**400 Bad Request:**
```json
{
  "detail": "Research desk is not in 'context_agent' state"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "prompt"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

Currently, there are no rate limits. This may change in future versions.

---

## Versioning

The API is currently in version 1. The base path includes the version:

```
/api/v1/...
```

Future versions will be released as:
```
/api/v2/...
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- See request/response schemas
- Test endpoints directly
- Download OpenAPI specification

---

## Examples

### Python Example

```python
import requests

# Create workspace
response = requests.post(
    "http://localhost:8000/workspaces",
    json={
        "name": "My Research",
        "user_id": "user123"
    }
)
workspace = response.json()["workspace"]

# Create research desk
response = requests.post(
    f"http://localhost:8000/workspace/{workspace['id']}/research-desk",
    json={"title": "AI Research"}
)
desk_id = response.json()["id"]

# Setup research desk
response = requests.post(
    f"http://localhost:8000/workspace/{workspace['id']}/research-desk/{desk_id}/setup",
    json={
        "prompt": "Research transformer models",
        "model": "auto"
    }
)
print(response.json())
```

### JavaScript Example

```javascript
// Create workspace
const workspace = await fetch('http://localhost:8000/workspaces', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'My Research',
    user_id: 'user123'
  })
}).then(r => r.json());

// Create chat
const chat = await fetch(
  `http://localhost:8000/workspace/${workspace.workspace.id}/chat`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: 'AI Discussion' })
  }
).then(r => r.json());

// Send message (streaming)
const response = await fetch(
  `http://localhost:8000/workspace/${workspace.workspace.id}/chat/${chat.id}`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: 'What is AI?',
      model: 'auto',
      search: true,
      agent: 'chat'
    })
  }
);

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log(data);
    }
  }
}
```

---

## Future Endpoints (Beta)

These endpoints are planned for future releases:

### Export Document

```
POST /workspace/{workspace_id}/research-desk/{desk_id}/export
```

**Request:**
```json
{
  "format": "pdf|docx|markdown|blogpost|research_paper",
  "include_references": true
}
```

### Format Document

```
POST /workspace/{workspace_id}/research-desk/{desk_id}/format
```

**Request:**
```json
{
  "style": "blogpost|research_paper|article",
  "add_references": true,
  "citation_style": "apa|mla|chicago"
}
```

---

For more information, visit the [interactive documentation](http://localhost:8000/docs).
