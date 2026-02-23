# FastAPI: The Core Engine of Scale AI Backend
**Goal:** Understand how a request flows from the internet into your code.

FastAPI is a modern Python web framework. Think of it like a "traffic controller" for HTTP requests. Its power comes from two things: **Async** (concurrency) and **Pydantic** (data validation).

## 1. The Simplest Server
Here is a "Hello World" in FastAPI.
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```
- `@app.get("/")`: This is a **Decorator**. It tells FastAPI: "When someone sends a `GET` request to the root URL `/`, run this function."

---

## 2. Pydantic: The "Guardian" of Your Data
Scale AI deals with complex JSON (images, labels, task metadata). You can't just trust that the JSON is correct. 
**Pydantic** models validate this for you.

```python
from pydantic import BaseModel

class Task(BaseModel):
    id: str
    label: str
    priority: int = 0 # Default value

@app.post("/tasks")
def create_task(task: Task):
    # FastAPI automatically checks:
    # 1. Is 'id' a string?
    # 2. Is 'label' a string?
    # 3. Is 'priority' an integer?
    # If not, it returns a 422 error automatically.
    return {"message": f"Task {task.id} created!"}
```

---

## 3. Dependency Injection (The Secret Sauce)
How do you pass a Database connection or an Authentication token into your function? You use `Depends`.

```python
from fastapi import Depends, Header, HTTPException

def get_db():
    db = MyDatabase()
    try:
        yield db
    finally:
        db.close()

@app.get("/items")
def read_items(db = Depends(get_db)):
    # You don't create 'db' yourself. 
    # FastAPI runs 'get_db', gives it to you, and closes it when done.
    return db.query("SELECT * FROM items")
```

---

## 4. Async: Why it's fast
Most web frameworks wait for the database to finish. FastAPI (using Python's `async/await`) says: "While the database is working, I'll go handle another request."

```python
@app.get("/slow-query")
async def slow_query():
    # 'await' means: "Pause here and let other requests run while I wait."
    data = await db.fetch_long_running_data()
    return data
```

---

## 5. FastAPI For Scale AI Interviews
In a Scale interview, you will likely be asked to build a **Backend Practical** (e.g., a Webhook or a Streaming API). You should know:
1. **Status Codes:** Use `202 Accepted` for async jobs, `204 No Content` for successful deletes, `409 Conflict` for duplicate webhooks.
2. **Background Tasks:** Use `BackgroundTasks` to send an email or a notification *after* returning a response to the user.
3. **Pydantic Models:** Always define your input and output schemas clearly.

## 🚀 Quick Exercise
Try to read the `Day_01` files again. Notice the `Request`, `Header`, and `Depends`. Those are all FastAPI primitives.
