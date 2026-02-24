# Lesson 06: Mock Project - Agentic Task Tracker

Let's build a mini-API that uses everything we learned!

### 1. Requirements (The Goal)

- A **Router** for task operations.
- **Pydantic** to define a Task.
- **Dependency Injection** to simulate a database.
- **Async** to wait for an LLM "analysis" of the task.
- **Middleware** to log how long the LLM analysis took.

### 2. Implementation Code (Full Example)

```python
import time
import asyncio
from typing import Dict
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

# --- SCHEMA (Pydantic) ---
class Task(BaseModel):
    id: int
    title: str = Field(..., min_length=5)
    description: str | None = None
    completed: bool = False

# --- "DATABASE" (Dependency Injection) ---
# A simple in-memory dictionary to act as our database
DB = {}

def get_task_db():
    return DB # In real life, this would be a Postgres connection

# --- ROUTER ---
task_router = APIRouter(prefix="/tasks", tags=["tasks"])

@task_router.post("/")
async def create_task(task: Task, db: Dict = Depends(get_task_db)):
    if task.id in db:
        raise HTTPException(status_code=400, detail="Task already exists")

    # Simulate an "AI Analysis" of the task title (takes time)
    print(f"Analyzing task: {task.title}...")
    await asyncio.sleep(2) # 'await' lets other users call our API during this!

    db[task.id] = task
    return {"message": "Task created", "task": task}

@task_router.get("/{task_id}")
async def get_task(task_id: int, db: Dict = Depends(get_task_db)):
    if task_id not in db:
        raise HTTPException(status_code=404, detail="Task not found")
    return db[task_id]

# --- APP SETUP ---
app = FastAPI(title="Agentic Task Tracker")

# 1. Add Middleware (The Security Guard/Logger)
@app.middleware("http")
async def log_duration(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"API Call to {request.url.path} took {duration:.4f}s")
    return response

# 2. Include our Router
app.include_router(task_router)
```

### 3. How to test it:

1.  **Save** this code to a file like `main.py`.
2.  **Run** it with `uvicorn main:app --reload`.
3.  **Visit** `http://localhost:8000/docs`.
4.  **Try** creating a task. You'll see:
    - The Pydantic validation (try a title shorter than 5 chars!).
    - The 2-second delay for "AI Analysis" (and notice how you can open a second tab and call the `GET` route while it's still waiting!).
    - The terminal output from our Middleware showing exactly how long it took.
