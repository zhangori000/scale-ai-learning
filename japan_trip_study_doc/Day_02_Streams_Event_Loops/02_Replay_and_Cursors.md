# Day 02 - Code: Replay Semantics with Last-Event-ID

If a user's WiFi flickers for 5 seconds, they might miss 10 events. How do we "catch them up"? This is the **Replay Protocol**.

## 1. The Strategy: The Cursor
Scale AI uses a `Last-Event-ID` header. When the client reconnects, they say: "I last saw event #10. Give me everything after that."

## 2. The Implementation
We'll update our generator to read from a **Redis Stream** (the "Standard" at Scale).

```python
import redis.asyncio as redis # Redis with 'async/await' support

@app.get("/v1/tasks/{task_id}/stream")
async def stream_with_replay(
    task_id: str,
    last_event_id: str = Header(None, alias="Last-Event-ID") # Browser sends this!
):
    # 1. Connect to Redis
    r = redis.from_url("redis://localhost")
    stream_key = f"task_stream:{task_id}"

    # 2. Determine the starting 'cursor'
    # '$' means 'give me only NEW events from now'
    # 'last_event_id' means 'give me everything AFTER this ID'
    cursor = last_event_id or "$"

    async def redis_generator():
        nonlocal cursor
        while True:
            # 3. Blocking Read (Wait up to 10 seconds for an event)
            events = await r.xread({stream_key: cursor}, block=10000, count=10)
            
            if not events:
                # 4. Heartbeat: Keep the connection alive
                yield ": heartbeat

"
                continue

            # 5. Process events
            for stream, msgs in events:
                for msg_id, data in msgs:
                    cursor = msg_id # Advance the cursor!
                    yield f"id: {msg_id}
data: {data.decode()}

"

    return StreamingResponse(redis_generator(), media_type="text/event-stream")
```

---

## 3. 🧠 Key Teaching Points:
*   **`XREAD` (Redis Streams)**: This is Scale's superpower. It's an "Append-Only Log" (like a mini Kafka). It's fast, ordered, and handles multiple subscribers.
*   **The Heartbeat (`: heartbeat

`)**: Many Load Balancers (like Nginx/ALB) will kill a connection if they don't see data for 60 seconds. A "Comment" (`: text`) in SSE keeps the connection alive without bothering the frontend code.
*   **`nonlocal cursor`**: We update the cursor inside the loop so that if the *loop* fails but the connection stays open, we don't repeat events.
*   **Scalability**: This design allows 10,000 users to stream the same task simultaneously without melting the database, because Redis is in-memory and `XREAD` is highly optimized.
