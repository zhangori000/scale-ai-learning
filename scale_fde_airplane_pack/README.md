# Scale FDE Airplane Pack (Essay-Depth Edition)

This pack is now written in long-form editorial style across all rounds:

- coding rounds
- debugging rounds
- backend practical rounds
- inferred-from-codebase rounds

The intention is to read like a textbook chapter, not a bullet summary. Each problem file is designed to explain:

1. what the problem really is
2. why naive solutions fail
3. how to solve step by step
4. how to reason about correctness
5. how to discuss it in interview language

## Exclusions You Requested

- excluded: Poker Game
- excluded: Party Times
- excluded as already done: Contractor + Skills matching
- excluded as already done: Google Places API practical

## Recommended Read Order

### Coding First

1. `coding/rt_01_nested_markup_parser/README.md`
2. `coding/rt_02_rich_text_mentions_links/README.md`
3. `coding/oa_01_session_pass_ranking/README.md`
4. `coding/oa_02_event_rollup_watermark/README.md`
5. `coding/oa_03_log_dedup_sliding_window/README.md`

### Then Debugging

1. `debugging/dbg_01_cursor_pagination_duplication/README.md`
2. `debugging/dbg_02_async_lost_update_race/README.md`
3. `debugging/dbg_03_retry_double_write_bug/README.md`
4. `debugging/dbg_04_auth_cache_lockout_bug/README.md`
5. `debugging/dbg_05_stream_json_decode_crash/README.md`

### Then Backend Practical

1. `backend_practical/bp_01_webhook_idempotent_ingestion/README.md`
2. `backend_practical/bp_02_order_station_assignment_api_sql/README.md`
3. `backend_practical/bp_03_sse_task_stream_service/README.md`
4. `backend_practical/bp_04_multitenant_rbac_service/README.md`
5. `backend_practical/bp_05_external_provider_failover_gateway/README.md`
6. `backend_practical/bp_06_batch_job_orchestrator_api/README.md`

### Then Inferred From `scale-agentex`

Read each inferred topic in this order:

1. Coding editorial (`README.md`)
2. Debugging editorial (`DEBUGGING_README.md`)

Topics:

1. `inferred_from_agentex/inf_01_temporal_vs_base_race_fix/README.md`
2. `inferred_from_agentex/inf_01_temporal_vs_base_race_fix/DEBUGGING_README.md`
3. `inferred_from_agentex/inf_02_redis_stream_replay_and_offsets/README.md`
4. `inferred_from_agentex/inf_02_redis_stream_replay_and_offsets/DEBUGGING_README.md`
5. `inferred_from_agentex/inf_03_auth_cache_negative_entry_policy/README.md`
6. `inferred_from_agentex/inf_03_auth_cache_negative_entry_policy/DEBUGGING_README.md`
7. `inferred_from_agentex/inf_04_cursor_pagination_contracts/README.md`
8. `inferred_from_agentex/inf_04_cursor_pagination_contracts/DEBUGGING_README.md`
9. `inferred_from_agentex/inf_05_transactional_rollback_boundary/README.md`
10. `inferred_from_agentex/inf_05_transactional_rollback_boundary/DEBUGGING_README.md`
11. `inferred_from_agentex/inf_06_streaming_delta_accumulation_protocol/README.md`
12. `inferred_from_agentex/inf_06_streaming_delta_accumulation_protocol/DEBUGGING_README.md`

## Suggested Usage On Plane

1. Read coding editorials in order without skipping examples.
2. Read corresponding debugging editorials right after to learn failure diagnosis language.
3. For inferred section, read coding then debugging per topic pair.

This sequence is optimized for interview transfer: implementation first, diagnosis second.
