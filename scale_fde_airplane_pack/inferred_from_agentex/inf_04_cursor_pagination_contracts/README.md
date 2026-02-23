# INF-04 Coding Round Editorial: Cursor Pagination Contracts and Validation

This chapter is a deep guide for building cursor pagination correctly when data changes while users scroll.

Grounded source files:

`scale-agentex/agentex/src/utils/pagination.py`. `scale-agentex/agentex/src/api/routes/messages.py`. `scale-agentex/agentex/src/domain/services/task_message_service.py`. `scale-agentex/agentex/src/adapters/crud_store/adapter_mongodb.py`.

## The Real Problem

Cursor pagination is not an encoding trick. It is a long-term API contract between:

sort order. cursor payload. boundary predicate.

If these drift, you get duplicates, gaps, and unstable scroll behavior.

## Mental Model

A cursor says: "continue from this exact position in this exact ordering system."

That means you must define deterministic ordering first.

## Ordering Foundation

In this code family, reliable ordering is:

primary: `created_at DESC`. tie-breaker: `_id ASC`.

Tie-breaker is mandatory because timestamps can collide.

## Why Interviewers Ask This

They want to know whether you understand that pagination correctness is a data-contract problem under mutation, not a frontend convenience feature.

## Step 0: Freeze The Contract

Contract fields:

cursor schema version. sort fields and direction. behavior for invalid/stale cursor.

Do not code before writing this contract.

## Step 1: Define Cursor Schema

Versioned opaque cursor:

```json
{ "v": 1, "id": "...", "created_at": "..." }
```

Encode with URL-safe base64.

Why include version? So you can evolve schema without breaking old clients.

## Step 2: Validate Cursor Strictly

Decode pipeline:

base64 decode. JSON parse. schema validate. version validate.

On failure, return `400 invalid_cursor`.

Do not silently ignore invalid cursor and restart from beginning.

## Step 3: Convert Cursor To Boundary Predicate

Given descending time order:

Older page predicate:

`created_at < anchor_ts` OR (`created_at == anchor_ts` AND `_id > anchor_id`).

Newer page predicate:

`created_at > anchor_ts` OR (`created_at == anchor_ts` AND `_id < anchor_id`).

This pair must be mathematically consistent.

## Step 4: Fetch `limit + 1`

Always query one extra row.

extra row exists -> `has_more=true`. extra row missing -> `has_more=false`.

Then return first `limit` rows.

## Step 5: Build Next Cursor

Create `next_cursor` from last returned row, not the extra row.

This keeps continuity stable.

## Step 6: Handle Cursor Anchor Missing

If anchor row was deleted, choose and document one policy:

`409 cursor_not_found`. empty page with reason code.

Undocumented fallback creates confusing client behavior.

## Step 7: End-to-End Endpoint Shape

```python
cursor_data = decode_validate(cursor) if cursor else None
before_id, after_id = map_direction(cursor_data, direction)
rows = repo.query(task_id, before_id, after_id, limit + 1)
has_more = len(rows) > limit
page = rows[:limit]
next_cursor = encode_cursor_from(page[-1]) if has_more and page else None
return {"data": page, "next_cursor": next_cursor, "has_more": has_more}
```

## Step 8: Worked Example

Suppose sorted IDs are `[M9, M8, M7, M6, M5]`.

Request 1 (`limit=2`) returns `[M9, M8]`, cursor from `M8`.

Request 2 with cursor `M8` and `older` returns `[M7, M6]`.

No overlap, no gap.

If `M8` deleted before request 2, follow documented stale-cursor policy.

## Step 9: Implementation Order

formalize sort + tie-break in repository. implement strict decode/validate. implement boundary predicate mapping. implement limit+1 and cursor generation. implement stale-anchor policy. add tests.

## Step 10: Tests You Need

Test 1: no overlaps across full traversal.

Test 2: no gaps across full traversal.

Test 3: equal timestamps still deterministic.

Test 4: invalid cursor rejected with `400`.

Test 5: stale anchor follows documented policy.

Test 6: inserts during pagination do not break already-traversed history.

## Common Mistakes

missing tie-breaker. silent invalid cursor fallback. wrong comparison signs in older/newer predicates. building next cursor from wrong row.

## Interview Wrap-Up Script

"I design cursor pagination as a stable contract. I lock deterministic tuple ordering, validate versioned opaque cursors strictly, and map cursor boundaries with mathematically consistent predicates for older/newer traversal. Then I verify no overlap and no gap under mutation."
