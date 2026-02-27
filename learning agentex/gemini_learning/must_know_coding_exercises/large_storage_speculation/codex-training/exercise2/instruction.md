# Exercise 2: Lazy Hydration With Byte Budgets

Now assume your state can contain many external refs. Hydrating all of them on every request is wasteful and expensive.

A first-class implementation should support partial, budget-aware hydration.

## The Challenge

Implement `StateHydrator.hydrate_selected`.

### Requirements
1. Input:
   - `state`: top-level dict where values may be inline or external refs.
   - `include_fields`: set of top-level field names to hydrate.
   - `byte_budget`: max bytes allowed to download in one call.
2. Behavior:
   - Only hydrate refs for fields listed in `include_fields`.
   - Use an in-call cache so duplicate URIs are fetched once.
   - If hydrated bytes would exceed budget, raise `ByteBudgetExceeded`.
   - Return a new dict; do not mutate input.
3. Integrity:
   - Verify `sha256` for each fetched payload before decoding.

## Starter Code

```python
import asyncio
import copy
import hashlib
import json
from typing import Any


class ByteBudgetExceeded(Exception):
    pass


class MockBlobStore:
    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects
        self.fetch_count = 0

    async def get(self, uri: str) -> bytes:
        await asyncio.sleep(0.01)
        self.fetch_count += 1
        return self.objects[uri]


def make_ref(uri: str, payload: bytes) -> dict[str, Any]:
    return {
        "$type": "external_ref",
        "uri": uri,
        "content_type": "application/json",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "status": "ready",
    }


class StateHydrator:
    def __init__(self, blobs: MockBlobStore):
        self.blobs = blobs

    def _is_ref(self, value: Any) -> bool:
        return isinstance(value, dict) and value.get("$type") == "external_ref"

    async def hydrate_selected(
        self,
        state: dict[str, Any],
        include_fields: set[str],
        byte_budget: int,
    ) -> dict[str, Any]:
        """
        TODO:
        - Create a deep copy of state.
        - For each field in include_fields:
          - If field value is external_ref:
            - enforce byte budget
            - fetch payload (dedupe via URI cache)
            - verify checksum and decode JSON
            - replace field with hydrated object
        - Return hydrated copy.
        """
        pass


async def demo():
    transcript_payload = json.dumps({"text": "hi " * 200}).encode("utf-8")
    profile_payload = json.dumps({"name": "Ada", "tier": "pro"}).encode("utf-8")

    objects = {
        "s3://bucket/transcript.json": transcript_payload,
        "s3://bucket/profile.json": profile_payload,
    }
    blobs = MockBlobStore(objects)
    hydrator = StateHydrator(blobs)

    state = {
        "task_id": "T200",
        "transcript": make_ref("s3://bucket/transcript.json", transcript_payload),
        "user_profile": make_ref("s3://bucket/profile.json", profile_payload),
        "summary": "inline summary",
    }

    hydrated = await hydrator.hydrate_selected(
        state=state,
        include_fields={"user_profile"},
        byte_budget=5_000,
    )
    print(hydrated["user_profile"])
    print("Blob fetch count:", blobs.fetch_count)


if __name__ == "__main__":
    asyncio.run(demo())
```

## Why this is first-class

A first-class ref is queryable and selectively materialized by policy, not blindly expanded.

