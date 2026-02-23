# Day 05 - System/Debug: The "Stuck" Job Mystery

How do you detect when a background worker "dies" invisibly? This is a **Liveness Monitoring** lesson.

## 1. The Scenario
Scale AI has a "Job Service" that runs a 1-hour batch of LLM evaluations. 

**The Bug:** The "Worker" process is in the middle of a job. It hits an "Out of Memory" (OOM) error and is killed by the operating system. 

**Result:** The database still says the job is `RUNNING`. But there is no worker. The job will sit there for weeks. The customer thinks the system is "Stuck." This is a **Zombie Job**.

---

## 2. The Solution: Heartbeats and a "Janitor"
You cannot "Know" that a process died if it's dead. You can only "Know" that it **stopped talking**.

### The "Scale AI" Correct Strategy:
1.  **The Heartbeat:** Every 30 seconds, the worker updates a `last_heartbeat_at` timestamp in the DB.
2.  **The Janitor:** A separate "Cleanup" process (Cron job) runs every 1 minute.
3.  **The Logic:** If a job is `RUNNING` but hasn't sent a heartbeat for 2 minutes, it's a **Zombie**. Mark it as `FAILED` or `RE-QUEUE` it.

### The Implementation:
```python
# --- IN THE WORKER ---
async def run_batch_job(job_id: str):
    while job_not_finished:
        # 1. UPDATE: Tell the world I'm still alive!
        await db.execute(
            "UPDATE jobs SET last_heartbeat_at = NOW() WHERE id = :id", 
            {"id": job_id}
        )
        await do_small_chunk_of_work()

# --- IN THE JANITOR (CRON JOB) ---
async def cleanup_zombie_jobs():
    """
    Runs every 60 seconds.
    """
    # 2. FIND: Any job that is 'RUNNING' but hasn't talked for 120 seconds
    query = """
    UPDATE jobs 
    SET status = 'FAILED', 
        error = 'Worker died (Heartbeat Timeout)'
    WHERE status = 'RUNNING' 
      AND last_heartbeat_at < NOW() - INTERVAL '120 seconds';
    """
    result = await db.execute(query)
    
    if result:
        log.warning(f"Cleaned up {len(result)} zombie jobs!")
```

---

## 3. 🧠 Key Teaching Points:
*   **The "Liveness" Proof**: A `last_heartbeat_at` column is the most robust way to monitor background work in any distributed system. 
*   **The Janitor Interval**: Your "Janitor" interval MUST be longer than your "Heartbeat" interval. If you heartbeat every 30s, don't kill the job after 31s! Give it room for network blips. **Scale's Best Practice**: Heartbeat Interval * 4 = Cleanup Timeout.
*   **Re-queue vs. Fail**: At Scale, if a worker dies, we usually **Re-queue** the job automatically. We only "Fail" it if it has died 3 times (the "Max Retries" policy).
*   **Distributed Systems are Fragile**: Workers will die. Disks will fill up. Networks will flicker. Designing for "The Worker Might Die" is the difference between a Junior and a **Senior Forward Deployed Engineer**.
*   **The "Forward Deployed" Tip**: If an interviewer asks "How do you handle a job that takes 10 hours?", your first answer should be: "I would use **Heartbeats** to ensure the worker is still alive, and I would break the job into **Small Chunks** so that if a worker dies, we don't lose 10 hours of work."
