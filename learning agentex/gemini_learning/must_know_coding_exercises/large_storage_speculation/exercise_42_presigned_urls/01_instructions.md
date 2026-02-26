# Exercise 42: Presigned URL Negotiation (Zero-Trust)

A common mistake is giving the "Agent" (the Python process) full credentials to S3. If that process is compromised, the attacker has access to ALL your files.

Instead, the **API** (Agentex Platform) should generate a **Presigned URL**—a temporary, cryptographically signed link that only allows access to *one* specific file for *5 minutes*.

## The Challenge
Implement a `SecurityGateway`.
1. `request_upload_url(task_id)`: 
   - Generates a "Temporary Link" for the agent to upload its large data.
2. `Agent.upload_large_data(link, data)`:
   - Uses the link to upload.
3. The platform then saves the **Final Path** in the State record.

## Starter Code
```python
import time
import hmac
import hashlib

class PlatformAPI:
    def __init__(self, secret: str):
        self.secret = secret

    def generate_presigned_url(self, file_path: str) -> str:
        """
        TODO: 
        1. Create an expiry timestamp (now + 300 seconds).
        2. Create a signature using hmac-sha256 of (file_path + expiry).
        3. Return a URL string containing these tokens.
        """
        pass

class AgentWorker:
    async def upload_directly_to_storage(self, signed_url: str, data: str):
        """Simulates an HTTP PUT to S3 using the signed link"""
        print(f"  [Agent] Uploading {len(data)} bytes via Signed URL...")
        # Validate signature (Simulating S3's side)
        if "expires" in signed_url and "sig" in signed_url:
            print("  [S3] Signature Valid! Write accepted.")
            return True
        return False

# --- Simulation ---
platform = PlatformAPI(secret="scale-super-secret")
agent = AgentWorker()

# 1. Agent asks for a place to put 100MB
upload_url = platform.generate_presigned_url("tasks/T1/massive_log.txt")
print(f"Generated URL: {upload_url}")

# 2. Agent uploads directly to S3 (Bypassing the API gateway)
success = asyncio.run(agent.upload_directly_to_storage(upload_url, "huge_content"))
```
