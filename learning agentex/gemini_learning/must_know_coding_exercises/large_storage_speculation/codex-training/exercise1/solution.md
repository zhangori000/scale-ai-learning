# Solution: First-Class ExternalRef Envelope

```python
import asyncio
import copy
import hashlib
import json
from typing import Any


class MockBlobStore:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    async def put(self, uri: str, payload: bytes):
        self.objects[uri] = payload

    async def get(self, uri: str) -> bytes:
        return self.objects[uri]


class StateExternalizer:
    def __init__(self, blobs: MockBlobStore, max_inline_bytes: int = 80):
        self.blobs = blobs
        self.max_inline_bytes = max_inline_bytes

    def _to_json_bytes(self, value: Any) -> bytes:
        return json.dumps(value, sort_keys=True).encode("utf-8")

    def _is_external_ref(self, value: Any) -> bool:
        return isinstance(value, dict) and value.get("$type") == "external_ref"

    async def persist_state(self, task_id: str, state: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(state)

        for field, value in list(result.items()):
            payload = self._to_json_bytes(value)
            if len(payload) <= self.max_inline_bytes:
                continue

            uri = f"s3://agentex-state/{task_id}/{field}.json"
            sha = hashlib.sha256(payload).hexdigest()
            await self.blobs.put(uri, payload)

            result[field] = {
                "$type": "external_ref",
                "uri": uri,
                "content_type": "application/json",
                "sha256": sha,
                "size_bytes": len(payload),
                "status": "ready",
            }

        return result

    async def hydrate_state(self, saved_state: dict[str, Any]) -> dict[str, Any]:
        hydrated = copy.deepcopy(saved_state)

        for field, value in list(hydrated.items()):
            if not self._is_external_ref(value):
                continue

            payload = await self.blobs.get(value["uri"])
            actual_sha = hashlib.sha256(payload).hexdigest()
            if actual_sha != value["sha256"]:
                raise ValueError(f"checksum mismatch for {value['uri']}")

            hydrated[field] = json.loads(payload.decode("utf-8"))

        return hydrated


async def demo():
    blobs = MockBlobStore()
    externalizer = StateExternalizer(blobs, max_inline_bytes=80)

    original = {
        "task": "T-100",
        "summary": "small",
        "transcript": "hello " * 100,
        "tool_trace": [{"tool": "search", "q": "policy"} for _ in range(20)],
    }

    stored = await externalizer.persist_state("task-100", original)
    print("Stored state:")
    print(json.dumps(stored, indent=2))

    hydrated = await externalizer.hydrate_state(stored)
    print("\\nHydrated transcript length:", len(hydrated["transcript"]))


if __name__ == "__main__":
    asyncio.run(demo())
```

## Key idea

First-class support starts with a typed envelope plus integrity metadata. That makes refs auditable and safe to hydrate.

