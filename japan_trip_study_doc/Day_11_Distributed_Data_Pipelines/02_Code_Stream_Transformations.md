# Day 11 - Code: Stream Transformation and Filtering (Pydantic + Python)

How do you handle 1,000,000 JSONs per hour without crashing? This is a **Data Transformation** lesson.

## 1. The Scenario
Scale AI's Kafka topic `images_raw` has a 1MB JSON for every image. We want to extract only the `image_id` and the `width` and `height`.

**The Problem:** If you just use `json.loads(msg)`, your Python worker will use 1GB of RAM for every 1,000 messages. This is a **Memory Leak** risk.

---

## 2. The Solution: Pydantic "Generators" and Memory Buffers
We don't want to load 1,000 messages into a list. We want to **process them one-by-one**.

### The "Scale AI" Memory-Efficient Transformer:
```python
from pydantic import BaseModel
from typing import Iterator
import json

class RawImageMetadata(BaseModel):
    image_id: str
    width: int
    height: int
    camera_model: str
    # (other 100 fields we don't care about)

def process_stream(raw_messages: Iterator[str]) -> Iterator[dict]:
    """
    1. GENERATOR: Yields one result at a time.
    2. VALIDATION: Pydantic only extracts the fields we need.
    3. EFFICIENCY: Python memory is reused for each 'msg'.
    """
    for msg in raw_messages:
        try:
            # Pydantic is much faster than raw json.loads + manual checks
            data = RawImageMetadata.model_validate_json(msg)
            
            # We transform 'width' and 'height' into a 'dimensions' dict
            yield {
                "id": data.image_id,
                "dims": f"{data.width}x{data.height}"
            }
        except Exception:
            # Skip bad records (Fault Isolation - Day 02!)
            continue

# --- USE CASE ---
# Instead of: results = list(process_stream(kafka_iterator))
# Use: for result in process_stream(kafka_iterator):
#          push_to_next_topic(result)
```

---

## 3. 🧠 Key Teaching Points:
*   **The Iterator/Generator**: In Python, `yield` creates an "Iterator." It's like a "Lazy List." It doesn't use memory until you "Ask" for the next item. This is how Scale processes **Petabytes** of data.
*   **`model_validate_json`**: Pydantic's built-in JSON parser is written in **Rust**! It's 10x faster than the standard `json.loads`. At Scale, every microsecond counts.
*   **Schema Evolution**: If the customer adds a new `f_stop` field to the JSON, our code *doesn't break* because Pydantic only extracts the fields we defined. This is **Schema-on-Read**.
*   **FDE Tip**: When an interviewer says "The worker is OOMing (Out of Memory)," your first check is the **List Collection**. If you're doing `results.append(data)` in a loop, you're building a "Memory Bomb." Use `yield` instead.
*   **Scale's Best Practice**: For 1 million images, NEVER load more than 100 into memory at a time. Process them in "Batches" of 100.
