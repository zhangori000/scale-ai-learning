# Exercise 39: External Storage Reference Simulator

As the Agentex docs mention, "First-class support for external storage references is coming soon." 

The idea is simple: if a piece of data is too big for the 16MB State limit (like a 50MB PDF transcript), you store it in **S3** and put a **pointer** (URI) in the Agentex State.

## The Challenge
Implement an `ExternalStateWrapper`. 
1. `write_large_field(key, data)`: 
   - Simulates saving `data` to an external blob store (e.g., S3).
   - Returns a "Reference URI" (e.g., `s3://bucket/key`).
2. `get_full_state(state_obj)`: 
   - Takes a state object.
   - If it finds an `external_ref`, it "fetches" the data and reconstructs the full object.

## Starter Code
```python
import asyncio

class MockS3:
    def __init__(self):
        self.blobs = {}

    async def upload(self, key: str, data: str) -> str:
        self.blobs[key] = data
        return f"s3://agentex-bucket/{key}"

    async def download(self, uri: str) -> str:
        key = uri.split("/")[-1]
        return self.blobs.get(key, "")

class ExternalStateWrapper:
    def __init__(self, s3: MockS3):
        self.s3 = s3

    async def prepare_state(self, task_id: str, large_transcript: str) -> dict:
        """
        TODO: 
        1. Upload transcript to S3.
        2. Create a state dict that contains only the URI.
        """
        pass

    async def hydrate_state(self, state: dict) -> dict:
        """
        TODO: 
        1. If 'transcript_uri' is in state, download it.
        2. Merge it back into the dictionary.
        """
        pass

# --- Simulation ---
async def main():
    s3 = MockS3()
    wrapper = ExternalStateWrapper(s3)
    
    large_text = "Once upon a time... " * 1000 # Pretend this is 100MB
    
    # 1. Prepare for saving to Agentex DB
    state_to_save = await wrapper.prepare_state("task_1", large_text)
    print(f"State stored in Agentex: {state_to_save}")
    
    # 2. Reconstruct for the Agent to use
    full_state = await wrapper.hydrate_state(state_to_save)
    print(f"Reconstructed transcript length: {len(full_state['transcript'])}")

if __name__ == "__main__":
    asyncio.run(main())
```
