# Exercise 43: Content-Addressable Storage (Deduplication)

In the Agentex docs, they mention that multiple agents might work on the same task. If every agent stores the same 10MB "Initial Knowledge Base" PDF in its own state, you are wasting 90% of your storage.

High-performance systems use **Content-Addressable Storage (CAS)**. Instead of saving a file as `task_1_state.pdf`, you save it as `sha256_of_content.pdf`. If two agents upload the same file, the hash is the same, and you only store it once.

## The Challenge
Implement a `DeduplicatingStorage`.
1. `upload(content)`:
   - Calculate the SHA-256 hash of the content.
   - Check if that hash already exists in storage.
   - If it exists, **don't upload**. Just return the existing URI.
   - If not, save it and return the new URI.

## Starter Code
```python
import hashlib

class DeduplicatingStorage:
    def __init__(self):
        self.phys_storage = {} # Actual bytes on "disk"
        self.upload_count = 0

    def upload(self, content: str) -> str:
        """
        TODO:
        1. Calculate SHA-256 of content.
        2. Check self.phys_storage for the hash.
        3. If missing, increment upload_count and save content.
        4. Return URI: "hash://<sha256>"
        """
        pass

# --- Simulation ---
storage = DeduplicatingStorage()

pdf_content = "This is a massive knowledge base about Scale AI..."

# Agent A uploads it
uri_a = storage.upload(pdf_content)
# Agent B uploads the EXACT SAME THING
uri_b = storage.upload(pdf_content)

print(f"Agent A URI: {uri_a}")
print(f"Agent B URI: {uri_b}")
print(f"Actual Physical Uploads: {storage.upload_count}")

assert uri_a == uri_b
assert storage.upload_count == 1 # Deduplication successful!
```
