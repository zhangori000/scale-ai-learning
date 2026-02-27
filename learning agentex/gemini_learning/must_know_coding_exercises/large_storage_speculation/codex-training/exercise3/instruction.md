# Exercise 3: First-Class Lifecycle (Revision Index + GC + Pins)

This is the production-hard part of "first-class support."

If refs are part of core state, the platform must manage their lifecycle safely across revisions and deletion.

## The Challenge

Implement `FirstClassStateManager` with revision-aware reference accounting.

### Requirements
1. `save_revision(task_id, revision_id, state)`:
   - Save state snapshot.
   - Extract all external refs from state (nested dict/list supported).
   - Increment `ref_count` per unique URI used in that revision.
2. `delete_revision(task_id, revision_id)`:
   - Remove snapshot.
   - Decrement `ref_count` for URIs used by that revision.
3. `pin_ref(uri, ttl_seconds, now)`:
   - Keep a ref protected from GC until `pinned_until`.
4. `collect_garbage(now)`:
   - Delete blob + index entry for refs where:
     - `ref_count == 0`
     - and `pinned_until` is absent or expired.
   - Return list of deleted URIs.

### Data model

Use:
```python
self.revisions[(task_id, revision_id)] = state_snapshot
self.ref_index[uri] = {"ref_count": int, "pinned_until": float | None}
```

## Starter Code

```python
import asyncio
from typing import Any


class MockBlobStore:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    async def delete(self, uri: str):
        self.objects.pop(uri, None)


class FirstClassStateManager:
    def __init__(self, blobs: MockBlobStore):
        self.blobs = blobs
        self.revisions: dict[tuple[str, str], dict[str, Any]] = {}
        self.ref_index: dict[str, dict[str, Any]] = {}

    def _is_ref(self, value: Any) -> bool:
        return isinstance(value, dict) and value.get("$type") == "external_ref"

    def _extract_refs(self, value: Any) -> set[str]:
        """
        TODO:
        Return all unique reference URIs found recursively in nested dict/list.
        """
        return set()

    async def save_revision(self, task_id: str, revision_id: str, state: dict[str, Any]):
        """
        TODO:
        - Save snapshot.
        - Find unique URIs in this revision.
        - Increment ref_count for each URI.
        """
        pass

    async def delete_revision(self, task_id: str, revision_id: str):
        """
        TODO:
        - Remove snapshot if exists.
        - Decrement ref_count for URIs referenced by this snapshot.
        """
        pass

    def pin_ref(self, uri: str, ttl_seconds: float, now: float):
        """
        TODO:
        Set pinned_until = now + ttl_seconds.
        """
        pass

    async def collect_garbage(self, now: float) -> list[str]:
        """
        TODO:
        - Delete unreferenced + unpinned (or expired pin) URIs.
        - Remove them from ref_index.
        - Return deleted URIs.
        """
        return []


async def demo():
    blobs = MockBlobStore()
    manager = FirstClassStateManager(blobs)

    ref_a = {"$type": "external_ref", "uri": "s3://bucket/A"}
    ref_b = {"$type": "external_ref", "uri": "s3://bucket/B"}
    blobs.objects["s3://bucket/A"] = b"A"
    blobs.objects["s3://bucket/B"] = b"B"

    await manager.save_revision("task-1", "r1", {"doc": ref_a, "other": [ref_b]})
    await manager.save_revision("task-1", "r2", {"doc": ref_a})
    await manager.delete_revision("task-1", "r1")

    manager.pin_ref("s3://bucket/B", ttl_seconds=30, now=100.0)
    deleted = await manager.collect_garbage(now=110.0)
    print("deleted at t=110:", deleted)
    deleted = await manager.collect_garbage(now=131.0)
    print("deleted at t=131:", deleted)


if __name__ == "__main__":
    asyncio.run(demo())
```

## Why this is first-class

You are not just storing pointers. You are managing reference lifecycle as a core platform concern.

