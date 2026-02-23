# Day 02 - Practical: FastAPI Streaming Responses (SSE)

Scale AI often deals with "Long-Running Tasks" (e.g., an LLM generating a 1,000-word response). We don't want the user to wait 30 seconds for a single JSON. We want to **stream** the response as it's being built.

## 1. The Server-Sent Events (SSE) Protocol
FastAPI handles this with `StreamingResponse`. It uses a **Generator** (a function with `yield`).

```python
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

async def event_generator(task_id: str):
    """
    Simulates a long-running labeling task.
    In a real app, this would read from a Redis Stream or Kafka.
    """
    for i in range(1, 6):
        # 1. Simulate work
        await asyncio.sleep(1) 
        
        # 2. Yield the data (must be a string!)
        # Each event MUST end with TWO newlines 


        yield f"id: {i}
event: task_update
data: {{"id": "{task_id}", "progress": {i*20}}}

"
        
    # 3. Final event
    yield "event: task_complete
data: {"status": "finished"}

"

@app.get("/v1/tasks/{task_id}/stream")
async def stream_task_updates(task_id: str):
    # StreamingResponse takes a generator and sets the correct HTTP headers
    return StreamingResponse(
        event_generator(task_id),
        media_type="text/event-stream"
    )
```

---

## 2. 🧠 Key Teaching Points:
*   **`StreamingResponse`**: This tells the browser (and Nginx) NOT to buffer the response. It sends the bytes immediately.
*   **The Generator (`yield`)**: Notice `async def`. This is "Non-Blocking." While one request is sleeping (`await asyncio.sleep(1)`), the server can handle 1,000 other requests.
*   **The Format**: SSE is a plain-text protocol. Every message looks like `event: name 
 data: payload 

`. The `

` is the separator that tells the client "The message is finished."
*   **Why use this at Scale?**: It's simpler than WebSockets (no bi-directional complex state) and more robust than raw long-polling. Perfect for LLM token streaming.
