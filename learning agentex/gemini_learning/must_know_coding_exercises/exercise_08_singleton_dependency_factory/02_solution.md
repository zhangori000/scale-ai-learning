# Solution: The Singleton Dependency Factory

This pattern is a foundational piece of `scale-agentex` architecture, located in `src/config/dependencies.py`. It's how the platform manages the complexity of having Postgres, Redis, and Temporal all running at once.

## The Implementation

```python
import asyncio
from typing import Optional, Any

# --- 1. The Global Manager (Singleton Factory) ---
class GlobalDependencies:
    """
    Manages the lifecycle of high-cost resources (Postgres, Redis, Temporal).
    """
    _instance: Optional['GlobalDependencies'] = None

    def __new__(cls):
        # Implementation of the Singleton pattern
        # This ensures there is only EVER one copy of this class in memory!
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # We only want to set up fields once
        if not hasattr(self, 'initialized'):
            self.db_pool: Optional[str] = None
            self.redis_pool: Optional[str] = None
            self.initialized = True
            print("[GLOBAL] Manager initialized.")

    async def get_db_pool(self) -> str:
        """
        Lazy Initialization: The 'Brain' only connects when someone actually asks for it.
        """
        if self.db_pool is None:
            print("  [INFRA] CONNECTING TO POSTGRES (this is expensive!)...")
            # Simulate network delay...
            await asyncio.sleep(0.5)
            self.db_pool = "postgresql://localhost:5432/agentex_db"
            print("  [INFRA] Postgres Connected.")
        
        return self.db_pool

    async def shutdown(self):
        """
        Clean up resources when the app stops.
        """
        if self.db_pool or self.redis_pool:
            print("
[GLOBAL] SHUTTING DOWN...")
            print(f"  [INFRA] Disposing DB Pool: {self.db_pool}")
            self.db_pool = None
            self.redis_pool = None
            print("[GLOBAL] Connections closed.")

# --- 2. The Dependency Shortcut (FastAPI style) ---
# This is what we would use with FastAPI's Depends()
_global_deps = GlobalDependencies()

async def get_database():
    """
    This function is the 'Injectable' dependency.
    """
    return await _global_deps.get_db_pool()

# --- 3. The API Logic (The Consumer) ---
async def create_user_route(db_connection: str):
    # This represents a route handler in FastAPI
    print(f"  [ROUTE] Executing logic using {db_connection}")

# --- 4. Execution ---
async def main():
    print("--- First Request ---")
    # 1. First request needs the DB, so it will connect
    db1 = await get_database()
    await create_user_route(db1)

    print("
--- Second Request ---")
    # 2. Second request also needs the DB, but it should reuse the existing pool!
    db2 = await get_database()
    await create_user_route(db2)

    # Simple check: the strings are the same and it didn't print 'CONNECTING' twice.
    assert db1 == db2

    print("
--- Final Shutdown ---")
    await _global_deps.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Takeaways

1.  **Lazy Initialization:** This is crucial for **fast startup times**. If you have 50 agents, you don't want the platform to connect to every single one of them at the exact same millisecond when the app starts. It only connects when a task is actually created for that agent.
2.  **Singleton Pattern:** By using `__new__`, we guarantee that every part of the application is sharing the exact same database engine. This prevents "Too Many Connections" errors in Postgres.
3.  **Encapsulation:** All the messy environment variables, connection strings, and pool settings are hidden inside `GlobalDependencies`. The rest of your app only sees a clean `get_database()` function.
4.  **Shutdown Logic:** In `scale-agentex` (`src/config/dependencies.py`), we use `dispose()` on the SQLAlchemy engine to ensure that all database connections are gracefully returned to the server, preventing zombie processes.
