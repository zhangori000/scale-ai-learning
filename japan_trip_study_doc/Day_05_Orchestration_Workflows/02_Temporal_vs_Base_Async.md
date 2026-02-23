# Day 05 - Code: Temporal vs. Base Async Concurrency (Serialization)

How do you handle two events for the same task arriving at the exact same millisecond? This is a **Concurrency Serialization** lesson.

## 1. The "Base" Async Problem (FastAPI/NodeJS)
Imagine a "Labeling Task" has a `version` number. Two webhooks (A and B) arrive for the SAME task ID. 

**The Bug:**
1. Webhook A reads `version = 5`.
2. Webhook B reads `version = 5`.
3. Webhook A writes `version = 6` (Status: "Approved").
4. Webhook B writes `version = 6` (Status: "Rejected").
**Result:** Webhook B just "erased" the Approval from Webhook A. This is a **Lost Update** because `Base Async` processes requests in "Parallel" across multiple workers.

---

## 2. The Solution: Temporal's "Serialized Signal" Pattern
Scale AI uses **Temporal.io** for complex workflows. Temporal has a "Superpower": It **Serializes** events for a specific "Workflow ID."

### The "Temporal" Way:
1. Webhook A and B arrive. 
2. Temporal puts them in a **Signal Queue** for that specific Task ID.
3. Temporal runs Webhook A to completion. `version` becomes 6.
4. Temporal *then* runs Webhook B. It sees `version = 6` and correctly increments it to 7. 
**Result:** No lost updates. No race conditions. The code is "Naturally Serialized."

---

## 3. The "Base Async" Way (Manual Fix):
If you *don't* have Temporal, you have to build this yourself using a **Durable Cursor**.

### The Manual "Scale AI" Correct Way:
```python
@app.post("/v1/tasks/{task_id}/events")
async def handle_task_event(
    task_id: str, 
    event_id: int, # MONOTONIC event ID (e.g., 1, 2, 3...)
    db = Depends(get_db)
):
    # 1. ATOMIC: Combine 'check' and 'update' in ONE transaction
    async with db.transaction():
        # 2. CURSOR: Only process if this is the 'Next' event
        # Check against the 'last_processed_event_id'
        last_id = await db.fetch_val("SELECT last_event_id FROM tasks WHERE id = :id", {"id": task_id})
        
        if event_id <= last_id:
            # 3. DUPLICATE: We've already seen this or a newer event. Skip!
            return {"status": "already_processed"}
            
        if event_id > last_id + 1:
            # 4. OUT-OF-ORDER: Event #10 arrived before Event #9. 
            # We must WAIT! In a real system, we would RE-QUEUE this event.
            raise HTTPException(status_code=425, detail="Too Early")

        # 5. WORK: Process the event and advance the cursor
        await db.execute(
            "UPDATE tasks SET last_event_id = :e, status = 'processed' WHERE id = :id",
            {"e": event_id, "id": task_id}
        )
    return {"status": "success"}
```

---

## 4. 🧠 Key Teaching Points:
*   **Sequential Consistency**: In "Base" Async (without Temporal), you MUST build your own "Guard" (the `last_event_id` cursor) to ensure events are processed in order. 
*   **Temporal Serialization**: Temporal is "Single-Writer-per-Workflow." It's like having a "Mini Mutex" for every task in your database. This is why it's so powerful for Scale.
*   **Monotonic IDs**: This logic ONLY works if the events have "Version Numbers" or "Timestamps" that are guaranteed to go forward. If Event IDs are random (UUIDs), you need a **Deduplication Table** (Day 01 lesson!). 
*   **Why at Scale?**: When you have 10,000 labelers clicking "Submit" at once, "Concurrency" isn't an edge case. It's the **Standard Environment**. You MUST design your code to handle simultaneous writes.
*   **The "Forward Deployed" Tip**: If an interviewer asks "How do you handle a race condition between two webhooks?", always start by asking, "Do these events have a **Sequence Number** or a **Version**?" This shows you're thinking about the data protocol, not just the code.
