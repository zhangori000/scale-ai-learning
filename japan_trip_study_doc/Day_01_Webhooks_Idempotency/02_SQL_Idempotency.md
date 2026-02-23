# Day 01 - SQL: Atomic Idempotency Patterns

How do you ensure you don't save the same data twice if the API is hit by two identical requests at the exact same millisecond? You use the **Database** as your source of truth.

## 1. The Schema
We use `JSONB` in Postgres to store the raw payload. This is great for Scale because task data format changes often.

```sql
CREATE TABLE webhook_events (
    event_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    status TEXT DEFAULT 'received',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 2. The Atomic "Insert or Skip"
In your Python code, you don't want to `SELECT` then `INSERT`. That creates a "Race Condition." Instead, use `ON CONFLICT`.

```python
async def insert_event_idempotent(self, event_id: str, data: dict) -> bool:
    """
    Returns True if the event was NEW.
    Returns False if the event was a DUPLICATE.
    """
    query = """
    INSERT INTO webhook_events (event_id, payload)
    VALUES (:id, :p)
    ON CONFLICT (event_id) DO NOTHING
    RETURNING 1;
    """
    result = await self.db.execute(query, {"id": event_id, "p": json.dumps(data)})
    
    # If RETURNING 1 gave us a row, it was a new insert.
    # If result is empty, it was a conflict (duplicate).
    return len(result) > 0
```

## 🧠 Why this is "Scale-Level" Engineering:
*   **Atomic Operations:** By using `ON CONFLICT`, the database handles the locking for you. No two threads can insert the same `event_id` simultaneously.
*   **JSONB Storage:** In AI/ML, data schemas evolve every week. Storing the raw webhook as `JSONB` means you never lose data if your Python code isn't ready for a new field yet.
*   **Time-Zoned Timestamps:** Always use `TIMESTAMPTZ`. Scale operates globally (Japan, US, Philippines). Handling timezones at the DB level prevents massive headaches.
