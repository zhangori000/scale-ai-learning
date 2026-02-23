# Day 03 - Practical: FastAPI Authentication Middleware

Scale AI is a "Multi-tenant" platform. One customer (e.g., OpenAI) should never see another customer's (e.g., Google) data. This starts with **Authentication**.

## 1. The JWT (JSON Web Token) Header
We don't want to hit the database on every single API call to check who the user is. Instead, we use a signed **JWT**.

```python
from fastapi import FastAPI, Depends, Header, HTTPException, status
from typing import Optional
from jose import jwt # 'python-jose' library for JWTs

app = FastAPI()

# Scale AI's Internal Secret
SECRET_KEY = "scale_super_secret"
ALGORITHM = "HS256"

async def get_current_user(authorization: str = Header(...)):
    """
    FastAPI 'Dependency' that extracts and validates the user.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer Token")
        
    token = authorization.split(" ")[1]
    
    try:
        # 1. VALIDATE: Verify the signature and expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. EXTRACT: Get the tenant_id and roles from the token
        tenant_id: str = payload.get("tenant_id")
        user_id: str = payload.get("sub")
        roles: list = payload.get("roles", [])

        if tenant_id is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        return {"id": user_id, "tenant_id": tenant_id, "roles": roles}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/v1/tasks")
async def list_tasks(current_user: dict = Depends(get_current_user)):
    # 3. USE: Now we have the tenant_id for our query
    return {"message": f"Hello {current_user['id']} from {current_user['tenant_id']}"}
```

---

## 2. 🧠 Key Teaching Points:
*   **`Depends(get_current_user)`**: This is FastAPI's "Secret Sauce." It automatically runs the auth code before your route logic. If `get_current_user` raises an `HTTPException`, the route code NEVER runs.
*   **Statelessness**: The server doesn't "store" sessions. The JWT *is* the session. This is why Scale can handle millions of requests—the database isn't a bottleneck for Auth.
*   **`tenant_id`**: This is the most important field at Scale. Every single database query MUST be filtered by this `tenant_id`.
*   **Security Best Practice**: Never trust a `tenant_id` from the URL or the Request Body (e.g., `GET /tasks?tenant_id=google`). A hacker can just change the URL. Always get it from the **Verified JWT**.
