# AgentEx Task/Worker/Concurrency File Map

This map now includes:
- local links to your cloned repos under `ScaleAI`
- published GitHub links for cross-checking

## Local Clones (under ScaleAI)

### Repos
- [scale-agentex-python (local)](../scale-agentex-python/)
- [scale-agentex (local)](../scale-agentex/)

### scale-agentex-python local files
- [worker.py](../scale-agentex-python/src/agentex/lib/core/temporal/workers/worker.py) (see lines around 122, 185)
- [temporal_task_service.py](../scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py) (see lines around 29, 54, 66)
- [temporal_client.py](../scale-agentex-python/src/agentex/lib/core/clients/temporal/temporal_client.py) (see lines around 125, 145, 172)
- [adapter_redis.py](../scale-agentex-python/src/agentex/lib/core/adapters/streams/adapter_redis.py) (see lines around 32, 62, 116)
- [workflow.py](../scale-agentex-python/examples/demos/procurement_agent/project/workflow.py) (see lines around 105, 207, 384)
- [_sync.py](../scale-agentex-python/src/agentex/_utils/_sync.py) (see line around 16)
- [trace.py](../scale-agentex-python/src/agentex/lib/core/tracing/trace.py) (see line around 228)
- [tracing_processor_manager.py](../scale-agentex-python/src/agentex/lib/core/tracing/tracing_processor_manager.py) (see line around 36)
- [async_base_acp.py](../scale-agentex-python/src/agentex/lib/sdk/fastacp/impl/async_base_acp.py) (see lines around 16, 50)

### scale-agentex local files
- [run_worker.py](../scale-agentex/agentex/src/temporal/run_worker.py) (see lines around 38, 89, 149)
- [adapter_temporal.py](../scale-agentex/agentex/src/adapters/temporal/adapter_temporal.py) (see lines around 57, 146, 293, 352)
- [adapter_redis.py](../scale-agentex/agentex/src/adapters/streams/adapter_redis.py) (see lines around 40, 123, 178)
- [streams_use_case.py](../scale-agentex/agentex/src/domain/use_cases/streams_use_case.py) (see lines around 86, 113, 165)
- [authentication_cache.py](../scale-agentex/agentex/src/api/authentication_cache.py) (see lines around 41, 341)
- [agent_task_tracker_repository.py](../scale-agentex/agentex/src/domain/repositories/agent_task_tracker_repository.py) (see line around 62)
- [dependencies.py](../scale-agentex/agentex/src/config/dependencies.py) (see lines around 169, 292)
- [agent_acp_service.py](../scale-agentex/agentex/src/domain/services/agent_acp_service.py) (see line around 348)
- [race_conditions.md](../scale-agentex/agentex/docs/docs/development_guides/race_conditions.md)

## Published GitHub Links

### scale-agentex-python
- https://github.com/scaleapi/scale-agentex-python/blob/main/src/agentex/lib/core/temporal/workers/worker.py#L122
- https://github.com/scaleapi/scale-agentex-python/blob/main/src/agentex/lib/core/temporal/services/temporal_task_service.py#L29
- https://github.com/scaleapi/scale-agentex-python/blob/main/src/agentex/lib/core/clients/temporal/temporal_client.py#L125
- https://github.com/scaleapi/scale-agentex-python/blob/main/src/agentex/lib/core/adapters/streams/adapter_redis.py#L32
- https://github.com/scaleapi/scale-agentex-python/blob/main/examples/demos/procurement_agent/project/workflow.py#L105
- https://github.com/scaleapi/scale-agentex-python/blob/main/src/agentex/lib/sdk/fastacp/impl/async_base_acp.py#L16

### scale-agentex
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/temporal/run_worker.py#L38
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/adapters/temporal/adapter_temporal.py#L57
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/adapters/streams/adapter_redis.py#L40
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/domain/use_cases/streams_use_case.py#L86
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/api/authentication_cache.py#L41
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/domain/repositories/agent_task_tracker_repository.py#L62
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/config/dependencies.py#L169
- https://github.com/scaleapi/scale-agentex/blob/main/agentex/src/domain/services/agent_acp_service.py#L348
