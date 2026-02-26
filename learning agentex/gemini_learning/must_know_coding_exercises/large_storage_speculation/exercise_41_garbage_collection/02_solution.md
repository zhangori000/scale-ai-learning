# Solution: The Lifecycle Hook (Garbage Collection)

In a production environment like Scale AI, you never want a database deletion to "wait" for a slow S3 deletion. You use the **Fire-and-Forget** pattern for cleanup.

## The Solution

```python
import asyncio

class StateLifecycleManager:
    def __init__(self, db: dict, blobs: MockBlobStore):
        self.db = db
        self.blobs = blobs

    async def delete_state(self, state_id: str):
        # 1. Fetch the data before we lose the pointer
        state = self.db.get(state_id)
        if not state:
            return

        uri = state.get("external_uri")
        
        # 2. Schedule the heavy lifting in the background
        if uri:
            # We DON'T 'await' this. We fire it into the background
            # so the user gets an immediate 'Success' response.
            asyncio.create_task(self.blobs.delete_file(uri))
            print(f"  [Manager] Scheduled cleanup for {uri}")

        # 3. Clean up the primary record (The DB)
        del self.db[state_id]
        print(f"  [Manager] Database record {state_id} deleted.")
```

## Why this is likely Scale AI's path:
1. **Low Latency**: The user's API request finishes in 10ms, even if S3 takes 500ms to respond.
2. **Reliability**: If the background task fails, a production system would usually put that URI into a "Retry Queue" (like SQS) to ensure it's eventually cleaned up.
3. **Cost Control**: Without this, thousands of "dead" files would stay in S3 forever, causing "Storage Bloat".
