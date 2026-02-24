# Solution: Discriminated Unions (The Tagged Union Pattern)

In `scale-agentex`, this pattern is essential for handling complex agent behaviors like "Thinking" vs. "Acting" vs. "Answering."

## The Implementation

```python
from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field, ValidationError

# --- 1. Define the specific content types ---

class TextContent(BaseModel):
    type: Literal["text"] # This is the "Tag"
    text: str

class DataContent(BaseModel):
    type: Literal["data"] # This is the "Tag"
    data: dict[str, Any]

# --- 2. Create the "Tagged Union" ---
# This is a 'best practice' found in the Scale-Agentex codebase.
# It makes route signatures very clean and readable.
AnyContent = Annotated[
    Union[TextContent, DataContent], 
    Field(discriminator="type")
]

class Message(BaseModel):
    id: str
    content: AnyContent

# --- 3. Test Cases ---

# Test A: Should parse as TextContent
msg_1 = {
    "id": "1",
    "content": {"type": "text", "text": "Hello world!"}
}
m1 = Message(**msg_1)
print(f"Msg 1 type: {type(m1.content).__name__}")
# Output: Msg 1 type: TextContent

# Test B: Should parse as DataContent
msg_2 = {
    "id": "2",
    "content": {"type": "data", "data": {"status": "ok", "code": 200}}
}
m2 = Message(**msg_2)
print(f"Msg 2 type: {type(m2.content).__name__}")
# Output: Msg 2 type: DataContent

# Test C: Should FAIL (Unknown type)
msg_3 = {
    "id": "3",
    "content": {"type": "video", "url": "..."}
}
try:
    m3 = Message(**msg_3)
except ValidationError as e:
    print("
--- Error Caught ---")
    print(f"Unknown message type 'video' failed as expected.")
    # In a real app, this would return a 400 Bad Request to the client!
```

### Key Takeaways

1.  **Safety First:** By using `Literal["text"]`, you are making the `type` field a **constant**. It must be exactly that string.
2.  **Automatic Dispatch:** Pydantic's `discriminator` is incredibly fast. It doesn't guess; it looks exactly at the tag you specified and picks the correct class.
3.  **Why we use it for Agents:** Agents often send back messy, mixed data. By using Tagged Unions, the Platform can safely process a list of 10 different message types and always know how to treat each one.
