# Day 03 - SQL: Multi-Tenant Query Guardrails

Once you know the `tenant_id` from the JWT, how do you make sure the SQL code doesn't "accidentally" show OpenAI's data to Google? This is a **Row-Level Security** problem.

## 1. The Schema
Every single table at Scale must have a `tenant_id` column.

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL, # 'openai', 'google', etc.
    label TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

# Important index for performance
CREATE INDEX idx_tasks_tenant ON tasks (tenant_id, created_at DESC);
```

## 2. The Python Repository (The "Safe" Way)
At Scale, we never write `SELECT * FROM tasks`. We always write `WHERE tenant_id = :t`.

```python
from fastapi import FastAPI, Depends, HTTPException

class TaskRepo:
    def __init__(self, db, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def list_tasks(self, limit: int = 100):
        # 1. ENFORCE the boundary!
        query = """
        SELECT * FROM tasks 
        WHERE tenant_id = :t 
        ORDER BY created_at DESC 
        LIMIT :l;
        """
        # 2. PASS the tenant_id from the JWT
        rows = await self.db.fetch_all(query, {"t": self.tenant_id, "l": limit})
        return rows

@app.get("/v1/tasks")
async def get_my_tasks(
    current_user: dict = Depends(get_current_user), # From File 01
    db = Depends(get_db)
):
    # 3. CONTEXT: Create a repo scoped to THIS user's tenant
    repo = TaskRepo(db, current_user['tenant_id'])
    return await repo.list_tasks()
```

---

## 3. 🧠 Key Teaching Points:
*   **Contextual Repositories**: This is an architectural pattern. We don't just "pass around" a database object. We create a "Repository" object that is *already configured* with the `tenant_id`. This makes it hard to "forget" the `WHERE tenant_id` clause.
*   **The Composite Index**: Notice `idx_tasks_tenant (tenant_id, created_at DESC)`. This is a "Compound Index." In Postgres, it means the database can find all of OpenAI's tasks and sort them by date in a single, lightning-fast operation.
*   **IDOR Protection**: IDOR stands for "Insecure Direct Object Reference." If a user tries `GET /tasks/123` where `123` belongs to another tenant, your code MUST return a `404` or `403`. 
    *   **Scale's Best Practice**: Don't even check if it exists! Just query `WHERE id = 123 AND tenant_id = 'my_tenant'`. If no rows are found, return `404`. This is more secure than leaking that ID 123 exists.
*   **Logical Isolation**: This is "Multi-tenancy on a budget." We share the same database (more efficient), but keep the data logically isolated.
