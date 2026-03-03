# Solution: SDK RPC Ingress Validation

## What to implement

In `BaseACPServer._handle_jsonrpc(...)`, isolate parameter model validation:

```python
from pydantic import ValidationError

...
params_model = PARAMS_MODEL_BY_METHOD[method]
params_data = dict(rpc_request.params) if rpc_request.params else {}
if custom_headers:
    params_data["request"] = {"headers": custom_headers}

try:
    params = params_model.model_validate(params_data)
except ValidationError as e:
    return JSONRPCResponse(
        id=rpc_request.id,
        error=JSONRPCError(code=-32602, message=f"Invalid params: {e.errors()}"),
    )
```

Keep everything else as-is:
- invalid method enum -> `-32601`
- missing registered handler -> `-32601`
- unexpected exception -> `-32603`

## Test patterns

In `test_base_acp_server.py`, add tests like:

1. `test_jsonrpc_invalid_params_returns_32602`
- register a valid method handler
- send payload with wrong params shape
- assert `error.code == -32602`

2. `test_jsonrpc_valid_method_missing_handler_returns_32601`
- do not register handler
- send valid method
- assert `error.code == -32601`

3. `test_jsonrpc_invalid_method_returns_32601`
- send non-existent method
- assert `error.code == -32601`

## Why this is protocol validation
This is the first place where method-specific ACP request contracts are enforced (`PARAMS_MODEL_BY_METHOD` + Pydantic model validation).  
If this layer fails open, agents receive malformed protocol inputs.
