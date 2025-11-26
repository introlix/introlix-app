# Development Guide

This guide helps you set up a development environment and contribute to Introlix.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Development Setup

### Prerequisites

Ensure you have installed:
- Python 3.11+
- Node.js 18+
- pnpm
- Git
- MongoDB
- Docker (optional if setup from code) (for SearXNG)

### Initial Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/introlix/introlix.git
   cd introlix
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. **Authenticate with Hugging Face**

   ```bash
   pip install huggingface_hub
   # Login to Hugging Face
   hf auth login

   # Or set token directly
   export HUGGING_FACE_HUB_TOKEN=your_hf_token_here
   ```

4. **Install development dependencies:**
   ```bash
   pip install pytest pytest-asyncio black flake8 mypy
   ```

5. **Set up frontend:**
   ```bash
   cd web
   pnpm install
   cd ..
   ```

6. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

7. **Start external services:**
   ```bash
   # MongoDB (via docker or use atlas)
   docker run -d --name mongodb -p 27017:27017 mongo:latest
   
   # SearXNG
   docker-compose up -d
   ```

---

## Project Structure

### Backend Structure

```
introlix/
├── agents/              # AI agent implementations
│   ├── base_agent.py   # Abstract base class
│   ├── baseclass.py    # Agent primitives (Tool, AgentInput, etc.)
│   ├── chat_agent.py   # Conversational agent
│   ├── context_agent.py # Context gathering agent
│   ├── planner_agent.py # Research planning agent
│   ├── explorer_agent.py # Web exploration agent
│   ├── edit_agent.py   # Document editing agent
│   └── writer_agent.py # Content generation agent
├── routes/             # FastAPI routes
│   ├── chat.py        # Chat endpoints
│   └── research_desk.py # Research desk endpoints
├── tools/              # Agent tools
│   ├── web_search.py  # SearXNG integration
│   └── web_crawler.py # Content extraction
├── services/           # Business logic layer
├── utils/              # Utility functions
├── models.py          # Pydantic models
├── schemas.py         # Response schemas
├── database.py        # MongoDB connection
├── llm_config.py      # LLM provider configuration
└── config.py          # Application configuration
```

### Frontend Structure

```
web/src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── providers/         # React context providers
│   └── workspaces/        # Workspace routes
│       └── [id]/          # Dynamic workspace pages
│           ├── page.tsx   # Workspace overview
│           ├── chat/      # Chat interface
│           └── desk/      # Research desk interface
├── components/            # React components
│   ├── ui/               # Base UI components (shadcn/ui)
│   ├── chat/             # Chat-specific components
│   ├── desk/             # Research desk components
│   └── workspace/        # Workspace components
├── hooks/                # Custom React hooks
│   ├── use-chat.ts       # Chat state management
│   ├── use-desk.ts       # Research desk state
│   └── use-streaming.ts  # SSE streaming utilities
├── lib/                  # Utilities and configuration
│   ├── api.ts           # API client
│   └── utils.ts         # Helper functions
└── types/               # TypeScript type definitions
    └── index.ts
```

---

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `feature/feature-name` - New features
- `fix/bug-name` - Bug fixes
- `docs/update-name` - Documentation updates

### Creating a Feature

1. **Create a branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push to your fork:**
   ```bash
   git push origin feature/my-feature
   ```

4. **Create a pull request** on GitHub

### Keeping Your Fork Updated

```bash
# Add upstream remote (once)
git remote add upstream https://github.com/introlix/introlix.git

# Fetch and merge updates
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

---

## Code Style

### Python

Follow **PEP 8** with these tools:

**Black** (code formatter):
```bash
# Format all Python files
black introlix/

# Check without modifying
black --check introlix/
```

**Flake8** (linter):
```bash
# Lint all Python files
flake8 introlix/ --max-line-length=88 --extend-ignore=E203

# Specific file
flake8 introlix/agents/chat_agent.py
```

**MyPy** (type checker):
```bash
# Type check
mypy introlix/

# Specific file
mypy introlix/agents/chat_agent.py
```

**Code Style Guidelines:**

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class MyModel(BaseModel):
    """
    Brief description of the model.
    
    Attributes:
        field_name: Description of field
    """
    field_name: str
    optional_field: Optional[int] = None


async def my_function(
    param1: str,
    param2: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something goes wrong
    """
    # Implementation
    pass
```

### TypeScript/React

**ESLint** (linter):
```bash
cd web
pnpm lint

# Fix auto-fixable issues
pnpm lint --fix
```

**Prettier** (formatter):
```bash
cd web
pnpm format

# Check without modifying
pnpm format:check
```

**Code Style Guidelines:**

```typescript
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

/**
 * Component description
 */
interface MyComponentProps {
  /** Description of prop */
  title: string;
  /** Optional prop */
  optional?: boolean;
  /** Callback function */
  onSubmit: (value: string) => void;
}

export function MyComponent({ 
  title, 
  optional = false, 
  onSubmit 
}: MyComponentProps) {
  const [value, setValue] = useState('');
  
  useEffect(() => {
    // Side effects
  }, []);
  
  const handleSubmit = () => {
    onSubmit(value);
  };
  
  return (
    <div className="container">
      <h2>{title}</h2>
      <Button onClick={handleSubmit}>Submit</Button>
    </div>
  );
}
```

---

## Testing

### Backend Testing

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=introlix --cov-report=html
```

**Run specific test:**
```bash
pytest tests/test_chat_agent.py
pytest tests/test_chat_agent.py::test_agent_initialization
```

**Writing Tests:**

```python
# tests/test_chat_agent.py
import pytest
from introlix.agents.chat_agent import ChatAgent

@pytest.fixture
def chat_agent():
    """Fixture to create a chat agent for testing."""
    return ChatAgent(
        unique_id="test-user",
        model="test-model"
    )

def test_agent_initialization(chat_agent):
    """Test that agent initializes correctly."""
    assert chat_agent.unique_id == "test-user"
    assert chat_agent.model == "test-model"

@pytest.mark.asyncio
async def test_agent_response(chat_agent):
    """Test that agent generates a response."""
    response = []
    async for chunk in chat_agent.arun("Hello"):
        response.append(chunk)
    
    assert len(response) > 0
```

### Frontend Testing

**Run tests:**
```bash
cd web
pnpm test

# Watch mode
pnpm test:watch

# Coverage
pnpm test:coverage
```

**Writing Tests:**

```typescript
// __tests__/components/chat.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Chat } from '@/components/chat';

describe('Chat Component', () => {
  it('renders chat input', () => {
    render(<Chat />);
    const input = screen.getByPlaceholderText('Type a message...');
    expect(input).toBeInTheDocument();
  });
  
  it('sends message on submit', async () => {
    const onSubmit = jest.fn();
    render(<Chat onSubmit={onSubmit} />);
    
    const input = screen.getByPlaceholderText('Type a message...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    const button = screen.getByRole('button', { name: /send/i });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith('Hello');
    });
  });
});
```

---

## Debugging

### Backend Debugging

**Using Python Debugger (pdb):**

```python
import pdb

def my_function():
    x = 10
    pdb.set_trace()  # Debugger will stop here
    y = x * 2
    return y
```

**Using VS Code:**

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

**Logging:**

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
```

### Frontend Debugging

**Browser DevTools:**
- Console: `console.log()`, `console.error()`
- Network tab: Inspect API calls
- React DevTools: Inspect component state

**VS Code Debugging:**

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug client-side",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000"
    }
  ]
}
```

---

## Common Tasks

### Adding a New Agent

1. **Create agent file:**
   ```bash
   touch introlix/agents/my_agent.py
   ```

2. **Implement agent:**
   ```python
   from introlix.agents.baseclass import BaseAgent, AgentInput, Tool
   
   class MyAgent(BaseAgent):
       def __init__(self, config: AgentInput):
           super().__init__(config)
           
       def _create_tools(self):
           return []
           
       def _build_prompt(self, user_prompt: str, state: dict):
           return f"System prompt\n\nUser: {user_prompt}"
           
       async def arun(self, user_prompt: str):
           # Implementation
           pass
   ```

3. **Add tests:**
   ```bash
   touch tests/test_my_agent.py
   ```

4. **Update documentation**

### Adding a New API Endpoint

1. **Add route in appropriate file:**
   ```python
   # introlix/routes/my_routes.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/my-endpoint", tags=["my_tag"])
   
   @router.get("/")
   async def get_items():
       return {"items": []}
   ```

2. **Register router in app.py:**
   ```python
   from introlix.routes.my_routes import router as my_router
   
   app.include_router(my_router)
   ```

3. **Add tests**

4. **Update API documentation**

### Adding a New Frontend Component

1. **Create component file:**
   ```bash
   touch web/src/components/my-component.tsx
   ```

2. **Implement component:**
   ```typescript
   interface MyComponentProps {
     title: string;
   }
   
   export function MyComponent({ title }: MyComponentProps) {
     return <div>{title}</div>;
   }
   ```

3. **Add tests:**
   ```bash
   touch web/__tests__/components/my-component.test.tsx
   ```

4. **Use in pages/components**

### Adding a New Dependency

**Backend:**
```bash
# Add to pyproject.toml dependencies
pip install new-package
pip freeze > requirements.txt  # If using requirements.txt
```

**Frontend:**
```bash
cd web
pnpm add new-package

# Dev dependency
pnpm add -D new-dev-package
```

---

## Troubleshooting

### Backend Issues

**Import errors:**
```bash
# Reinstall in editable mode
pip install -e .
```

**Database connection errors:**
```bash
# Check MongoDB is running
docker ps | grep mongodb

# Check connection string in .env
echo $MONGO_URI
```

**LLM API errors:**
```bash
# Verify API keys
echo $OPEN_ROUTER_KEY
echo $GEMINI_API_KEY

# Check provider configuration in introlix/config.py
```

### Frontend Issues

**Module not found:**
```bash
cd web
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

**Build errors:**
```bash
# Clear Next.js cache
cd web
rm -rf .next
pnpm build
```

**Type errors:**
```bash
# Check TypeScript
cd web
pnpm tsc --noEmit
```

### General Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill process
kill -9 <PID>
```

**Environment variables not loading:**
```bash
# Check .env file exists
ls -la .env

# Verify dotenv is loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('MONGO_URI'))"
```

---

## Development Tips

### Hot Reload

Both backend and frontend support hot reload:

**Backend:**
```bash
uvicorn app:app --reload
```

**Frontend:**
```bash
cd web
pnpm dev
```

### Database GUI

Use MongoDB Compass for easier database inspection:
```
mongodb://localhost:27017
```

### API Testing

Use the built-in Swagger UI:
```
http://localhost:8000/docs
```

Or use tools like:
- Postman
- Insomnia
- curl
- httpie

### Code Snippets

Create VS Code snippets for common patterns:

`.vscode/python.code-snippets`:
```json
{
  "FastAPI Route": {
    "prefix": "route",
    "body": [
      "@router.${1:get}(\"/${2:path}\")",
      "async def ${3:function_name}():",
      "    ${4:pass}"
    ]
  }
}
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [TanStack Query](https://tanstack.com/query/latest)
- [MongoDB Documentation](https://www.mongodb.com/docs/)

---

## Getting Help

- Check [GitHub Issues](https://github.com/introlix/introlix/issues)
- Ask in [GitHub Discussions](https://github.com/introlix/introlix/discussions)
- Read the [Contributing Guide](./CONTRIBUTING.md)

Happy coding! 🚀
