# Lesson 02: FastAPI for Agentex Developers

FastAPI is the backbone of the Agentex platform. It's chosen for its high performance, speed of development, and native support for Python's `async/await`.

## 1. The Core Architecture
In `scale-agentex/agentex/src/api/app.py`, you'll see how the main application is instantiated:

```python
from fastapi import FastAPI
app = FastAPI(title="Agentex API")
```

The app is broken down into **Routers** (`APIRouter`). This allows the codebase to stay organized by grouping related endpoints (e.g., `/agents`, `/tasks`, `/messages`).

## 2. Pydantic: The Data Contract
Every request and response in Agentex uses **Pydantic models**. These are located in `src/api/schemas`.

**Why it matters:**
*   **Validation:** If a client sends a string where a number is expected, FastAPI returns a clear error before your code even runs.
*   **Serialization:** It automatically converts Python objects (like database results) into JSON.

**Example (simplified):**
```python
from pydantic import BaseModel

class CreateAgentRequest(BaseModel):
    name: str
    description: str | None = None
```

## 3. Dependency Injection
FastAPI's `Depends` system is used heavily in Agentex for things like:
*   Database connections (`get_db`)
*   Authentication/Authorization checks
*   Fetching configurations

It's a way to say: "Before this function runs, I need these objects prepared for me."

## 4. Async/Await: The Powerhouse
AI agents are often "I/O bound"—they spend a lot of time waiting for LLM responses or database queries. 

By using `async def`, FastAPI can handle thousands of concurrent connections on a single thread. It doesn't "block" while waiting for OpenAI to respond; it moves on to the next request.

## 5. Middleware: The Security Guard
Check out `src/api/authentication_middleware.py`. 
Middleware in FastAPI intercepts every request before it reaches your routes. In Agentex, it's used to:
*   Log every incoming request.
*   Verify API keys or Auth tokens.
*   Add tracing headers for OpenTelemetry.

---

### Pro-Tip for Newcomers:
Run the backend and visit `http://localhost:5003/docs` (or `/swagger`). 
This interactive documentation is generated **automatically** by FastAPI from the Python code and Pydantic models. You can test every API endpoint directly from your browser!
