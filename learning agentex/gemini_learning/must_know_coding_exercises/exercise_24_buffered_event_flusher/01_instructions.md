# Exercise: The Buffered Event Flusher (Data Engineering)

In `scale-agentex` (`src/domain/use_cases/agents_acp_use_case.py`), the platform receives hundreds of "text deltas" per second. If we saved every single letter to the database, the database would crash.

Instead, the platform **aggregates** (buffers) the text in memory and only "Flushes" it to the database when a specific condition is met.

## The Goal
Create an `EventFlusher` that buffers strings and "Flushes" them (prints them) only when:
1.  The buffer reaches a certain **Size** (e.g., 10 characters).
2.  An explicit **Flush Signal** is received (e.g., "DONE").

## Requirements
1.  **The Flusher:** Create a class `EventFlusher` with `self.buffer = ""` and `self.max_size = 10`.
2.  **Add Method:** `add_fragment(text: str)`:
    *   Appends text to the buffer.
    *   If `len(self.buffer) >= self.max_size`, call `self.flush()`.
3.  **Flush Method:** `flush()`:
    *   If the buffer is NOT empty, print "[FLUSH] Saving to DB: {self.buffer}".
    *   Clear the buffer.
4.  **The Test:** Send a sequence of fragments and show how the flushing happens in batches.

## Starter Code
```python
from typing import List

class EventFlusher:
    def __init__(self, max_size: int = 10):
        self.buffer = ""
        self.max_size = max_size
        self.flush_count = 0

    def add_fragment(self, text: str):
        """
        TODO: 
        1. Append text to buffer.
        2. If buffer exceeds max_size, call flush().
        """
        pass

    def flush(self):
        """
        TODO: 
        1. If buffer has content, print it and clear it.
        2. Increment flush_count.
        """
        pass

# --- 3. Execution ---
flusher = EventFlusher(max_size=10)

print("--- Sending fragments ---")
# "Hello" (5 chars) -> Buffer: "Hello"
flusher.add_fragment("Hello") 

# " World" (6 chars) -> Total 11 -> Should Trigger Flush!
flusher.add_fragment(" World") 

# "!" (1 char) -> Buffer: "!"
flusher.add_fragment("!")

print("
--- Explicit Flush (End of stream) ---")
flusher.flush()

print(f"
Total Database Writes: {flusher.flush_count}")
# Expected flush_count: 2 (One automatic, one explicit)
```
