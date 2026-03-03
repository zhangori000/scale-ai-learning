# Exercise 2: Backend ACP-Type Method Gating

## Difficulty
High

## Why this exercise exists
Even with valid JSON-RPC envelopes, the wrong RPC method for an agent type must be blocked.  
Example: `event/send` should not run against a `sync` agent.

## Target files
- `scale-agentex/agentex/src/domain/entities/agents_rpc.py`
- `scale-agentex/agentex/src/domain/use_cases/agents_acp_use_case.py`
- `scale-agentex/agentex/tests/unit/use_cases/test_agents_acp_use_case.py`

## Your task
Create comprehensive tests for ACP-type method gating and tighten behavior if needed.

### Requirements
1. Verify allowed method matrix:
   - `sync`: `task/create`, `message/send`
   - `async` + `agentic`: `task/create`, `task/cancel`, `event/send`
2. Verify blocked combinations raise `ClientError` with clear message.
3. Ensure `handle_rpc_request(...)` enforces gating before method execution.

## Hints
- Gating map is `ACP_TYPE_TO_ALLOWED_RPC_METHODS`.
- Gate function is `_validate_rpc_method_for_acp_type(...)`.
- `handle_rpc_request(...)` should call gate before dispatch.

## Expected deliverables
1. Table-driven unit tests covering allowed and disallowed pairs.
2. One test proving a disallowed method never reaches `_handle_*` execution path.

## Success criteria
- Matrix is fully covered by tests.
- Regression-proof behavior for legacy `agentic` alias remains explicit.
