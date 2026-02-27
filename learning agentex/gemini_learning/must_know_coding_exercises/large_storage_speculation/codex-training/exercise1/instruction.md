# Exercise 1: First-Class ExternalRef Envelope

In `agentex/docs/docs/concepts/state.md`, the docs say first-class support for external storage references is coming soon.

What does "first-class" mean here?
1. Not just raw URI strings in state.
2. References have a schema and metadata (checksum, size, type, status).
3. The system can validate and hydrate references safely.

## The Challenge

Implement a `StateExternalizer` that upgrades large fields into structured references.

### Requirements
1. `persist_state(task_id, state)`:
   - Keep small values inline.
   - Offload large values to blob storage.
   - Replace offloaded values with a typed reference envelope.
2. `hydrate_state(saved_state)`:
   - Detect reference envelopes.
   - Download and deserialize the payload.
   - Verify `sha256` before returning hydrated state.
3. The reference envelope shape must be:

```python
{
  "$type": "external_ref",
  "uri": "...",
  "content_type": "application/json",
  "sha256": "...",
  "size_bytes": 1234,
  "status": "ready"
}
```

## Starter Code

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
        """
        TODO:
        - Copy incoming state.
        - For each top-level field, compute json bytes.
        - If payload length > max_inline_bytes:
          - write payload to uri: s3://agentex-state/{task_id}/{field}.json
          - compute sha256
          - replace field with first-class external_ref envelope
        """
        pass

    async def hydrate_state(self, saved_state: dict[str, Any]) -> dict[str, Any]:
        """
        TODO:
        - Copy saved_state.
        - For each top-level field that is external_ref:
          - load payload by uri
          - verify sha256
          - json.loads(payload) back into hydrated value
        """
        pass


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

## Why this is first-class

You are defining a durable contract for external refs instead of sprinkling raw storage pointers throughout state.

