# Day 04 - Practical: Consistency and Atomic SQL Updates

Scale AI processes millions of labeling tasks. If two people try to "Claim" the same task at the same time, you'll have a **Concurrency Race Condition**. This is a **Consistency** lesson.

## 1. The Scenario
We have a task with `status = 'available'`. Two workers (A and B) both click "Start Task" at the exact same millisecond. 

**The Bug:**
1. Worker A's server reads `SELECT status FROM tasks WHERE id = 123` (sees `'available'`).
2. Worker B's server reads `SELECT status FROM tasks WHERE id = 123` (sees `'available'`).
3. Worker A's server writes `UPDATE tasks SET status = 'claimed', worker_id = 'A'`.
4. Worker B's server writes `UPDATE tasks SET status = 'claimed', worker_id = 'B'`.
**Result:** Worker B "overwrote" Worker A. Worker A *thinks* they have the task, but the database says Worker B. Both start working. $100 in labor is wasted. This is a **Lost Update**.

---

## 2. The Solution: Optimistic Locking with "Atomic Conditional Updates"
We don't need "Locks" (which are slow). We just need to check the status **inside** the update.

### The "Scale AI" Correct Way (Atomic Update):
```python
@app.post("/v1/tasks/{task_id}/claim")
async def claim_task(
    task_id: str, 
    worker_id: str, 
    db = Depends(get_db)
):
    # 1. ATOMIC: Combine 'check' and 'update' in ONE statement
    # The database will ONLY update if the status is STILL 'available'
    query = """
    UPDATE tasks 
    SET status = 'claimed', 
        worker_id = :w,
        claimed_at = NOW()
    WHERE id = :t 
      AND status = 'available'
    RETURNING id;
    """
    
    # 2. CHECK: If 0 rows were updated, someone else already claimed it
    result = await db.execute(query, {"t": task_id, "w": worker_id})
    
    if not result:
        # 3. FAILURE: This is the 'Safe' path. We lost the race.
        raise HTTPException(
            status_code=409, # 409 = Conflict
            detail="This task was already claimed by another worker."
        )

    # 4. SUCCESS: We won the race!
    return {"status": "success", "task_id": task_id}
```

---

## 3. 🧠 Key Teaching Points:
*   **Compare-and-Swap (CAS)**: This is the logic of `WHERE status = 'available'`. It's like saying: "I want to change the state ONLY if the current state is what I think it is." This is the foundation of all high-performance distributed systems.
*   **The 409 Conflict**: This is the correct HTTP status code for state races. It tells the frontend "The request was valid, but the current state of the resource prevents this action."
*   **Avoiding "Heavy" Locking**: We didn't use `FOR UPDATE` (which "locks" the row and blocks other readers). Our way is "Lock-free." It's faster and scales to millions of users.
*   **Determinism**: This is a "Deterministic State Machine." No matter how many people try to claim the task, only ONE can ever succeed.
*   **Why at Scale?**: In a system with 1,000 servers, you can't use a "Python lock" because a lock in Server A doesn't help Server B. The **Database is the only global source of truth**.
