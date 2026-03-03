# Exercise 1: SDK RPC Ingress Validation

## Difficulty
High

## Why this exercise exists
If this layer is weak, every downstream ACP handler can receive malformed input.  
This is the first protocol gate.

## Target files
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/base/base_acp_server.py`
- `scale-agentex-python/src/agentex/lib/types/acp.py`
- `scale-agentex-python/src/agentex/lib/types/json_rpc.py`
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/tests/test_base_acp_server.py`

## Your task
Implement and verify strict ingress behavior for JSON-RPC requests in `BaseACPServer`.

### Requirements
1. Invalid `method` must return JSON-RPC `-32601` with the original request id.
2. Valid method but invalid `params` shape must return JSON-RPC `-32602` (invalid params), not generic internal error.
3. Requests for methods without a registered handler must return `-32601`.
4. Add tests that prove each case.

## Hints
- `PARAMS_MODEL_BY_METHOD` in `acp.py` is the protocol contract map.
- Wrap only `params_model.model_validate(...)` with a `ValidationError` branch so you can map to `-32602`.
- Keep existing behavior for unexpected exceptions (`-32603`).

## Expected deliverables
1. Code changes in `base_acp_server.py`.
2. At least 3 tests in `test_base_acp_server.py`:
   - invalid method
   - invalid params for a valid method
   - missing handler for valid method

## Success criteria
- Tests pass.
- Error codes are deterministic and protocol-correct (`-32601`, `-32602`, `-32603`).
