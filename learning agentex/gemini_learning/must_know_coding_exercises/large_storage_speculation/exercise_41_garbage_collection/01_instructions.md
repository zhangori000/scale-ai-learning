# Exercise 41: The Lifecycle Hook (Garbage Collection)

When you store data in an external blob store (like S3), deleting the record in the database doesn't automatically delete the file. Over time, these "orphan" files can cost thousands of dollars.

## The Challenge
Implement a `StateLifecycleManager`.
1. `delete_state(task_id, agent_id)`: 
   - It must first find the state.
   - It must extract any `external_storage_uris`.
   - It must delete the state from the DB.
   - **The Critical Part**: It must trigger a "Background Job" (simulated with `asyncio.create_task`) to delete the actual files from the blob store.

## Starter Code
```python
import asyncio

class MockBlobStore:
    def __init__(self):
        self.files = {"s3://bucket/large-1": "data1", "s3://bucket/large-2": "data2"}

    async def delete_file(self, uri: str):
        await asyncio.sleep(0.5) # Simulate network lag
        if uri in self.files:
            del self.files[uri]
            print(f"  [BlobStore] Successfully deleted: {uri}")

class StateLifecycleManager:
    def __init__(self, db: dict, blobs: MockBlobStore):
        self.db = db # Simulated MongoDB
        self.blobs = blobs

    async def delete_state(self, state_id: str):
        """
        TODO:
        1. Find state in self.db.
        2. If 'external_uri' exists, schedule it for deletion in the background.
        3. Delete the record from self.db.
        """
        pass

# --- Simulation ---
async def main():
    blobs = MockBlobStore()
    db = {
        "state_123": {"task": "T1", "external_uri": "s3://bucket/large-1"}
    }
    manager = StateLifecycleManager(db, blobs)
    
    print("--- Deleting State 123 ---")
    await manager.delete_state("state_123")
    
    # Wait a bit for the background job
    await asyncio.sleep(1)
    print(f"Remaining blobs: {list(blobs.files.keys())}")

if __name__ == "__main__":
    asyncio.run(main())
```
