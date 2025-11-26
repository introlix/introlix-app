# Contributing to Introlix

Thank you for your interest in contributing to Introlix! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

### Our Standards

- **Be respectful**: Treat everyone with respect and kindness
- **Be collaborative**: Work together and help each other
- **Be constructive**: Provide helpful feedback and suggestions
- **Be inclusive**: Welcome people of all backgrounds and experience levels

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling, insulting, or derogatory remarks
- Personal or political attacks
- Publishing others' private information
- Other conduct that could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

Before contributing, make sure you have:

- Python 3.11+
- Node.js 18+
- pnpm
- Git
- A GitHub account

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/introlix.git
   cd introlix
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/introlix/introlix.git
   ```

4. **Verify remotes:**
   ```bash
   git remote -v
   ```

---

## Development Setup

### Backend Setup

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Install development dependencies:**
   ```bash
   pip install pytest black flake8 mypy
   ```

4. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Frontend Setup

1. **Navigate to web directory:**
   ```bash
   cd web
   ```

2. **Install dependencies:**
   ```bash
   pnpm install
   ```

3. **Install development tools:**
   ```bash
   pnpm add -D @types/node @types/react
   ```

### Database Setup

Set up MongoDB and Pinecone as described in the README.md quick start guide.

---

## How to Contribute

### Reporting Bugs

Before creating a bug report:

1. **Check existing issues** to avoid duplicates
2. **Verify the bug** in the latest version
3. **Collect information** about your environment

**Create a bug report with:**

- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Environment details (OS, Python version, etc.)
- Error messages and logs

**Example:**

```markdown
**Bug**: Chat agent fails when search returns empty results

**Steps to Reproduce:**
1. Create a new chat
2. Ask a very specific question that has no results
3. Observe error in console

**Expected**: Agent should handle empty results gracefully
**Actual**: Application crashes with TypeError

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.5
- Browser: Chrome 120

**Error Log:**

TypeError: Cannot read property 'results' of undefined
  at ChatAgent.arun (chat_agent.py:350)
```


### Suggesting Features

Before suggesting a feature:

1. **Check existing issues** and discussions
2. **Consider if it fits** the project's goals
3. **Think about implementation** complexity

**Create a feature request with:**

- Clear, descriptive title
- Problem it solves
- Proposed solution
- Alternative solutions considered
- Additional context

**Example:**

```markdown
**Feature**: Export research desk as PDF

**Problem**: Users want to share research offline

**Proposed Solution:**
Add an "Export" button that generates a PDF with:
- Research title and metadata
- All document content
- Formatted references
- Table of contents

**Alternatives:**
- Export as Markdown
- Export as DOCX
- Print-friendly HTML view

**Additional Context:**
Similar to how Notion handles exports
```

### Contributing Code

1. **Find an issue** to work on or create one
2. **Comment on the issue** to claim it
3. **Create a branch** for your work
4. **Make your changes** following coding standards
5. **Test your changes** thoroughly
6. **Submit a pull request**

---

## Coding Standards

### Python (Backend)

#### Style Guide

Follow [PEP 8](https://pep8.org/) style guide:

- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names
- Add docstrings to functions and classes

#### Code Formatting

Use **Black** for automatic formatting:

```bash
black introlix/
```

#### Linting

Use **Flake8** for linting:

```bash
flake8 introlix/ --max-line-length=88 --extend-ignore=E203
```

#### Type Hints

Use type hints for function signatures:

```python
from typing import List, Optional, Dict, Any

def process_results(
    results: List[Dict[str, Any]], 
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Process search results.
    
    Args:
        results: List of search result dictionaries
        limit: Optional maximum number of results to return
        
    Returns:
        Processed list of results
    """
    # Implementation
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def create_agent(model: str, config: Optional[AgentInput] = None) -> BaseAgent:
    """
    Create an AI agent instance.
    
    Args:
        model: Name of the LLM model to use
        config: Optional agent configuration
        
    Returns:
        Initialized agent instance
        
    Raises:
        ValueError: If model is not supported
        
    Example:
        >>> agent = create_agent("gpt-4", config=my_config)
        >>> response = await agent.arun("Hello")
    """
    pass
```

### TypeScript/React (Frontend)

#### Style Guide

- Use 2 spaces for indentation
- Use TypeScript for all new code
- Use functional components with hooks
- Use meaningful component and variable names

#### Code Formatting

Use **Prettier** (configured in project):

```bash
pnpm format
```

#### Linting

Use **ESLint**:

```bash
pnpm lint
```

#### Component Structure

```typescript
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

interface MyComponentProps {
  title: string;
  onSubmit: (value: string) => void;
  optional?: boolean;
}

/**
 * MyComponent - Brief description
 * 
 * Longer description if needed
 */
export function MyComponent({ title, onSubmit, optional = false }: MyComponentProps) {
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

#### Hooks

Create custom hooks for reusable logic:

```typescript
// hooks/use-research-desk.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useResearchDesk(deskId: string) {
  const { data, isLoading } = useQuery({
    queryKey: ['desk', deskId],
    queryFn: () => api.getDesk(deskId),
  });
  
  const updateMutation = useMutation({
    mutationFn: api.updateDesk,
  });
  
  return {
    desk: data,
    isLoading,
    update: updateMutation.mutate,
  };
}
```

---

## Commit Guidelines

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(chat): add streaming support for responses

Implement streaming responses in chat agent to improve
user experience with real-time feedback.

Closes #123
```

```
fix(research-desk): handle empty search results

Previously crashed when search returned no results.
Now displays appropriate message to user.

Fixes #456
```

```
docs(readme): update installation instructions

Add missing step for Pinecone index creation
```

### Commit Best Practices

- **One logical change per commit**
- **Write clear, descriptive messages**
- **Reference issues** when applicable
- **Keep commits atomic** and focused

---

## Pull Request Process

### Before Submitting

1. **Update from upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests:**
   ```bash
   # Backend
   pytest
   
   # Frontend
   cd web
   pnpm test
   ```

3. **Check code quality:**
   ```bash
   # Backend
   black introlix/
   flake8 introlix/
   
   # Frontend
   pnpm lint
   ```

4. **Update documentation** if needed

### Creating a Pull Request

1. **Push to your fork:**
   ```bash
   git push origin feature/my-feature
   ```

2. **Open a pull request** on GitHub

3. **Fill out the PR template:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Changes Made
- Added streaming support
- Updated API endpoints
- Added tests

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainers
3. **Address feedback** and make changes
4. **Approval** from at least one maintainer
5. **Merge** by maintainer

### After Merge

1. **Delete your branch:**
   ```bash
   git branch -d feature/my-feature
   git push origin --delete feature/my-feature
   ```

2. **Update your fork:**
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

---

## Testing

### Backend Testing

Use **pytest** for testing:

```python
# tests/test_chat_agent.py
import pytest
from introlix.agents.chat_agent import ChatAgent

@pytest.fixture
def chat_agent():
    return ChatAgent(
        unique_id="test-user",
        model="test-model"
    )

def test_agent_initialization(chat_agent):
    assert chat_agent.unique_id == "test-user"
    assert chat_agent.model == "test-model"

@pytest.mark.asyncio
async def test_agent_response(chat_agent):
    response = await chat_agent.arun("Hello")
    assert response is not None
```

**Run tests:**
```bash
pytest
pytest -v  # Verbose
pytest tests/test_chat_agent.py  # Specific file
pytest -k "test_agent"  # Match pattern
```

### Frontend Testing

Use **Jest** and **React Testing Library**:

```typescript
// __tests__/components/chat.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Chat } from '@/components/chat';

describe('Chat Component', () => {
  it('renders chat input', () => {
    render(<Chat />);
    expect(screen.getByPlaceholderText('Type a message...')).toBeInTheDocument();
  });
  
  it('sends message on submit', async () => {
    const onSubmit = jest.fn();
    render(<Chat onSubmit={onSubmit} />);
    
    const input = screen.getByPlaceholderText('Type a message...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.submit(input);
    
    expect(onSubmit).toHaveBeenCalledWith('Hello');
  });
});
```

**Run tests:**
```bash
cd web
pnpm test
pnpm test:watch  # Watch mode
pnpm test:coverage  # Coverage report
```

---

## Documentation

### Code Documentation

- Add docstrings to all functions and classes
- Comment complex logic
- Keep comments up-to-date

### User Documentation

When adding features, update:

- `README.md` - If it affects quick start
- `docs/API.md` - If it adds/changes API endpoints
- `docs/DEVELOPMENT.md` - If it affects development

### API Documentation

Backend API is auto-documented with FastAPI. Add clear descriptions:

```python
@router.post("/chat", response_model=ChatResponse)
async def create_chat(
    workspace_id: str,
    request: ChatRequest
) -> ChatResponse:
    """
    Create a new chat session.
    
    This endpoint initializes a new chat session within a workspace
    and returns the chat ID for subsequent messages.
    
    Args:
        workspace_id: ID of the workspace
        request: Chat creation request with initial message
        
    Returns:
        ChatResponse with chat ID and initial response
        
    Raises:
        HTTPException: 404 if workspace not found
    """
    pass
```

---

## Questions?

If you have questions:

1. Check existing [documentation](../README.md)
2. Search [GitHub Issues](https://github.com/introlix/introlix/issues)
3. Ask in [GitHub Discussions](https://github.com/introlix/introlix/discussions)
4. Join our [Discord Community](https://discord.gg/mhyKwfVm)
5. Reach out to maintainers

---

## Recognition

Contributors will be recognized in:

- GitHub contributors page
- Release notes
- Project documentation

Thank you for contributing to Introlix! 🎉
