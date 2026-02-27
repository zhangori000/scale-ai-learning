# Solution: First-Class Lifecycle (Revision Index + GC + Pins)

```python
import asyncio
import copy
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
        return isinstance(value, dict) and value.get("$type") == "external_ref" and "uri" in value

    def _extract_refs(self, value: Any) -> set[str]:
        uris: set[str] = set()

        if self._is_ref(value):
            uris.add(value["uri"])
            return uris
        if isinstance(value, dict):
            for child in value.values():
                uris.update(self._extract_refs(child))
            return uris
        if isinstance(value, list):
            for child in value:
                uris.update(self._extract_refs(child))
            return uris
        return uris

    async def save_revision(self, task_id: str, revision_id: str, state: dict[str, Any]):
        key = (task_id, revision_id)
        snapshot = copy.deepcopy(state)
        self.revisions[key] = snapshot

        uris = self._extract_refs(snapshot)
        for uri in uris:
            entry = self.ref_index.setdefault(uri, {"ref_count": 0, "pinned_until": None})
            entry["ref_count"] += 1

    async def delete_revision(self, task_id: str, revision_id: str):
        key = (task_id, revision_id)
        snapshot = self.revisions.pop(key, None)
        if snapshot is None:
            return

        uris = self._extract_refs(snapshot)
        for uri in uris:
            entry = self.ref_index.get(uri)
            if not entry:
                continue
            entry["ref_count"] = max(0, entry["ref_count"] - 1)

    def pin_ref(self, uri: str, ttl_seconds: float, now: float):
        entry = self.ref_index.setdefault(uri, {"ref_count": 0, "pinned_until": None})
        entry["pinned_until"] = now + ttl_seconds

    async def collect_garbage(self, now: float) -> list[str]:
        deleted: list[str] = []

        for uri, entry in list(self.ref_index.items()):
            ref_count = int(entry.get("ref_count", 0))
            pinned_until = entry.get("pinned_until")
            is_pinned = pinned_until is not None and pinned_until > now

            if ref_count == 0 and not is_pinned:
                await self.blobs.delete(uri)
                deleted.append(uri)
                del self.ref_index[uri]

        return deleted


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
    # counts now: A=1, B=0

    manager.pin_ref("s3://bucket/B", ttl_seconds=30, now=100.0)
    deleted = await manager.collect_garbage(now=110.0)
    print("deleted at t=110:", deleted)  # expected []

    deleted = await manager.collect_garbage(now=131.0)
    print("deleted at t=131:", deleted)  # expected ['s3://bucket/B']


if __name__ == "__main__":
    asyncio.run(demo())
```

## Key idea

First-class support requires reference accounting across revisions, not just read/write helpers.

