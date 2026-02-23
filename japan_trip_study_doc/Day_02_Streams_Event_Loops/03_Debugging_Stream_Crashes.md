# Day 02 - System/Debug: The JSON Decode Crash in Streams

One bad record shouldn't kill your entire service. This is a **Fault Isolation** lesson.

## 1. The Scenario
The Scale AI backend is streaming 1,000 "Labeling Events" to a client. At event #500, a worker process accidentally saves a malformed JSON string (e.g., `{"id": 1, "data": {bad_json: }}`).

**The Bug:** The server's `json.loads()` fails inside the stream loop. The `Exception` escapes, the generator stops, the client disconnects, and they never see events 501–1,000.

## 2. The Solution: Isolating the Failure
We MUST move the "Risky" code (parsing JSON) inside a `try/except` block **inside** the loop.

### The Broken Way (DO NOT USE)
```python
async for msg_id, raw_data in redis_stream:
    data = json.loads(raw_data) # CRASH! Loop terminates
    yield f"data: {json.dumps(data)}

"
```

### The Correct Way (The "Scale" Way)
```python
async for msg_id, raw_data in redis_stream:
    try:
        # 1. Parse inside the block
        data = json.loads(raw_data)
        
        # 2. Yield ONLY if it's valid
        yield f"id: {msg_id}
data: {json.dumps(data)}

"
        
    except json.JSONDecodeError as e:
        # 3. LOG it, MEASURE it, but DON'T stop the stream!
        log.error(f"Skipping bad record {msg_id}: {str(e)}")
        # We can yield a special error event to the client
        yield f"id: {msg_id}
event: error
data: {{"error": "corrupt_record"}}

"
        continue # MOVE TO THE NEXT RECORD!
```

---

## 3. 🧠 Key Teaching Points:
*   **Liveness vs. Correctness**: In many Scale systems, it's better to deliver 99% of a stream than to deliver 0% because 1% was bad. **Liveness is prioritized** in real-time dashboards.
*   **Structured Logging**: In an interview, don't just `print(e)`. Say, "I would log this to a monitoring system like Datadog or Sentry so we can alert on it, while still preserving the connection for the user."
*   **The `continue` Keyword**: This is the heart of the solution. It skips the "broken" parts and keeps the loop spinning.
*   **Fault Isolation**: This is a core principle of "Forward Deployed Engineering." When building on top of fragile 3rd party model outputs (like LLMs), you MUST assume the data is broken and protect your own service from it.
