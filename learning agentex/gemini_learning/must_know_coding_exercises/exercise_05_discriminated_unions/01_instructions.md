# Exercise: Discriminated Unions (The "Tagged Union" Pattern)

In `scale-agentex` (`src/api/schemas/task_messages.py`), messages can be many different things: a **text** message, a **tool call**, or raw **data**.

How does Pydantic know which one it is when it receives a JSON blob? It uses a **Discriminator** (a "tag").

## The Goal
Create a `TaskMessageContent` union that automatically parses into the correct class based on a `type` field.

## Requirements
1.  **TextContent Model:**
    *   `type`: Must be the literal string `"text"`.
    *   `text`: A string.
2.  **DataContent Model:**
    *   `type`: Must be the literal string `"data"`.
    *   `data`: A dictionary of any data.
3.  **Union:** Create a type `AnyContent` that is a `Union` of these two.
4.  **Envelope:** Create a `Message` model that has a `content: AnyContent` field and uses a **discriminator** on the `type` field.

## Starter Code
```python
from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field

# --- 1. Define the specific content types ---

class TextContent(BaseModel):
    # TODO: Add 'type' as Literal["text"] and 'text' as str
    pass

class DataContent(BaseModel):
    # TODO: Add 'type' as Literal["data"] and 'data' as dict
    pass

# --- 2. Create the "Tagged Union" ---
# This tells Pydantic: "Look at the 'type' field to decide which class to use"
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
print(f"Msg 1 type: {type(m1.content)}")

# Test B: Should parse as DataContent
msg_2 = {
    "id": "2",
    "content": {"type": "data", "data": {"status": "ok", "code": 200}}
}
m2 = Message(**msg_2)
print(f"Msg 2 type: {type(m2.content)}")

# Test C: Should FAIL (Unknown type)
msg_3 = {
    "id": "3",
    "content": {"type": "video", "url": "..."}
}
# TODO: Try-except this to see it fail!
```
