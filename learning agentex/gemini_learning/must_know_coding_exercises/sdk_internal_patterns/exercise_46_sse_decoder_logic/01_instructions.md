# Exercise 46: The SSE Decoder (Parsing the Stream)

The most complex part of `scale-agentex-python/src/agentex/_streaming.py` is the `SSEDecoder`. 
It has to take raw chunks of bytes (which might be cut off mid-line!) and turn them into valid JSON events.

## The Challenge
Implement a `SimpleSSEDecoder`.
1. `decode_chunk(chunk_bytes)`:
   - Takes a chunk like `b"data: {"t":1}

data: {"t":2}"`.
   - Splts by `

`.
   - Removes the `data: ` prefix.
   - Parses the JSON.
   - Yields the dictionaries.

## Starter Code
```python
import json

class SimpleSSEDecoder:
    def __init__(self):
        self.buffer = b""

    def decode_chunk(self, chunk: bytes):
        """
        TODO:
        1. Add chunk to self.buffer.
        2. Split self.buffer by b"

".
        3. The last part might be incomplete - keep it in self.buffer.
        4. For all complete parts:
           - Remove b"data: " prefix.
           - json.loads().
           - Yield.
        """
        pass

# --- Simulation ---
decoder = SimpleSSEDecoder()

# Chunk 1: Ends with a full event
c1 = b"data: {"msg": "Hello"}

"
print(f"Chunk 1 yield: {list(decoder.decode_chunk(c1))}")

# Chunk 2: CUT OFF! (Incomplete)
c2 = b"data: {"msg": "Incompl"
print(f"Chunk 2 yield (Should be empty): {list(decoder.decode_chunk(c2))}")

# Chunk 3: The rest of the data
c3 = b"ete"}

"
print(f"Chunk 3 yield: {list(decoder.decode_chunk(c3))}")
```
