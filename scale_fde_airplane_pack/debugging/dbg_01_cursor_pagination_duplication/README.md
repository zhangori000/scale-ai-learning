# DBG-01: Cursor Pagination Duplication Bug (Debugging Essay)

This chapter treats pagination duplication as a debugging investigation, not just a SQL patch. The practical goal is to train your diagnostic flow: how to reproduce, isolate, and prove a boundary-condition fix.

Symptom reported by users: page 1 and page 2 contain duplicate messages, and some messages disappear when new writes happen between page fetches.

The original query pattern is timestamp-only:

```sql
WHERE created_at <= :cursor_created_at
ORDER BY created_at DESC
LIMIT :limit
```

At first this looks reasonable. The bug appears when multiple rows share identical `created_at`. In that case, the boundary `<=` includes the cursor row again, and timestamp-only ordering has no deterministic tie-breaker.

So there are two coupled defects:

non-strict boundary on primary sort key. missing tie-breaker for equal timestamps.

A strong debugging process starts by proving overlap directly. Fetch page 1, then page 2 with cursor from page 1 tail, and compare IDs. If intersection is non-empty, duplication is objective.

Next, inspect ordering determinism. If rows share timestamp but no secondary key is used in both ORDER BY and cursor predicate, pagination cannot be stable.

Correct model: use composite cursor and composite strict comparison.

Sort order:

`created_at DESC`. `id DESC` (or another unique monotonic tie-breaker).

Boundary for next page:

```sql
WHERE (created_at, id) < (:cursor_created_at, :cursor_id)
```

This means "strictly older in the same total ordering," which prevents replaying cursor row.

Patch implementation:

```python
def list_messages(repo, limit=20, cursor=None):
    base = """
    SELECT id, created_at, content
    FROM messages
    """

    params = {"limit": limit}

    if cursor is None:
        where = ""
    else:
        where = "WHERE (created_at, id) < (:cursor_created_at, :cursor_id)"
        params["cursor_created_at"] = cursor["created_at"]
        params["cursor_id"] = cursor["id"]

    sql = f"""
    {base}
    {where}
    ORDER BY created_at DESC, id DESC
    LIMIT :limit
    """

    rows = repo.query(sql, params)
    next_cursor = None
    if rows:
        tail = rows[-1]
        next_cursor = {"created_at": tail["created_at"], "id": tail["id"]}

    return {"data": rows, "next_cursor": next_cursor}
```

Why this fix works:

tuple ordering defines a total order. strict `<` tuple predicate excludes boundary row. next cursor built from tail row preserves continuity.

Regression tests should prove invariants, not implementation details.

Invariant A: consecutive pages are disjoint by ID.

Invariant B: concatenated pages preserve global ordering.

Invariant C: equal-timestamp rows still paginate without overlap.

```python
def test_no_overlap(repo):
    p1 = list_messages(repo, limit=3)
    p2 = list_messages(repo, limit=3, cursor=p1["next_cursor"])
    assert {r["id"] for r in p1["data"]}.isdisjoint({r["id"] for r in p2["data"]})

def test_same_timestamp_stable(repo):
    p1 = list_messages(repo, limit=1)
    p2 = list_messages(repo, limit=1, cursor=p1["next_cursor"])
    assert p1["data"][0]["id"] != p2["data"][0]["id"]
```

A concise interview narrative:

"I reproduced duplication by checking ID overlap across pages. Root cause was timestamp-only non-strict boundary with no deterministic tie-breaker. I switched to composite cursor `(created_at,id)`, strict tuple comparison, and matching ORDER BY keys, then verified no-overlap and same-timestamp regression tests."
