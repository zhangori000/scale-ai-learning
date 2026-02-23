# Day 10 - Code: Recursive CTEs (Hierarchical Task Structures)

How do you handle a "Tree" of tasks at Scale AI? This is a **Hierarchical Query** lesson.

## 1. The Scenario
Scale AI has "Parent Tasks" (e.g., an entire video) and "Child Tasks" (e.g., each frame in that video). Sometimes a child has its own children (e.g., each object inside a frame).

**The Problem:** You want to find "All descendants of Video #123." You could use 5 different SQL queries (`SELECT children`, then `SELECT grandchildren`), but that's slow and hard to code.

---

## 2. The Solution: Recursive Common Table Expressions (CTEs)
Postgres has a "Secret Superpower": **WITH RECURSIVE**. It allows you to "walk the tree" in ONE query.

### The "Scale AI" Hierarchical Query:
```sql
# THE FIX:
WITH RECURSIVE task_tree AS (
    # 1. BASE CASE: Start with the Parent (Video #123)
    SELECT id, parent_id, label
    FROM tasks
    WHERE id = '123'
    
    UNION ALL
    
    # 2. RECURSIVE STEP: Find all children of the rows we just found
    SELECT t.id, t.parent_id, t.label
    FROM tasks t
    JOIN task_tree tt ON t.parent_id = tt.id
)
# 3. FINAL RESULT: Now we have the whole tree!
SELECT * FROM task_tree;
```

---

## 3. 🧠 Key Teaching Points:
*   **The Recursive Anchor**: This is the "Base Case" (where `id = '123'`). This tells the database where to start.
*   **The Recursive Union**: This is the "Recursive Step." The database keeps joining the `tasks` table with the *results* of the previous step until it hits a leaf (no more children).
*   **The Depth Limit**: In a real Scale production system, you MUST put a "Depth Limit" (e.g., `WHERE depth < 10`) to prevent infinite loops if someone accidentally creates a "Circular Task" (A is parent of B, B is parent of A).
*   **Adjacency List vs. Path (Ltree)**: In this model (`parent_id`), we use an "Adjacency List." It's simple to insert but slower for deep trees. At Scale, for very deep trees, we might use **Ltree** (storing the path as `123.456.789`), which is much faster for queries but harder to update.
*   **Why at Scale?**: Video annotation, 3D point cloud segmentation, and document processing all use "Hierarchical Models." Being able to write a single SQL query to find an entire tree is a **Senior FDE skill**.
*   **FDE Tip**: When an interviewer says "Design a system for nested labels," your first response should be: "I would use a **Self-Referencing parent_id column** and query it with a **Recursive CTE**."
