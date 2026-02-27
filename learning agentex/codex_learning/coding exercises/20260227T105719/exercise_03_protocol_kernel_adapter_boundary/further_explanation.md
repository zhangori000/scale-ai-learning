# Further Explanation: Evidence from Agentex + Agentex-Python

## Evidence for Layer 1 (Contract Kernel)
1. `scale-agentex/agentex/src/domain/entities/agents_rpc.py`
   - canonical RPC methods and request models.
2. `scale-agentex-python/src/agentex/lib/types/acp.py`
   - SDK-side ACP contract mirror.
3. `scale-agentex/agentex/src/domain/entities/task_message_updates.py`
   - typed stream update protocol (`start/delta/full/done` + delta variants).
4. `scale-agentex-python/src/agentex/lib/sdk/fastacp/base/base_acp_server.py`
   - NDJSON JSON-RPC streaming boundary and strict message typing.

## Evidence for Layer 2 (Port/Adapter Substrate)
1. `scale-agentex/agentex/src/adapters/streams/port.py` + `adapter_redis.py`
2. `scale-agentex/agentex/src/adapters/temporal/port.py`
3. `scale-agentex-python/src/agentex/lib/core/adapters/streams/port.py` + `adapter_redis.py`
4. `scale-agentex/agentex/src/config/dependencies.py`
   - concrete infra wiring (Temporal, Redis, DB engines, Mongo, HTTP client).

## Evidence for Layer 3 (Orchestration)
1. `scale-agentex/agentex/src/domain/use_cases/agents_acp_use_case.py`
   - stream update aggregation, task/message orchestration, error handling.
2. `scale-agentex/agentex/src/domain/use_cases/streams_use_case.py`
   - SSE loop, keepalive, and task stream projection.
3. `scale-agentex-python/src/agentex/lib/core/services/adk/streaming.py`
   - streaming context lifecycle + delta accumulation + persistence.

## Why Exercise 03 is the correct training target
1. It trains protocol correctness before framework code.
2. It trains strict adapter boundaries before implementation details.
3. It mirrors how both repos separate contracts from infrastructure.
4. It is the minimum architectural maturity expected from senior candidates.
