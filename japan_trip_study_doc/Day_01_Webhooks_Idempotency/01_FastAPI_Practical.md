# Day 01 - Practical: Building a Webhook Ingestor in FastAPI

In this lesson, we build the "front door" for Scale AI's data. When a provider (like a labeling partner) finishes a task, they send us a Webhook. 

## 1. The FastAPI Webhook Route
FastAPI uses `Request` and `Header` to extract data. We use a Pydantic model `WebhookPayload` to validate the incoming JSON.

```python
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from pydantic import BaseModel
import hmac
import hashlib

app = FastAPI()

class WebhookPayload(BaseModel):
    event_id: str
    data: dict

# This is our 'Secret Key' shared with the provider
WEBHOOK_SECRET = "scale_secret_123"

@app.post("/v1/ingest", status_code=202) # 202 = Accepted for async processing
async def ingest_webhook(
    payload: WebhookPayload,
    x_signature: str = Header(...), # FastAPI extracts 'X-Signature' automatically
    db = Depends(get_db) # We'll define this in the next file
):
    # 1. SECURITY: Verify the signature
    # In a real interview, you MUST check this.
    # We hash the raw body with our secret and compare it to the header.
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode(), 
        payload.model_dump_json().encode(), 
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(x_signature, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. IDEMPOTENCY: Check if we've seen this event_id
    success = await db.insert_event_idempotent(payload.event_id, payload.data)
    
    if not success:
        # We've already processed this. Return 200/202 to stop the provider from retrying,
        # but don't do any work.
        return {"status": "already_processed"}

    # 3. ASYNC: Put it in a queue (offload the work)
    await queue.publish(payload.event_id)
    
    return {"status": "accepted", "id": payload.event_id}
```

## 🧠 Key Teaching Points:
*   **`status_code=202`**: Very important. It tells the caller "I got it, I'll deal with it later." This keeps your API fast.
*   **`hmac.compare_digest`**: Never use `==` for signatures. It's vulnerable to "Timing Attacks." Always use the built-in compare function.
*   **Pydantic Validation**: Notice how we don't have to manually check if `event_id` is a string. FastAPI/Pydantic does it for us.
