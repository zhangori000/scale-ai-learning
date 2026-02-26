# Solution: Request Transformation (Keyword to JSON)

In the `scale-agentex-python` repo, you'll see a function called `maybe_transform`. It handles this mapping using Pydantic schemas.

## The Solution

```python
def transform_request(data: dict) -> dict:
    new_data = {}
    for key, value in data.items():
        # 1. Transform the key
        new_key = to_camel_case(key)
        
        # 2. Recurse if value is a dictionary
        if isinstance(value, dict):
            new_data[new_key] = transform_request(value)
        else:
            new_data[new_key] = value
            
    return new_data
```

## Why this is Agentex-style:
1. **Developer Experience (DX)**: Python developers love `snake_case`. Web APIs (like the one in `scale-agentex`) often prefer `camelCase` (the JSON standard). This transformation allows both worlds to use their preferred styles.
2. **Schema Decoupling**: The Platform API can change its internal JSON naming, and the SDK can hide those changes by updating the Transformer, so the end-user's code doesn't break.
3. **Pydantic Integration**: In the real repo, this logic is often handled by `Pydantic`'s `alias` feature, but the recursive logic remains the same.
