# Day 04 - SQL: The Transactional Outbox Pattern

How do you save a Task to Postgres AND notify a Slack Channel? This is a **Consistency** lesson.

## 1. The Scenario
Scale AI needs to (1) Save a Task to the database and (2) Send a Webhook to the customer's server. 

**The Bug:**
1. Worker A's server starts a transaction.
2. Worker A saves the task to the DB.
3. Worker A sends the HTTP request to the customer's Webhook.
4. Worker A's server **crashes** before the DB transaction commits.
**Result:** The customer *thinks* they have a task (they got the Webhook!), but the database doesn't have it! This is **Divergent State**. 

**Wait, what if we swap them?**
1. Send the Webhook first.
2. The Webhook succeeds.
3. The DB write fails (e.g., a "Constraint Violation").
**Result:** Again, the customer thinks they have a task, but the DB says no. 

## 2. The Solution: The Transactional Outbox
You CANNOT "rollback" an HTTP request once it's sent. You can only rollback a Database Transaction. 

### The "Scale AI" Correct Strategy (The Outbox):
1.  **The Table:** Create an `outbox_events` table in the SAME database as your tasks.
2.  **The Transaction:** Save the `task` AND the `outbox_event` (the "Intent to send a webhook") in the SAME transaction. If one fails, BOTH fail.
3.  **The Relay:** A separate background "Worker" reads the `outbox_events` table and sends the webhooks.

### The Implementation:
```python
@app.post("/v1/tasks")
async def create_task(db = Depends(get_db)):
    # 1. ATOMIC: Start ONE transaction
    async with db.transaction():
        # 2. SAVE: Create the actual task
        task_id = await db.execute("INSERT INTO tasks (label) VALUES ('test') RETURNING id")
        
        # 3. RECORD: Create the 'Intent' to send a webhook
        # This is the 'Outbox' write.
        await db.execute(
            "INSERT INTO outbox_events (event_type, payload) VALUES (:t, :p)",
            {"t": "task_created", "p": json.dumps({"task_id": task_id})}
        )
    
    # 4. DONE: The transaction is committed. We are safe.
    # The background worker will pick it up and send the webhook now.
    return {"id": task_id}
```

---

## 3. 🧠 Key Teaching Points:
*   **Single-Resource Atomicity**: We only use the database. We don't try to "coordinate" with the outside world (Slack, Webhooks) inside our transaction. This is the **most important lesson** in distributed systems.
*   **The Relay Worker**: This worker can retry as many times as it needs. If the customer's server is down, it just waits and tries again in 5 minutes. No data is ever lost.
*   **Idempotency is Mandatory**: Because the Relay might "Retry" a webhook, the customer's server MUST be idempotent (Day 01 lesson!). 
*   **Eventually Consistent**: The DB and the customer's server will *eventually* match. We trade "Instant Consistency" for "Guaranteed Consistency."
*   **Scaling the Outbox**: At Scale, we might use **CDC (Change Data Capture)** tools like Debezium to read the Postgres "WAL Log" (the database's internal history) and automatically turn every DB write into a Kafka message. This is "Outbox without the code."
