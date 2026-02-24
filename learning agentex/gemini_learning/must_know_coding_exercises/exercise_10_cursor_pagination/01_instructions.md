# Exercise: Cursor-Based Pagination (The High-Scale Feed)

In `scale-agentex`, when you scroll through 1,000 messages, the UI doesn't say "Give me Page 2." It says **"Give me the next 10 messages after the message I just saw."**

## The Problem (Why Offset is Bad)
Imagine a list of messages `[A, B, C, D, E]`.
1.  User reads Page 1 (`A, B`).
2.  A NEW message `F` arrives: `[F, A, B, C, D, E]`.
3.  User requests Page 2 (items 3 and 4).
4.  The server returns `B, C`.
5.  **OH NO!** The user saw `B` on Page 1 AND Page 2.

## The Goal
Build a `PaginationEngine` that uses a `cursor` (a base64 string containing the last seen ID) to fetch the next page.

## Requirements
1.  **Cursor Encoding:** Create a function `encode_cursor(id: int)` that returns a base64 string.
2.  **Cursor Decoding:** Create a function `decode_cursor(cursor: str)` that returns the ID as an integer.
3.  **The Fetcher:** Create `get_page(data: list, cursor: str | None, limit: int)` that:
    *   If no cursor, returns the first `limit` items.
    *   If cursor provided, decodes it, finds its index in the list, and returns the *next* `limit` items.
    *   Returns the data AND the `next_cursor` (the ID of the last item in the page).

## Starter Code
```python
import base64
from typing import List, Dict, Optional, Tuple

# --- 1. The Raw Data (The Database) ---
MOCK_DB = [
    {"id": 100, "text": "Hello"},
    {"id": 101, "text": "How are you?"},
    {"id": 102, "text": "I am an agent."},
    {"id": 103, "text": "I can help with legal docs."},
    {"id": 104, "text": "Just send the URL."},
    {"id": 105, "text": "Analyzing..."},
    {"id": 106, "text": "Complete!"},
]

# --- 2. The Pagination Utilities (YOUR JOB) ---
def encode_cursor(item_id: int) -> str:
    """Encodes an integer ID into a base64 string"""
    pass

def decode_cursor(cursor: str) -> int:
    """Decodes a base64 string back into an integer ID"""
    pass

def get_page(data: List[Dict], cursor: Optional[str], limit: int) -> Tuple[List[Dict], Optional[str]]:
    """
    Returns (page_data, next_cursor)
    """
    # TODO: 
    # 1. If cursor is None, start from the beginning.
    # 2. If cursor exists, decode it to find the last seen ID.
    # 3. Find the index of that ID in 'data'.
    # 4. Slice the list to get 'limit' items starting after that index.
    # 5. Create the next_cursor from the last item in the page.
    pass

# --- 3. The Execution ---
print("--- Initial Request (No Cursor) ---")
page_1, cursor_1 = get_page(MOCK_DB, cursor=None, limit=3)
print(f"Page 1: {page_1}")
print(f"Next Cursor: {cursor_1}")

print("
--- Next Request (Using Cursor) ---")
page_2, cursor_2 = get_page(MOCK_DB, cursor=cursor_1, limit=3)
print(f"Page 2: {page_2}")
print(f"Next Cursor: {cursor_2}")
```
