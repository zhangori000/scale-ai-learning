# Exercise 3: Streaming Contract Fault Injection (End-to-End)

## Difficulty
Very High

## Why this exercise exists
Streaming is the highest-risk protocol surface:
- multi-chunk NDJSON
- discriminated unions
- response id matching
- stateful delta accumulation

A single malformed chunk can corrupt conversation persistence if not validated correctly.

## Target files
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/base/base_acp_server.py`
- `scale-agentex/agentex/src/domain/services/agent_acp_service.py`
- `scale-agentex/agentex/src/domain/use_cases/agents_acp_use_case.py`
- `scale-agentex/agentex/tests/unit/services/test_agent_acp_service.py`
- `scale-agentex/agentex/tests/unit/use_cases/test_agents_acp_use_case.py`

## Your task
Design and implement fault-injection tests for streaming protocol violations.

### Fault cases to cover
1. **Invalid stream chunk shape from agent handler**
   - SDK should reject non-`TaskMessageUpdate` chunk via `TypeAdapter`.
2. **Mismatched JSON-RPC response id in stream**
   - Backend `AgentACPService._call_jsonrpc_stream` should fail hard.
3. **Unknown or invalid stream update type**
   - Backend `_parse_task_message_update(...)` should raise clear error.
4. **Delta type inconsistency within a single message index**
   - `DeltaAccumulator.add_delta(...)` should raise `ClientError`.

## Hints
- Validation chain:
  - SDK chunk validation: `task_message_update_adapter.validate_python(...)`
  - Backend stream response validation: `JSONRPCResponse.model_validate(...)`
  - Update union parsing: `_parse_task_message_update(...)`
  - Aggregation integrity: `DeltaAccumulator.add_delta(...)`

## Expected deliverables
1. New unit tests in service/use-case test files for all 4 fault classes.
2. Optional hardening improvements:
   - include chunk index in error logs
   - include offending `type` value in exceptions

## Success criteria
- Each fault is detected at the correct layer.
- Failures are explicit and reproducible.
- No silent partial-success on malformed streams.
