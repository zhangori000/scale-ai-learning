# Solution: Streaming SSE Generator

In `scale-agentex`, this pattern is used in `src/domain/use_cases/streams_use_case.py` and `src/api/routes/tasks.py`. It allows the platform to "bridge" the stream from OpenAI -> Agent -> Platform -> UI without buffering.

```python
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

# --- 1. The Generator (Simulates the Agent) ---
async def fake_llm_stream(full_response: str):
    """
    Yields chunks of text in SSE (Server-Sent Events) format.
    Format: 'data: <JSON_STRING>

'
    """
    words = full_response.split(" ")
    
    # Simulate thinking...
    await asyncio.sleep(0.5) 
    
    for word in words:
        # Create a structured JSON object
        chunk_data = {"chunk": word + " ", "type": "delta"}
        
        # Serialize to JSON string
        json_str = json.dumps(chunk_data)
        
        # Format as SSE event
        # Note the double newline at the end! This is required by the SSE protocol.
        sse_event = f"data: {json_str}

"
        
        # Yield as bytes
        yield sse_event.encode("utf-8")
        
        # Simulate typing speed
        await asyncio.sleep(0.1)
    
    # Signal completion (optional but good practice)
    yield "data: [DONE]

".encode("utf-8")

# --- 2. The Route (The API) ---
@app.get("/stream-chat")
async def stream_chat():
    response_text = "Hello! I am an AI agent running on Scale Agentex. I am streaming this response to you token by token."
    
    return StreamingResponse(
        fake_llm_stream(response_text),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", # Important so browsers don't cache partial streams
            "X-Accel-Buffering": "no",   # Important for Nginx proxies
        }
    )

# --- 3. How to Run ---
# 1. Save this file as 'main.py'
# 2. Run: 'uvicorn main:app --reload'
# 3. Visit: http://localhost:8000/stream-chat
# You should see the text appear chunk by chunk!
```

### Why this matters for Scale-Agentex?
Agents are slow. If we waited for the entire response (30 seconds) before sending anything back, the user would think the app is broken. By using `StreamingResponse` and `Async Generators`, we can show the user that the AI is "alive" immediately. This is fundamental to the UX of `agentex-ui`.
