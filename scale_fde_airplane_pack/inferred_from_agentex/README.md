# Inferred From Agentex: Editorial Track

This section is now organized as editorial-style guides, not drill lists.

For every inferred topic, read in this exact order:

1. `README.md` (Coding Round Editorial)
2. `DEBUGGING_README.md` (Debugging Round Editorial)

The goal is to mirror how real interviews unfold: first solve the coding problem from first principles, then debug production failure modes of that same system.

## Prerequisites

Read these once before any inferred chapter:

1. `context/00_how_to_read_agentex.md`
2. `context/01_async_concurrency_primer.md`
3. `context/02_streaming_and_sse_primer.md`
4. `context/03_auth_cache_primer.md`
5. `context/04_cursor_pagination_primer.md`
6. `context/05_transactions_and_outbox_primer.md`

## Reading Order

1. `inf_01_temporal_vs_base_race_fix/README.md`
2. `inf_01_temporal_vs_base_race_fix/DEBUGGING_README.md`
3. `inf_02_redis_stream_replay_and_offsets/README.md`
4. `inf_02_redis_stream_replay_and_offsets/DEBUGGING_README.md`
5. `inf_03_auth_cache_negative_entry_policy/README.md`
6. `inf_03_auth_cache_negative_entry_policy/DEBUGGING_README.md`
7. `inf_04_cursor_pagination_contracts/README.md`
8. `inf_04_cursor_pagination_contracts/DEBUGGING_README.md`
9. `inf_05_transactional_rollback_boundary/README.md`
10. `inf_05_transactional_rollback_boundary/DEBUGGING_README.md`
11. `inf_06_streaming_delta_accumulation_protocol/README.md`
12. `inf_06_streaming_delta_accumulation_protocol/DEBUGGING_README.md`

## Source Grounding

These editorials are grounded in real `scale-agentex` files, including:

- `agentex/src/domain/use_cases/agents_acp_use_case.py`
- `agentex/src/domain/use_cases/streams_use_case.py`
- `agentex/src/adapters/streams/adapter_redis.py`
- `agentex/src/api/authentication_middleware.py`
- `agentex/src/api/authentication_cache.py`
- `agentex/src/utils/pagination.py`
- `agentex/src/api/routes/messages.py`
- `agentex/src/adapters/crud_store/adapter_mongodb.py`
- `agentex/src/domain/services/task_service.py`
- `agentex/tests/unit/infrastructure/test_transactional_proof.py`

## How To Use Each Editorial

For coding-round files, follow the sections in order and implement exactly in the sequence shown.

For debugging-round files, follow the incident flow exactly: reproduce, instrument, isolate, fix, validate, and only then discuss optimization.
