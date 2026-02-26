# Solution: External Storage Reference Simulator

This pattern allows Agentex to handle gigabytes of data while keeping its internal "State" object small, fast, and searchable.

## The Solution

```python
import asyncio

class ExternalStateWrapper:
    def __init__(self, s3: MockS3):
        self.s3 = s3

    async def prepare_state(self, task_id: str, large_transcript: str) -> dict:
        # 1. Offload the heavy data to S3
        # We use the task_id to ensure a unique key in S3
        s3_key = f"transcripts/{task_id}.txt"
        uri = await self.s3.upload(s3_key, large_transcript)
        
        # 2. Store only the POINTER in the Agentex State
        return {
            "transcript_uri": uri,
            "has_external_data": True
        }

    async def hydrate_state(self, state: dict) -> dict:
        # Check if this state has external references
        if "transcript_uri" in state:
            uri = state["transcript_uri"]
            print(f"  [Hydrator] Fetching external data from {uri}...")
            
            # 3. Pull the data back on demand
            large_data = await self.s3.download(uri)
            
            # Merge it back so the Agent code doesn't have to know about S3
            state["transcript"] = large_data
            
        return state
```

## Why this is Agentex-style:
1. **Separation of Concerns**: Agentex (the Platform) manages the metadata, while S3 (the Storage) manages the raw bytes.
2. **Cost Efficiency**: Storing 1GB in S3 is significantly cheaper than storing 1GB in a high-performance MongoDB/Postgres index.
3. **Future Proofing**: By using URIs (`s3://...`), Agentex can eventually support other storage providers (Google Cloud Storage, Azure Blob) without changing the core State API.
