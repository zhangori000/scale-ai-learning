# Solution: Cursor-Based Pagination (The High-Scale Feed)

In `scale-agentex`, this logic is the foundation for `src/utils/pagination.py`. It's how the system maintains its "Chat Flow" even if thousands of users are chatting at the same time.

## The Implementation

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

# --- 2. The Pagination Utilities ---
def encode_cursor(item_id: int) -> str:
    """
    Encodes an integer ID into a base64 string to make it 'Opaque'.
    Opaque cursors mean the client doesn't need to understand the ID.
    """
    id_bytes = str(item_id).encode("utf-8")
    base64_bytes = base64.b64encode(id_bytes)
    return base64_bytes.decode("utf-8")

def decode_cursor(cursor: str) -> int:
    """
    Decodes a base64 string back into an integer ID.
    """
    base64_bytes = cursor.encode("utf-8")
    id_bytes = base64.b64decode(base64_bytes)
    return int(id_bytes.decode("utf-8"))

def get_page(data: List[Dict], cursor: Optional[str], limit: int) -> Tuple[List[Dict], Optional[str]]:
    """
    Returns (page_data, next_cursor)
    """
    # 1. Determine the starting point
    if cursor is None:
        # If no cursor, start at the very beginning (index 0)
        start_index = 0
    else:
        # If a cursor is provided, decode it and find the next item's index
        last_seen_id = decode_cursor(cursor)
        
        # We search for the index of the ID in the data
        # In a real DB, this is much faster (using 'WHERE id > X')
        last_seen_index = next((i for i, item in enumerate(data) if item["id"] == last_seen_id), -1)
        
        if last_seen_index == -1:
            # If the ID wasn't found, return empty (or start from beginning)
            return [], None
            
        start_index = last_seen_index + 1
        
    # 2. Slice the data to get the page
    page_data = data[start_index : start_index + limit]
    
    # 3. Generate the next_cursor from the LAST item in the page
    next_cursor = None
    if page_data:
        last_item_id = page_data[-1]["id"]
        next_cursor = encode_cursor(last_item_id)
        
    return page_data, next_cursor

# --- 3. The Execution ---
print("--- Initial Request (No Cursor) ---")
# User asks for first 3 items
page_1, cursor_1 = get_page(MOCK_DB, cursor=None, limit=3)
print(f"Page 1: {page_1}")
print(f"Next Cursor: {cursor_1}")

print("
--- Next Request (Using Cursor) ---")
# User passes back the cursor from the previous request
page_2, cursor_2 = get_page(MOCK_DB, cursor=cursor_1, limit=3)
print(f"Page 2: {page_2}")
print(f"Next Cursor: {cursor_2}")

print("
--- Last Request ---")
# User fetches the very last item
page_3, cursor_3 = get_page(MOCK_DB, cursor=cursor_2, limit=3)
print(f"Page 3: {page_3}")
print(f"Next Cursor: {cursor_3}") # Should be None or pointing to last item
```

### Key Takeaways from the Solution

1.  **Opaque Cursors:** By base64-encoding the ID, you are hiding your internal ID format from the user. This is an **industry-best practice**. It means if you decide to change your IDs from integers to UUIDs later, you don't have to break your API—you just change your `decode_cursor` logic.
2.  **No Duplicates:** Even if someone inserts a new message at the top of `MOCK_DB` while you are scrolling, your "Index" or "ID" logic ensures you only ever see messages that come *after* the one you already have.
3.  **Why we use it for Agents:** In `scale-agentex`, message history can be massive. By using Cursor Pagination, the UI stays fast and snappy even with a 50,000-message conversation, as it only ever loads small "windows" of data at a time.
