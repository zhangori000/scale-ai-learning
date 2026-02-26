# Solution: The SSE Decoder (Parsing the Stream)

This exercise teaches you about **Stream Buffering**. Without this, your SDK would crash every time a network packet was slightly delayed.

## The Solution

```python
import json

class SimpleSSEDecoder:
    def __init__(self):
        self.buffer = b""

    def decode_chunk(self, chunk: bytes):
        # 1. Accumulate bytes
        self.buffer += chunk
        
        # 2. Split by the SSE delimiter
        parts = self.buffer.split(b"

")
        
        # 3. Handle the Incomplete Tail
        # The last element of 'parts' is either empty (if it ended with 

)
        # or it is an incomplete line. We save it back to the buffer.
        self.buffer = parts.pop() 
        
        for p in parts:
            line = p.decode("utf-8").strip()
            
            # 4. Strip the SSE prefix
            if line.startswith("data: "):
                json_str = line[6:] # Remove 'data: '
                try:
                    yield json.loads(json_str)
                except json.JSONDecodeError:
                    pass # Ignore partial/bad JSON
```

## Why this is Agentex-style:
1. **Network Fragmentation**: Real internet traffic arrives in unpredictable chunks. Your logic must be able to "wait" for the rest of a line.
2. **Standard Compliance**: The `SSEDecoder` in `_streaming.py` is much more complex (it handles `id:`, `retry:`, and `event:` fields), but the **Buffer-and-Split** logic is exactly the same.
3. **Efficiency**: By using `yield`, the SDK can start giving data to the user's `for` loop as soon as the first line is complete, even if the rest of the 50MB stream is still downloading.
