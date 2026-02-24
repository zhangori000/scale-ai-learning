# Solution: The Agent API Key Validator

This solution mirrors the patterns used in `src/utils/authorization_shortcuts.py` and `src/api/app.py`.

```python
import asyncio
from typing import Annotated
from fastapi import FastAPI, Header, HTTPException, Depends, status

app = FastAPI()

# 1. Custom Exception
# This allows for consistent error reporting across the entire app.
class InvalidKeyException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Your Agent Key is invalid or has expired."
        )

# 2. Mock Database
VALID_AGENT_KEYS = {"secret-agent-1", "top-priority-agent", "dev-agent-99"}

# 3. Dependency Function
# Notice the 'async' - this allows for non-blocking DB checks.
async def validate_agent_key(x_agent_key: Annotated[str | None, Header()] = None):
    # Simulate an async DB lookup (taking 0.1s)
    await asyncio.sleep(0.1)
    
    if not x_agent_key or x_agent_key not in VALID_AGENT_KEYS:
        # We don't just return False; we raise the exception immediately.
        # This stops the route logic from ever running!
        raise InvalidKeyException()
    
    return x_agent_key

# 4. Annotated Type (Reusable & Clean)
# This is a 'best practice' found in the Scale-Agentex codebase.
# It makes route signatures very clean and readable.
ValidKey = Annotated[str, Depends(validate_agent_key)]

# 5. Protected Route
@app.get("/secure-data")
async def get_secure_data(agent_key: ValidKey):
    # If we reach this line, we KNOW the key is valid.
    # We even get the 'agent_key' string back for use in our logic!
    return {
        "message": "Access granted to secure intelligence data.",
        "authorized_agent": agent_key,
        "payload": "Secret coordinates: 37.7749 N, 122.4194 W"
    }

# To test:
# uvicorn main:app --reload
# curl -H "X-Agent-Key: secret-agent-1" http://localhost:8000/secure-data
```

### Key Takeaways from the Solution:
1.  **Inheritance:** By inheriting from `HTTPException`, you can pre-fill information like `status_code` so your route functions don't have to worry about it.
2.  **Annotated:** This is a modern Python feature that combines a type (`str`) with metadata (`Depends(validate_agent_key)`). It's used everywhere in `scale-agentex` to manage dependencies cleanly.
3.  **Security First:** The dependency check happens **before** the route code is executed, preventing unauthorized access to sensitive logic.
