# Exercise: The Singleton Dependency Factory

In `scale-agentex`, we have many heavy "Infrastructure" pieces:
*   **Postgres** (Relational Data)
*   **Redis** (Fast Caching)
*   **Temporal** (Durable Workflows)

We don't want to recreate these connections on every single API call. We want to **reuse** them.

## The Goal
Create a `GlobalDependencies` singleton class that lazily initializes its resources and provides them to your app.

## Requirements
1.  **The Singleton:** Create a `GlobalDependencies` class. It should have a `self.db_pool` and `self.cache_pool`, initially set to `None`.
2.  **Lazy Initialization:** Create a method `get_db_pool()` that:
    *   If `self.db_pool` is `None`, prints "CONNECTING TO POSTGRES..." and sets it.
    *   Returns the pool.
3.  **Setup/Shutdown:** Create an `async setup()` method (to connect everything) and an `async shutdown()` method (to close all connections).
4.  **Integration:** Create a function `get_db(global_deps: GlobalDependencies = Depends(get_global_deps))` that retrieves the pool.

## Starter Code
```python
import asyncio
from typing import Optional

# --- 1. The Global Manager (YOUR JOB) ---
class GlobalDependencies:
    _instance: Optional['GlobalDependencies'] = None

    def __new__(cls):
        # TODO: Implement Singleton pattern (return existing instance if it exists)
        pass

    def __init__(self):
        # Prevent re-initialization if it's already set up
        if not hasattr(self, 'initialized'):
            self.db_pool = None
            self.redis_pool = None
            self.initialized = True

    async def get_db(self):
        # TODO: Lazy initialization of DB pool
        pass

    async def shutdown(self):
        # TODO: Print "CLOSING CONNECTIONS..." and reset pools
        pass

# --- 2. The Dependency Shortcut (FastAPI style) ---
# In real life, we wrap the global instance in a function for FastAPI's 'Depends'
_global_deps = GlobalDependencies()

async def get_database():
    return await _global_deps.get_db()

# --- 3. The API Logic (The Consumer) ---
async def create_user_route(db=None):
    # This simulates a FastAPI route that 'Depends' on the DB
    print(f"  [ROUTE] Using DB connection: {db}")

# --- 4. Execution ---
async def main():
    print("--- First Request ---")
    db1 = await get_database()
    await create_user_route(db1)

    print("
--- Second Request ---")
    db2 = await get_database()
    await create_user_route(db2) # Should NOT reconnect!

    print("
--- Shutting Down ---")
    await _global_deps.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```
