# Protocol Contract Validation Lab (Agentex)

This module answers one concrete question:

Where does Agentex validate that agents are speaking ACP correctly?

## Validation map (actual code)

### 1) SDK-side ACP server ingress checks
- File: `scale-agentex-python/src/agentex/lib/sdk/fastacp/base/base_acp_server.py`
- Key checks:
  - Parse JSON-RPC envelope: `JSONRPCRequest(**data)`
  - Validate RPC method enum: `RPCMethod(rpc_request.method)`
  - Validate method has a registered handler: `self._handlers[...]`
  - Validate params against method-specific model:
    - `PARAMS_MODEL_BY_METHOD[...]`
    - `params_model.model_validate(params_data)`
  - Validate streaming chunks are valid `TaskMessageUpdate` union:
    - `task_message_update_adapter.validate_python(chunk)`

### 2) Backend ACP gateway + response contract checks
- File: `scale-agentex/agentex/src/domain/services/agent_acp_service.py`
- Key checks:
  - Validate downstream JSON-RPC response structure:
    - `JSONRPCResponse.model_validate(response)`
  - Validate response id matches request id
  - Validate returned message/update shape:
    - `_parse_task_message(...)`
    - `_parse_task_message_update(...)`

### 3) Backend method gate by agent ACP type
- File: `scale-agentex/agentex/src/domain/use_cases/agents_acp_use_case.py`
- Key checks:
  - `ACP_TYPE_TO_ALLOWED_RPC_METHODS` map (from `entities/agents_rpc.py`)
  - `_validate_rpc_method_for_acp_type(...)`
  - Called from `handle_rpc_request(...)` before dispatch

## Exercise order
1. `exercise1_sdk_rpc_ingress_validation`
2. `exercise2_backend_acp_type_method_gating`
3. `exercise3_streaming_contract_fault_injection`

Do these in order. Each exercise assumes the previous one.
