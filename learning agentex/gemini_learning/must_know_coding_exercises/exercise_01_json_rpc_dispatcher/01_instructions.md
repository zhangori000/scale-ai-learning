# Exercise: Build a JSON-RPC Dispatcher

In `scale-agentex`, the core communication between the Platform and the Agents happens via **JSON-RPC**.
(See `src/api/routes/agents.py` and `src/api/schemas/agents_rpc.py`).

The platform receives a request like:
```json
{
  "method": "task/create",
  "params": { "name": "Audit Contract", "priority": "high" }
}
```
It must figure out **which function to call** based on the "method" string.

## The Goal
Build a `dispatch_rpc` function that takes a raw dictionary and routes it to the correct handler.

## Requirements
1.  **Pydantic Models:**
    *   Create `CreateTaskParams` (name: str, priority: str).
    *   Create `SendMessageParams` (content: str, task_id: str).
    *   Create a `RPCRequest` model that can parse either request based on a "method" field. (Hint: Use `Literal` and `Union` or manual dispatch).
2.  **Handlers:**
    *   `handle_create_task(params: CreateTaskParams)` -> Returns "Task {name} created!"
    *   `handle_send_message(params: SendMessageParams)` -> Returns "Message sent to {task_id}"
3.  **Dispatcher:**
    *   `dispatch(request: dict)` -> Returns the result string.

## Starter Code
```python
from typing import Literal, Union, Any
from pydantic import BaseModel, Field

# --- 1. Define your Parameter Models ---
class CreateTaskParams(BaseModel):
    # TODO: Add fields
    pass

class SendMessageParams(BaseModel):
    # TODO: Add fields
    pass

# --- 2. Define the Request Envelope ---
# This is tricky! How do you know which params to use?
# Hint: You might parse the "method" first, then parse the "params".
class RPCRequest(BaseModel):
    method: str
    params: dict[str, Any]

# --- 3. Define Handlers ---
def handle_create_task(params: CreateTaskParams):
    return f"Task '{params.name}' created with priority {params.priority}"

def handle_send_message(params: SendMessageParams):
    return f"Message: '{params.content}' sent to task {params.task_id}"

# --- 4. The Dispatcher (YOUR JOB) ---
def dispatch(raw_request: dict) -> str:
    """
    1. Parse raw_request into RPCRequest.
    2. Check the 'method'.
    3. Parse 'params' into the specific Pydantic model (CreateTaskParams or SendMessageParams).
    4. Call the correct handler.
    """
    # TODO: Implement logic
    pass

# --- 5. Test Cases ---
req1 = {"method": "task/create", "params": {"name": "Audit", "priority": "high"}}
print(dispatch(req1)) 
# Expected: "Task 'Audit' created with priority high"

req2 = {"method": "message/send", "params": {"content": "Hello", "task_id": "123"}}
print(dispatch(req2)) 
# Expected: "Message: 'Hello' sent to task 123"
```
