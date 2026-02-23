# Day 10 - Practical: Query Optimization and Database Internals

As an FDE, you'll often have to fix slow APIs. Usually, the problem isn't the Python code—it's the **SQL Query**.

## 1. The Scenario: The "Slow Dashboard"
Scale AI's dashboard for "Project Alpha" takes 15 seconds to load. Project Alpha has 10 million tasks.

**The Query:**
```sql
SELECT * FROM tasks 
WHERE project_id = 'alpha' 
  AND status = 'completed'
ORDER BY created_at DESC 
LIMIT 100;
```

**Why it's slow:**
Without the right index, Postgres has to scan **all 10 million rows**, find the ones that match 'alpha' and 'completed', sort them in memory, and then give you the top 100. This is an `O(N)` scan.

## 2. The Solution: Composite B-Tree Indexes
We need an index that matches our `WHERE` and `ORDER BY` clauses perfectly.

### The "Scale AI" Index Strategy:
1.  **Equality First:** Put columns with `=` first.
2.  **Sort Last:** Put columns used in `ORDER BY` last.

```sql
# THE FIX:
CREATE INDEX idx_tasks_project_status_date 
ON tasks (project_id, status, created_at DESC);
```

**How Postgres uses this:**
1. It jumps directly to the 'alpha' section of the index tree.
2. Inside 'alpha', it jumps to the 'completed' section.
3. Because we indexed by `created_at DESC`, the rows are **already sorted**. 
4. It just grabs the first 100 rows and returns them in **milliseconds**.

---

## 3. 🧠 Key Teaching Points:
*   **The "Rule of Indexing"**: An index is only useful if it "narrows down" the search. If you index a column like `is_active` (which is 50/50 True/False), the index doesn't help much. This is called **Low Cardinality**.
*   **EXPLAIN ANALYZE**: In an interview, if they ask "How would you optimize this?", your first words should be: "**I would run EXPLAIN ANALYZE** to see the query plan." This shows you're a professional who uses data, not guesses.
*   **Index Overhead**: Indexes make `SELECT` fast but `INSERT` slow (because the DB has to update the index tree). At Scale, we balance this by only indexing the "Hot Path" queries.
*   **The "Covering Index"**: If you select only the columns that are in the index (e.g. `SELECT id, created_at`), Postgres doesn't even have to look at the table! It gets everything from the index. This is called an **Index-Only Scan**.
*   **FDE Tip**: When a customer says "The system is slow," your first step is to check the **Slow Query Log** in the database.
