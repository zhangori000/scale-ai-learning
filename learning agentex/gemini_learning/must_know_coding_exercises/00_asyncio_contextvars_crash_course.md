# Asyncio & ContextVars: The "Agentex" Engine Room

In `scale-agentex`, almost everything is **Asynchronous**. If you want to understand how it handles thousands of events without crashing, you need to master these two concepts.

---

## 1. Asyncio Crash Course (The "Conductor")

### What is a Coroutine?
Think of a normal function (`def`) like a **contractor** who starts a job and won't leave until it's 100% done. You are stuck waiting for them.

A `coroutine` (`async def`) is like a **smart worker** who can start a job (like fetching data from a database), and while they wait for the "bricks to arrive," they say: *"I'm waiting now, you can go do something else!"*

*   **`async def`**: Defines a coroutine (it doesn't *run* the code, it just creates a "plan").
*   **`await`**: Actually executes the "plan" and pauses the function until the result is ready.

```python
import asyncio

async def fetch_data():
    print("  [Fetch] Starting...")
    await asyncio.sleep(1)  # Simulates waiting for a network (DOES NOT BLOCK)
    print("  [Fetch] Done!")
    return {"data": 123}

async def main():
    # Calling fetch_data() returns a COROUTINE object, it doesn't run it yet.
    coro = fetch_data() 
    print("Created coro, now awaiting it...")
    result = await coro # NOW it runs
    print(f"Result: {result}")

asyncio.run(main())
```

### Asyncio Locks (Preventing "Double-Writes")
In Agentex, multiple workers might try to update the same "Task Status" at the same time. This is a **Race Condition**.

`asyncio.Lock` ensures only **one** coroutine can enter a specific block of code at a time.

```python
lock = asyncio.Lock()

async def update_task_status(task_id):
    async with lock:  # Only one worker enters here at a time
        print(f"Updating task {task_id}...")
        await asyncio.sleep(0.1) # Simulate DB write
        print(f"Task {task_id} updated.")
```

### Other Essential Asyncio Ops
*   **`asyncio.gather(*coros)`**: Runs multiple coroutines **at the same time** (in parallel) and waits for all of them to finish.
*   **`asyncio.create_task(coro)`**: Starts a coroutine in the "background" immediately without waiting for it to finish right now.

---

## 2. ContextVars (The "Request Passport")

### The Problem: Global Variables are Dangerous
If you use a global variable `current_user_id = 123`, and then another request comes in for User 456, User 123 might accidentally see User 456's data!

### The Solution: ContextVars
`contextvars` are like "Local Globals." They are isolated to the **current execution context** (the current async task).

Imagine a waiter (an async task) carrying a tray (the context). Anything on that tray is only for the table they are serving.

```python
import contextvars
import asyncio

# 1. Define the variable
request_id_ctx = contextvars.ContextVar("request_id", default="none")

async def log_with_id(message):
    # 2. Access the variable
    req_id = request_id_ctx.get()
    print(f"[{req_id}] {message}")

async def handle_request(req_id):
    # 3. Set the variable for THIS specific task
    request_id_ctx.set(req_id)
    await asyncio.sleep(1)
    await log_with_id("Processing request...")

async def main():
    # Run two requests "simultaneously"
    # Even though they run at the same time, their ContextVars are ISOLATED!
    await asyncio.gather(
        handle_request("ABC-123"),
        handle_request("XYZ-789")
    )

asyncio.run(main())
```

### Why does Agentex use this?
In the `scale-agentex` repo, you'll see `ContextVars` used for:
1.  **Tracing**: Carrying a `trace_id` through 10 different function calls without passing it as an argument every time.
2.  **Auth**: Storing the `current_user` after a middleware validates the token.
3.  **Tenant Isolation**: Ensuring code only operates on the correct customer's database.

---

## Summary for Exercise 27
When you see `trace_id_ctx.set(new_id)` in Exercise 27, think: *"I am putting a Trace ID on the current task's 'tray'. Any code called by this task can look at the tray to see the ID."*
