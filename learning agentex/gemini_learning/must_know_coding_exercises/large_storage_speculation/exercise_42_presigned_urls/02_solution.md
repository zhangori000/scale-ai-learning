# Solution: Presigned URL Negotiation (Zero-Trust)

This is the most secure way to handle large file uploads in a multi-tenant cloud environment.

## The Solution

```python
import time
import hmac
import hashlib

class PlatformAPI:
    def __init__(self, secret: str):
        self.secret = secret

    def generate_presigned_url(self, file_path: str) -> str:
        # 1. Define the lease (5 minutes)
        expiry = int(time.time()) + 300
        
        # 2. Create the cryptographic signature
        # We sign the path and the expiry time so neither can be tampered with.
        message = f"{file_path}{expiry}".encode()
        signature = hmac.new(
            self.secret.encode(), 
            message, 
            hashlib.sha256
        ).hexdigest()
        
        # 3. Construct the "Access Key"
        return f"https://s3.scale.com/{file_path}?expires={expiry}&sig={signature}"
```

## Why this is likely Scale AI's path:
1. **Least Privilege**: The Agent process only knows how to write to *one* file. It can't list other users' files or delete its own history.
2. **Bandwidth Savings**: A 1GB upload goes from the Agent's server directly to S3. If it went *through* the Agentex API, the API server would be pegged at 100% CPU/Network just moving bytes.
3. **Auditability**: Every signed URL request can be logged by the Platform API, giving a perfect audit trail of who uploaded what and when.
