# Solution: The Resource Hierarchy (Lazy Loading)

This is the standard architectural pattern for modern Python SDKs (like OpenAI or Stripe).

## The Solution

```python
import functools

class MiniSDK:
    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    @functools.lru_cache(maxsize=None)
    def tasks(self):
        # This code only runs ONCE
        return Tasks(self)

    @property
    @functools.lru_cache(maxsize=None)
    def agents(self):
        return Agents(self)
```

## Why this is Agentex-style:
1. **Performance**: If a developer only needs to use `client.tasks`, the SDK doesn't waste time importing and initializing `Agents`, `Events`, `Spans`, etc.
2. **State Sharing**: Because the same instance of `Tasks` is reused, if the `Tasks` resource maintains any local state (like a small cache or configuration), it persists across the life of the `client` object.
3. **Clean Syntax**: It allows the beautiful `client.tasks.create()` syntax instead of `client.create_task()`.
