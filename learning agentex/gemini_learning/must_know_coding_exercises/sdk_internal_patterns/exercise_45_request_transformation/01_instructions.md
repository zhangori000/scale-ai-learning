# Exercise 45: Request Transformation (Keyword to JSON)

The SDK methods like `client.tasks.create(name="My Task")` take Python **Keyword Arguments** (`**kwargs`). The server, however, often expects a specific JSON structure (e.g., camelCase keys).

The SDK uses a "Transformer" to bridge this gap.

## The Challenge
Implement a `RequestTransformer`.
1. It takes a Python dictionary with `snake_case` keys.
2. It must return a new dictionary with `camelCase` keys.
3. **The Complexity**: It should handle nested dictionaries (recursively).

## Starter Code
```python
def to_camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def transform_request(data: dict) -> dict:
    """
    TODO: Recursively transform keys to camelCase.
    
    Example input: {"task_id": 1, "metadata": {"user_id": 2}}
    Example output: {"taskId": 1, "metadata": {"userId": 2}}
    """
    pass

# --- Simulation ---
input_data = {
    "task_name": "Transcription",
    "agent_id": "worker-1",
    "config": {
        "max_retries": 3,
        "timeout_seconds": 30
    }
}

output = transform_request(input_data)
print(f"Transformed: {output}")

assert "taskName" in output
assert "maxRetries" in output["config"]
```
