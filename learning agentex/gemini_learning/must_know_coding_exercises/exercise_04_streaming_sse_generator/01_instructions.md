# Exercise: Streaming SSE Generator

In `scale-agentex` (`src/api/routes/tasks.py`), the endpoint `/tasks/{id}/stream` returns a `StreamingResponse`. This allows the UI to show the AI "typing" in real-time.

## The Goal
Create a FastAPI endpoint that yields "deltas" (chunks of text) one by one, simulating an LLM response.

## Requirements
1.  **Async Generator:** Create an `async def fake_llm_stream(text: str)` that:
    *   Splits the text into words.
    *   Yields each word with a small delay (`await asyncio.sleep(0.1)`).
    *   Formats the output as Server-Sent Events (SSE): `data: {"chunk": "word"}

`.
2.  **FastAPI Route:** Create a route `/stream-chat` that returns a `StreamingResponse` using your generator.

## Starter Code
```python
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

# --- 1. The Generator (Simulates the Agent) ---
async def fake_llm_stream(full_response: str):
    """
    Yields chunks of text in SSE format.
    Format: 'data: <JSON_STRING>

'
    """
    words = full_response.split(" ")
    for word in words:
        # TODO: 
        # 1. Create a JSON object: {"chunk": word + " "}
        # 2. Format it as SSE string.
        # 3. Yield it as bytes.
        # 4. Sleep for 0.1s to simulate network latency.
        pass

# --- 2. The Route (The API) ---
@app.get("/stream-chat")
async def stream_chat():
    response_text = "Hello! I am an AI agent running on Scale Agentex. I am streaming this response to you token by token."
    
    # TODO: Return a StreamingResponse using the generator
    # Hint: media_type="text/event-stream"
    pass

# --- 3. How to Run ---
# Save as 'main.py' and run: 'uvicorn main:app --reload'
# Then visit: http://localhost:8000/stream-chat in your browser.
```
