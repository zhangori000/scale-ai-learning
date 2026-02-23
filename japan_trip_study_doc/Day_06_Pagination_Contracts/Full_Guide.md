# Day 06: Pagination & Data Contracts
**Focus:** Building stable APIs for massive datasets (like Scale's task history).

## 01. The Problem: The "Duplicate Row" Mystery
**Scenario:** A user is scrolling through a list of 1 million labeling tasks. They see Task #45 on Page 1. They click "Next", and Task #45 appears again at the top of Page 2. 

**Why it happens:** 
1. **The "Offset" Trap:** Using `LIMIT 10 OFFSET 10` is slow and unstable. If a new task is added to Page 1 while the user is reading, every task "shifts" down by one, causing the last task of Page 1 to become the first task of Page 2.
2. **The "Non-Unique Sort" Trap:** Sorting by `created_at` isn't enough. If two tasks have the exact same timestamp (common in high-volume systems), the database might return them in a different order every time.

---

## 02. The Solution: Composite Cursor Pagination
To solve this, we use **Cursors** instead of Offsets. A cursor is an "anchor" that says "Give me everything *after* this specific task."

### The "Scale AI" Standard:
1. **Unique Tie-breaker:** Always sort by a primary key (`id`) in addition to your main sort key (`created_at`).
2. **Strict Comparison:** Use tuple comparison `(created_at, id) < (cursor_ts, cursor_id)` to ensure you never see the anchor task again.
3. **Opaque Cursors:** Encode your cursor (e.g., Base64) so the frontend doesn't try to "guess" it.

---

## 03. The Working Code (FastAPI + SQL)
Here is a complete, production-ready implementation of a paginated Task API.

### `schemas.py` (Data Models)
```python
from pydantic import BaseModel
from typing import List, Optional
import base64
import json

class Task(BaseModel):
    id: str
    created_at: int
    label: str

class PaginatedResponse(BaseModel):
    items: List[Task]
    next_cursor: Optional[str]
    has_more: bool

def encode_cursor(ts: int, task_id: str) -> str:
    """Creates an opaque Base64 string from task data."""
    data = json.dumps({"ts": ts, "id": task_id})
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_cursor(cursor_str: str) -> dict:
    """Decodes the Base64 string back into a dictionary."""
    data = base64.urlsafe_b64decode(cursor_str.encode()).decode()
    return json.loads(data)
```

### `main.py` (The API)
```python
from fastapi import FastAPI, Query, HTTPException
from .schemas import Task, PaginatedResponse, encode_cursor, decode_cursor

app = FastAPI()

@app.get("/tasks", response_model=PaginatedResponse)
async def list_tasks(limit: int = 10, cursor: Optional[str] = None):
    # 1. Parse Cursor
    params = {"limit": limit + 1} # Fetch 1 extra to see if there's a "Next Page"
    where_clause = ""
    
    if cursor:
        try:
            c = decode_cursor(cursor)
            # TUPLE COMPARISON: Strictly 'older' than the cursor
            where_clause = "WHERE (created_at, id) < (:ts, :id)"
            params.update({"ts": c["ts"], "id": c["id"]})
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    # 2. Execute Query (Pseudo-code for SQL)
    # ORDER BY must match the cursor logic
    query = f"SELECT * FROM tasks {where_clause} ORDER BY created_at DESC, id DESC LIMIT :limit"
    rows = await db.fetch_all(query, params)

    # 3. Check for More
    has_more = len(rows) > limit
    items = rows[:limit]
    
    # 4. Generate Next Cursor
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor(last["created_at"], last["id"])

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more
    }
```

---

## 04. Architectural Tradeoffs: How to Ace the Interview

### Q: Why not just use `OFFSET`?
**A:** "Two reasons: **Performance** and **Consistency**. `OFFSET 1,000,000` requires the database to scan and discard a million rows, which is `O(N)`. Cursors use an index to jump directly to the right spot, which is `O(log N)`. Also, `OFFSET` is vulnerable to 'drifting' when data is inserted or deleted mid-scroll."

### Q: What if the task at the cursor is deleted?
**A:** "That's the beauty of the **Composite Tuple Comparison**. Even if the exact ID is gone, the `created_at < cursor_ts` part of the logic still works perfectly. The 'anchor' doesn't need to exist for the comparison to be valid."

### Q: Why Base64 encode the cursor?
**A:** "It's a **Data Contract**. If I send a raw timestamp, the frontend might try to manipulate it. By making it opaque, I signal that the cursor is a 'black box' owned by the backend. It also allows me to change the cursor format (e.g., adding a version number) without breaking the frontend."
