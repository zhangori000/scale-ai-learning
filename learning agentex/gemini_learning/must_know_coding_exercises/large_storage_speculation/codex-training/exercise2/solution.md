# Solution: Lazy Hydration With Byte Budgets

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
        result = copy.deepcopy(state)
        uri_cache: dict[str, bytes] = {}
        used_bytes = 0

        for field in include_fields:
            if field not in result:
                continue
            value = result[field]
            if not self._is_ref(value):
                continue

            size = int(value["size_bytes"])
            if used_bytes + size > byte_budget:
                raise ByteBudgetExceeded(
                    f"budget exceeded while hydrating {field}: {used_bytes + size} > {byte_budget}"
                )

            uri = value["uri"]
            if uri not in uri_cache:
                uri_cache[uri] = await self.blobs.get(uri)
            payload = uri_cache[uri]

            actual_sha = hashlib.sha256(payload).hexdigest()
            if actual_sha != value["sha256"]:
                raise ValueError(f"checksum mismatch for {uri}")

            result[field] = json.loads(payload.decode("utf-8"))
            used_bytes += size

        return result


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

## Key idea

First-class support needs policy controls: selective hydration, integrity checks, and byte limits.

