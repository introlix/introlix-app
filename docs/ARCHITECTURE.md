# Architecture Documentation

This document provides an overview of the Introlix system architecture, design decisions, and component interactions.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Data Flow](#data-flow)
- [Agent System](#agent-system)
- [Database Schema](#database-schema)
- [External Services](#external-services)
- [Design Decisions](#design-decisions)

---

## System Overview

Introlix is a full-stack AI-powered research platform built with:

- **Backend**: Python/FastAPI with async support
- **Frontend**: Next.js/React with TypeScript
- **Database**: MongoDB for document storage
- **Vector DB**: Pinecone for semantic search
- **Search**: SearXNG for privacy-focused web search
- **LLM**: Multiple providers (OpenRouter, Google AI Studio)

### Key Components

1. **Multi-Agent System**: Specialized AI agents for different research tasks
2. **Research Desk Workflow**: Guided multi-stage research process
3. **Chat Interface**: Conversational AI with search capabilities
4. **Document Editor**: AI-assisted writing and editing
5. **Knowledge Management**: Vector-based semantic search

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Workspace  │  │     Chat     │  │ Research Desk│         │
│  │     Page     │  │  Interface   │  │   Workflow   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                     │
│                    ┌───────▼────────┐                           │
│                    │   API Client   │                           │
│                    │  (TanStack)    │                           │
│                    └───────┬────────┘                           │
└────────────────────────────┼──────────────────────────────────┘
                             │ HTTP/SSE
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    API Routes                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────────┐        │ │
│  │  │Workspace │  │   Chat   │  │ Research Desk   │        │ │
│  │  │  Routes  │  │  Routes  │  │     Routes      │        │ │
│  │  └────┬─────┘  └────┬─────┘  └────────┬────────┘        │ │
│  └───────┼─────────────┼─────────────────┼──────────────────┘ │
│          │             │                  │                    │
│  ┌───────▼─────────────▼──────────────────▼──────────────────┐│
│  │                  Agent System                              ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    ││
│  │  │   Chat   │ │ Context  │ │ Planner  │ │ Explorer │    ││
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │    ││
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    ││
│  │       │            │            │            │            ││
│  │  ┌────▼────────────▼────────────▼────────────▼─────┐     ││
│  │  │              Base Agent                          │     ││
│  │  │        (LLM Integration, Tool Execution)         │     ││
│  │  └────┬─────────────────────────────────────────────┘     ││
│  └───────┼────────────────────────────────────────────────────┘│
│          │                                                      │
│  ┌───────▼──────────────────────────────────────────────────┐ │
│  │                    Tools & Services                       │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │ │
│  │  │   Web    │  │   Web    │  │  Vector  │               │ │
│  │  │  Search  │  │ Crawler  │  │  Search  │               │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘               │ │
│  └───────┼─────────────┼─────────────┼────────────────────────┘│
└──────────┼─────────────┼─────────────┼─────────────────────────┘
           │             │             │
     ┌─────▼─────┐ ┌─────▼─────┐ ┌────▼────┐
     │  SearXNG  │ │  MongoDB  │ │Pinecone │
     │  (Search) │ │    (DB)   │ │(Vector) │
     └───────────┘ └───────────┘ └─────────┘
                         │
                    ┌────▼────┐
                    │   LLM   │
                    │Provider │
                    └─────────┘
```

---

## Backend Architecture

### FastAPI Application

**File**: `app.py`

Main application entry point with:
- CORS middleware for frontend communication
- Route registration
- Database connection
- Pinecone initialization

### Project Structure

```
introlix/
├── agents/              # AI agent implementations
│   ├── base_agent.py   # Base agent class
│   ├── baseclass.py    # Agent primitives
│   ├── chat_agent.py   # Chat agent
│   ├── context_agent.py # Context gathering
│   ├── planner_agent.py # Research planning
│   ├── explorer_agent.py # Web exploration
│   ├── edit_agent.py   # Document editing
│   └── writer_agent.py # Content generation
├── routes/             # API endpoints
│   ├── chat.py        # Chat endpoints
│   └── research_desk.py # Research desk endpoints
├── tools/              # Agent tools
│   ├── web_search.py  # SearXNG integration
│   └── web_crawler.py # Content extraction
├── services/           # Business logic
├── utils/              # Utility functions
├── models.py          # Pydantic models
├── schemas.py         # Response schemas
├── database.py        # MongoDB connection
├── llm_config.py      # LLM configuration
└── config.py          # App configuration
```

### API Layer

**Routes** handle HTTP requests and responses:
- Input validation with Pydantic
- Authentication (future)
- Error handling
- Response formatting

**Example Route**:
```python
@router.post("/workspace/{workspace_id}/chat/{chat_id}")
async def send_message(
    workspace_id: str,
    chat_id: str,
    request: ChatRequest
):
    # Validate workspace and chat exist
    # Initialize agent
    # Stream response
    pass
```

### Agent Layer

**Agents** implement AI logic:
- Inherit from `BaseAgent`
- Define tools and capabilities
- Handle reasoning loops
- Manage conversation state

**Agent Hierarchy**:
```
BaseAgent (abstract)
├── ChatAgent (conversational AI)
├── ContextAgent (question generation)
├── PlannerAgent (research planning)
├── ExplorerAgent (web search & extraction)
├── EditAgent (document editing)
└── WriterAgent (content generation)
```

### Tool Layer

**Tools** provide capabilities to agents:
- Web search via SearXNG
- Web page crawling and extraction
- Vector search in Pinecone
- File processing (future)

**Tool Interface**:
```python
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
```

### Data Layer

**MongoDB Collections**:
- `workspaces` - User workspaces
- `chats` - Chat sessions
- `research_desks` - Research desk data

**Pinecone Namespaces**:
- `Search` - Explored web content
- (Future: `Documents`, `Citations`)

---

## Frontend Architecture

### Next.js Application

**Framework**: Next.js 15 with App Router

**Key Features**:
- Server-side rendering (SSR)
- Client-side navigation
- API routes (not used, backend is separate)
- Image optimization

### Project Structure

```
web/src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── providers/         # Context providers
│   └── workspaces/        # Workspace pages
│       ├── [id]/          # Dynamic workspace routes
│       │   ├── chat/      # Chat interface
│       │   └── desk/      # Research desk interface
├── components/            # React components
│   ├── ui/               # Base UI components (Radix)
│   ├── chat/             # Chat components
│   ├── desk/             # Research desk components
│   └── workspace/        # Workspace components
├── hooks/                # Custom React hooks
│   ├── use-chat.ts       # Chat state management
│   ├── use-desk.ts       # Research desk state
│   └── use-streaming.ts  # SSE streaming
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   └── utils.ts         # Helper functions
└── types/               # TypeScript types
    └── index.ts
```

### Component Architecture

**Component Hierarchy**:
```
App
├── WorkspacePage
│   ├── Sidebar
│   │   ├── WorkspaceList
│   │   └── ItemList
│   └── MainContent
│       ├── ChatInterface
│       │   ├── MessageList
│       │   ├── MessageInput
│       │   └── StreamingIndicator
│       └── ResearchDesk
│           ├── DeskHeader
│           ├── TextEditor (Lexical)
│           ├── DeskAIPanel
│           │   ├── ModeSelector
│           │   ├── PromptInput
│           │   └── ResponseDisplay
│           └── PlanViewer
```

### State Management

**TanStack Query** for server state:
- Automatic caching
- Background refetching
- Optimistic updates
- Error handling

**React Hooks** for local state:
- `useState` for component state
- `useEffect` for side effects
- Custom hooks for complex logic

**Example Hook**:
```typescript
export function useChat(chatId: string) {
  const { data, isLoading } = useQuery({
    queryKey: ['chat', chatId],
    queryFn: () => api.getChat(chatId),
  });
  
  const sendMessage = useMutation({
    mutationFn: api.sendMessage,
    onSuccess: () => {
      queryClient.invalidateQueries(['chat', chatId]);
    },
  });
  
  return { chat: data, isLoading, sendMessage };
}
```

### Streaming Implementation

**Server-Sent Events (SSE)** for real-time updates:

```typescript
async function* streamResponse(url: string, body: any) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6));
      }
    }
  }
}
```

---

## Data Flow

### Chat Flow

1. **User sends message** → Frontend
2. **POST request** → Backend API
3. **Create ChatAgent** → Agent system
4. **Agent reasoning loop**:
   - Analyze user query
   - Decide if search needed
   - Execute search tool (if needed)
   - Generate response
5. **Stream response** → Frontend (SSE)
6. **Update UI** → Display message
7. **Save to DB** → MongoDB

### Research Desk Flow

1. **Create desk** → Initial state
2. **Setup** → Generate title, move to context_agent
3. **Context Agent**:
   - Ask clarifying questions
   - User provides answers
   - Generate enhanced prompt
   - Move to planner_agent
4. **Planner Agent**:
   - Generate research plan
   - Extract topics and keywords
   - Move to approve_plan
5. **User approves/edits plan** → Move to explorer_agent
6. **Explorer Agent**:
   - Search for each keyword
   - Extract content from results
   - Store in Pinecone
   - Move to complete
7. **User edits document** → EditAgent
8. **User chats** → ChatAgent with desk context

---

## Agent System

### Base Agent

All agents inherit from `BaseAgent`:

```python
class BaseAgent(ABC):
    def __init__(self, config: AgentInput):
        self.model = config.model
        self.tools = self._create_tools()
        self.max_iterations = config.max_iterations
        
    @abstractmethod
    def _create_tools(self) -> List[Tool]:
        """Define agent-specific tools"""
        pass
        
    @abstractmethod
    def _build_prompt(self, user_prompt: str, state: Dict) -> str:
        """Build prompt for LLM"""
        pass
        
    async def arun(self, user_prompt: str):
        """Main agent execution loop"""
        for iteration in range(self.max_iterations):
            # Get LLM decision
            decision = await self._call_llm(user_prompt)
            
            # Execute tool if needed
            if decision.type == "tool":
                result = await self._execute_tool(decision.tool_call)
                state["tool_results"].append(result)
            
            # Return answer if done
            elif decision.type == "final":
                yield decision.answer
                break
```

### Agent Communication

Agents communicate via:
- **Shared state**: Passed between agents
- **Database**: Persistent storage
- **Vector DB**: Shared knowledge base

### Tool Execution

Tools are executed asynchronously:

```python
async def _execute_tool(self, tool_call: ToolCall):
    tool = self.tools[tool_call.name]
    
    try:
        result = await tool.function(**tool_call.input)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

---

## Database Schema

### MongoDB Collections

**workspaces**:
```javascript
{
  _id: ObjectId,
  name: String,
  user_id: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

**chats**:
```javascript
{
  _id: ObjectId,
  workspace_id: String,
  title: String,
  messages: [
    {
      id: String,
      role: "user" | "assistant" | "system",
      content: String,
      created_at: DateTime,
      tokens: Number,
      model: String
    }
  ],
  created_at: DateTime,
  updated_at: DateTime
}
```

**research_desks**:
```javascript
{
  _id: ObjectId,
  workspace_id: String,
  state: "initial" | "context_agent" | "planner_agent" | "approve_plan" | "explorer_agent" | "complete",
  title: String,
  documents: {
    [doc_id]: {
      title: String,
      content: String
    }
  },
  context_agent: {
    conv_history: String,
    questions: [String],
    move_next: Boolean,
    confidence_level: Number,
    final_prompt: String,
    research_parameters: Object
  },
  planner_agent: {
    topics: [
      {
        topic: String,
        keywords: [String]
      }
    ]
  },
  messages: [Message],  // Chat messages
  created_at: DateTime,
  updated_at: DateTime
}
```

### Pinecone Vectors

**Namespace: Search**:
```javascript
{
  id: String,  // Unique vector ID
  values: [Float],  // 384-dim embedding
  metadata: {
    unique_id: String,  // Workspace ID
    title: String,
    url: String,
    content: String,
    source: String
  }
}
```

---

## External Services

### LLM Providers

**OpenRouter**:
- Multiple model access
- Pay-per-use pricing
- Free tier available

**Google AI Studio**:
- Gemini models
- Generous free tier
- Fast inference

**Integration**:
```python
class CloudLLMManager:
    def __init__(self, provider: str):
        self.provider = provider
        
    async def generate(self, messages: List[Dict], stream: bool = False):
        if self.provider == "openrouter":
            return await self._openrouter_generate(messages, stream)
        elif self.provider == "google_ai_studio":
            return await self._google_generate(messages, stream)
```

### SearXNG

**Purpose**: Privacy-focused web search

**Integration**:
```python
async def search(query: str, num_results: int = 10):
    response = await aiohttp.get(
        f"{SEARCHXNG_HOST}/search",
        params={"q": query, "format": "json"}
    )
    data = await response.json()
    return data["results"][:num_results]
```

### Pinecone

**Purpose**: Vector storage for semantic search

**Integration**:
```python
from pinecone import Pinecone

pc = Pinecone(api_key=PINECONE_KEY)
index = pc.Index("explored-data-index")

# Store vectors
index.upsert(vectors=[
    {
        "id": "vec1",
        "values": embedding,
        "metadata": {"title": "...", "content": "..."}
    }
])

# Search
results = index.query(
    vector=query_embedding,
    top_k=10,
    filter={"unique_id": workspace_id}
)
```

---

## Design Decisions

### Why FastAPI?

- **Async support**: Essential for streaming and concurrent requests
- **Type safety**: Pydantic integration
- **Auto documentation**: Swagger UI out of the box
- **Performance**: One of the fastest Python frameworks
- **Modern**: Python 3.11+ features

### Why Next.js?

- **SSR**: Better SEO and initial load
- **App Router**: Modern routing with layouts
- **TypeScript**: Type safety
- **Developer experience**: Hot reload, error overlay
- **Ecosystem**: Rich component libraries

### Why MongoDB?

- **Flexible schema**: Research desk structure evolves
- **Document model**: Natural fit for nested data
- **Async driver**: Motor for async operations
- **Scalability**: Horizontal scaling support

### Why Pinecone?

- **Managed service**: No infrastructure management
- **Performance**: Fast vector search
- **Filtering**: Metadata filtering for multi-tenancy
- **Reliability**: High availability

### Why SearXNG?

- **Privacy**: No tracking or data collection
- **Self-hosted**: Full control
- **Aggregation**: Multiple search engines
- **Free**: No API costs

### Multi-Agent Architecture

**Benefits**:
- **Separation of concerns**: Each agent has specific role
- **Reusability**: Agents can be composed
- **Testability**: Test agents independently
- **Flexibility**: Easy to add new agents

**Trade-offs**:
- **Complexity**: More moving parts
- **Debugging**: Harder to trace execution
- **Performance**: Multiple LLM calls

---

## Security Considerations

### Current State

- No authentication (development only)
- CORS allows all origins
- No rate limiting
- No input sanitization beyond Pydantic

### Future Improvements

- **Authentication**: JWT tokens
- **Authorization**: Role-based access
- **Rate limiting**: Prevent abuse
- **Input validation**: Sanitize user input
- **HTTPS**: Encrypt traffic
- **API keys**: Secure external service credentials

---

## Performance Optimization

### Backend

- **Async operations**: Non-blocking I/O
- **Connection pooling**: MongoDB and HTTP clients
- **Caching**: Redis for frequently accessed data (future)
- **Batch processing**: Group similar operations

### Frontend

- **Code splitting**: Load only needed code
- **Image optimization**: Next.js automatic optimization
- **Lazy loading**: Components and routes
- **Memoization**: React.memo for expensive components

### Database

- **Indexes**: On frequently queried fields
- **Projection**: Fetch only needed fields
- **Aggregation**: Server-side data processing

---

## Scalability

### Horizontal Scaling

- **Stateless backend**: Can run multiple instances
- **Load balancer**: Distribute traffic
- **Database sharding**: MongoDB horizontal partitioning
- **CDN**: Static assets and frontend

### Vertical Scaling

- **Increase resources**: More CPU/RAM
- **Optimize queries**: Reduce database load
- **Caching**: Reduce external API calls

---

## Monitoring & Logging

### Current State

- Basic Python logging
- Console logs in frontend

### Future Improvements

- **Structured logging**: JSON logs
- **Log aggregation**: ELK stack or similar
- **Metrics**: Prometheus + Grafana
- **Error tracking**: Sentry
- **Performance monitoring**: APM tools

---

## Future Architecture

### Planned Improvements

1. **Authentication & Authorization**
2. **Real-time collaboration** (WebSockets)
3. **File upload & processing**
4. **Export functionality** (PDF, DOCX)
5. **Reference management**
6. **Advanced search** (full-text + vector)
7. **Caching layer** (Redis)
8. **Background jobs** (Celery)
9. **API versioning**
10. **GraphQL API** (alternative to REST)

---

For more information, see:
- [API Documentation](./API.md)
- [Development Guide](./DEVELOPMENT.md)
- [SearXNG Setup](./SEARXNG_SETUP.md)
