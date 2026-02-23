# Day 10 - System/Debug: Distributed SQL and Read Replicas

How do you handle a "Spike" of 100,000 read requests per second? This is a **Database Scaling** lesson.

## 1. The Scenario
Scale AI's API for "Task Status" is hit 1,000,000 times per minute by customers polling for results.

**The Problem:** The "Primary" Database (the "Writer") is melting. It's busy doing `UPDATE` and `INSERT` and can't keep up with all the `SELECT` calls. This is a **Read Contention** bottleneck.

## 2. The Solution: Read Replicas (Read-Write Splitting)
You don't need a "Bigger" DB. You need **More** DBs. 

### The "Scale AI" Read-Write Splitting:
1.  **The Primary (Writer):** Only does `INSERT`, `UPDATE`, `DELETE`. It's the "Source of Truth."
2.  **The Replicas (Readers):** Only do `SELECT`. We have 5 of them. 
3.  **The Logic:** The Primary "Replicates" (streams) every change to the Replicas in real-time (usually < 100ms lag).

### The Implementation in FastAPI:
```python
# --- IN THE DB SESSION ---
def get_db(use_replica: bool = False):
    if use_replica:
        # 1. READ: Use one of the 5 read replicas
        return ReadReplicaPool.get_connection()
    else:
        # 2. WRITE: Must use the single primary writer
        return PrimaryWriterPool.get_connection()

@app.get("/v1/tasks/{id}")
async def get_task_status(id: str, db = Depends(lambda: get_db(use_replica=True))):
    # 3. FAST: This query doesn't bother the 'Writer' at all!
    return await db.fetch_row("SELECT status FROM tasks WHERE id = :id", {"id": id})
```

---

## 3. 🧠 Key Teaching Points:
*   **The Replication Lag Bug**: This is a classic "FDE Interview" problem. A user creates a task (`WRITE` to Primary) and then immediately refreshes the page (`READ` from Replica). The Replica hasn't received the change yet, so the task is missing! This is **Replication Lag**. 
*   **The Fix for Lag**: If you just did a `WRITE`, the next few `READs` for that user should go to the **Primary** (using a `last_write_at` cookie or session state). This is called "Read-Your-Own-Writes" consistency.
*   **Vertical vs. Horizontal Scaling**: 
    *   **Vertical**: Buy a bigger CPU/RAM for the Primary. (Expensive, has a "Limit").
    *   **Horizontal**: Add more Read Replicas. (Cheaper, almost "Unlimited" for reads).
*   **Availability**: If the Primary dies, we "Promote" one of the Replicas to be the new Primary. This is **Failover**.
*   **FDE Tip**: When a customer says "My API is slow but the DB CPU is only at 20%," your first check should be **Lock Contention** (many processes waiting for the same row) or **Connection Pooling** (not enough DB connections available in the pool).
*   **Scale's Best Practice**: For 99% of "Status Polls," use a Read Replica. For "Billing" or "Critical Updates," always use the Primary.
