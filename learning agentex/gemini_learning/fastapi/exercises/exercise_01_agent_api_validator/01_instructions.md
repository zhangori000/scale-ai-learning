# Exercise: The Agent API Key Validator

In `scale-agentex`, security is handled by complex middleware and dependency injection chains. This exercise will help you master the **Annotated Dependencies** and **Custom Exception** patterns found in the real codebase.

## The Goal
Create a small FastAPI app that validates an `X-Agent-Key` header. If the key is missing or invalid, it should raise a specific error.

## Requirements
1.  **Custom Exception:** Create a class `InvalidKeyException` that inherits from `HTTPException`. It should always return a `403 Forbidden` status code.
2.  **Mock Database:** Create a set or list of "valid keys" (e.g., `{"secret-agent-1", "top-priority-agent"}`).
3.  **Dependency:** Create an async function `validate_agent_key` that:
    *   Takes the `X-Agent-Key` from the request headers.
    *   Checks if it's in your "valid keys" set.
    *   Raises `InvalidKeyException` if it's not.
4.  **Annotated Type:** Use `typing.Annotated` to create a reusable type called `ValidKey`.
5.  **Route:** Create a protected route `@app.get("/secure-data")` that uses your `ValidKey` dependency.

## Starter Code
```python
from typing import Annotated
from fastapi import FastAPI, Header, HTTPException, Depends

app = FastAPI()

# 1. Your Custom Exception here...

# 2. Your Mock DB here...

# 3. Your Dependency function here...

# 4. Your Annotated type here...

# 5. Your Route here...
```

---
### When you are ready, check the solution file!
