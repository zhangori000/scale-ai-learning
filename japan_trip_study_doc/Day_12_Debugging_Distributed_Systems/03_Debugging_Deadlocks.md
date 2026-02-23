# Day 12 - System/Debug: Deadlocks and Concurrency Issues

How do you find a bug that only happens "Once in a Blue Moon"? This is a **Concurrency Debugging** lesson.

## 1. The Scenario
Scale AI's Billing Service occasionally "Freezes." The CPU is at 0%, but no requests are being processed. This happens once every 2 days.

**The Complexity:** 
- **The Code:** The Python code is using `asyncio.Lock()` to protect a shared resource (e.g., the User's Balance).
- **The Deployment:** 100 workers are running.

---

## 2. The Solution: Deadlock Identification
This is a **Deadlock**. Two threads are waiting for each other.
- Thread A has Lock #1 and wants Lock #2.
- Thread B has Lock #2 and wants Lock #1.
**Result:** Both wait forever. The system "Freezes."

### The "Scale AI" Deadlock Strategy:
1.  **Avoid Shared State:** The best fix for deadlocks is to **Remove Locks**. Use atomic database updates (Day 04 lesson!) instead of Python locks.
2.  **Lock Ordering:** If you MUST use locks, always acquire them in the **Same Order** (e.g. Always Lock User #1, then User #2. Never the reverse).
3.  **Timeouts:** Never wait for a lock forever. `await lock.acquire(timeout=5)`.

### How to debug this in Production:
- **`py-spy`**: This is a tool that can "Attach" to a running Python process and show you the **Stack Trace**. If you see 100 threads all stuck on `await lock.acquire()`, you've found the deadlock.
- **`asyncio.all_tasks()`**: In a running FastAPI app, you can add a "Debug" endpoint that returns a list of all active tasks and what they are waiting for.

---

## 3. 🧠 Key Teaching Points:
*   **The "Lock Contention" Slowdown**: Even if you don't have a deadlock, too many locks make your system slow. If 1,000 threads are waiting for one "Balance Lock," only 1 thread can work at a time. This is **Serialization**.
*   **The "Context Manager" Rule**: Always use `async with lock:`. Never use `lock.acquire()` and `lock.release()` manually. If your code crashes between the two, you'll have a **Leaked Lock** (another type of deadlock!).
*   **Atomic DB vs. In-Memory Lock**: At Scale, we almost NEVER use Python locks. We use **Database Transactions**. Why? Because a Python lock only works for *one* server. A database transaction works for *all* 1,000 servers.
*   **FDE Tip**: When an interviewer says "The system is frozen but the CPU is low," your first response should be: "I would check for a **Deadlock** or **Starvation** by looking at the thread stacks."
*   **Scale's Best Practice**: For 99% of "Concurrency" problems, the answer is: "Let the Database handle it with an **Atomic Update**."
*   **The "Starvation" Lesson**: If a "Large" task always gets a lock and "Small" tasks never do, the small tasks are "Starved." This is why we use "Fair Locks" or "Priority Queues."
