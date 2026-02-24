# Solution: Build a JSON-RPC Dispatcher

In `scale-agentex`, the system uses `src/api/schemas/agents_rpc.py` to define a `Discriminator`.

Here is the robust, production-grade way to handle JSON-RPC requests using Pydantic.

```python
from typing import Literal, Union, Any, Annotated
from pydantic import BaseModel, Field

# --- 1. Define Parameter Models ---
class CreateTaskParams(BaseModel):
    name: str
    priority: str

class SendMessageParams(BaseModel):
    content: str
    task_id: str

# --- 2. Define the Request Envelope ---
# Using Literal and Union is the most "Pydantic" way.
# But for simplicity, we can also parse the method string directly.
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
    try:
        # Step 1: Validate the outer envelope
        request = RPCRequest(**raw_request)
        
        # Step 2: Route based on method
        match request.method:
            case "task/create":
                # Step 3: Validate the specific params
                params = CreateTaskParams(**request.params)
                # Step 4: Call handler
                return handle_create_task(params)
                
            case "message/send":
                params = SendMessageParams(**request.params)
                return handle_send_message(params)
                
            case _:
                return f"Error: Unknown method '{request.method}'"
                
    except ValueError as e:
        return f"Error: Invalid Request - {e}"

# --- 5. Test Cases ---
req1 = {"method": "task/create", "params": {"name": "Audit", "priority": "high"}}
print(dispatch(req1)) 
# Output: "Task 'Audit' created with priority high"

req2 = {"method": "message/send", "params": {"content": "Hello", "task_id": "123"}}
print(dispatch(req2)) 
# Output: "Message: 'Hello' sent to task 123"

# --- Error Handling ---
req_bad = {"method": "task/create", "params": {"missing_priority": "oops"}}
print(dispatch(req_bad)) 
# Output: Error: Invalid Request...
```

### Why this matters for Scale-Agentex?
In `src/api/routes/agents.py`, you will see code exactly like this inside the `handle_rpc_request` function. The platform receives a generic JSON blob, inspects the `method` string, and then converts the `params` dictionary into a strict Python object (`CreateTaskParams`) before passing it to the logic layer. This ensures type safety even with dynamic JSON.
