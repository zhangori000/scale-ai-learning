# Lesson 01: What is FastAPI? (Origins & Performance)

### What is it?
FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints.

### Who made it?
It was created by **Sebastián Ramírez** (known online as [@tiangolo](https://github.com/tiangolo)) in 2018. He was frustrated with existing frameworks (like Flask and Django) because they didn't have great support for modern Python features like **type hints** and **async/await**.

### How fast is it?
FastAPI is one of the fastest Python frameworks available. It's built on top of two heavy hitters:
1.  **Starlette:** For the web parts (routing, requests, responses).
2.  **Pydantic:** For the data parts (validation, serialization).

**Is it as fast as C++ or Rust?**
*   **No.** C++ and Rust are "system-level" languages. They are compiled to machine code and don't have the overhead of a Python interpreter.
*   **But...** FastAPI is often fast *enough*. For most web APIs, the bottleneck isn't the CPU (the language speed); it's the **I/O** (waiting for a database or a network call like OpenAI).
*   In the Python world, FastAPI is in the same league as Go and NodeJS for many web tasks because it handles many connections at once without blocking.

---

# Lesson 02: Pydantic & Routers (The Skeleton)

### What is a Router?
Imagine your app has 100 endpoints. If you put them all in one file, it’s a nightmare. `APIRouter` lets you split them into logical files (e.g., `users.py`, `items.py`, `agents.py`).

### What is Pydantic?
Pydantic is how you define **exactly** what your data should look like.

```python
from fastapi import APIRouter
from pydantic import BaseModel, Field

# 1. Define your "Data Contract" (Schema)
class User(BaseModel):
    id: int
    username: str = Field(..., min_length=3)
    is_active: bool = True

# 2. Create a Router
router = APIRouter(prefix="/users", tags=["users"])

# 3. Use the schema in a route
@router.post("/")
async def create_user(user: User):
    # FastAPI automatically checks if 'user' matches the schema!
    return {"message": f"User {user.username} created"}
```

---

# Lesson 03: Dependency Injection (The "I Need This" Pattern)

### What is it?
"Dependency Injection" sounds scary, but it just means: **"I tell the framework what I need, and it gives it to me."**

Instead of a function creating its own database connection, it asks for one.

**Why?**
1.  **Testing:** You can easily swap a real database for a fake one during tests.
2.  **Clean Code:** Your functions stay focused on their job, not on setting up infrastructure.

```python
from fastapi import Depends

def get_db():
    db = "Real Database Connection"
    try:
        yield db
    finally:
        print("Closing connection...")

@router.get("/profile")
async def get_profile(db: str = Depends(get_db)):
    # I didn't create 'db', FastAPI 'injected' it for me!
    return {"db_used": db}
```
