# Lesson 04: Async & Await (Non-Blocking Concurrency)

### What is it?
In many web frameworks (like Flask), your code is "synchronous." If one user requests an LLM response (taking 10 seconds), the server is "busy" and can't help anyone else until it's finished.

**Async/Await** changes that.
*   `async def`: Tells Python this function can **wait** for something (like a network call or an OpenAI response) without blocking the entire server.
*   `await`: Tells Python, "I'm waiting now! You can go help other users until I'm done."

### Example (Non-blocking):
```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/slow-task")
async def slow_task():
    # 'await' here means the server can do other things 
    # while waiting for this sleep to finish.
    await asyncio.sleep(5) 
    return {"message": "Finally done!"}

@app.get("/fast-task")
async def fast_task():
    # This task can be run IMMEDIATELY, even if /slow-task is still waiting!
    return {"message": "I'm fast!"}
```

---

# Lesson 05: Middleware (The "Security Guard" Pattern)

### What is it?
Think of Middleware as a **Security Guard** standing in front of your building.
1.  **Incoming:** It checks every person (Request) entering the building.
2.  **Outgoing:** It checks every package (Response) leaving the building.

**Common Uses:**
*   Logging (e.g., "User 123 just called /agents")
*   Authentication (e.g., "Does this request have a valid API Key?")
*   Adding "Headers" (e.g., "This request took 20ms to process")

### Coding Example:
```python
import time
from fastapi import Request, FastAPI

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 1. Before the route runs:
    start_time = time.time()
    
    # 2. Let the request proceed to the route:
    response = await call_next(request)
    
    # 3. After the route finishes:
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```
