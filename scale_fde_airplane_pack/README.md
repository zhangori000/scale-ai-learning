# Scale FDE Airplane Pack (Essay-Depth Edition)

This pack is now written in long-form editorial style across all rounds:

coding rounds. debugging rounds. backend practical rounds. inferred-from-codebase rounds.

The intention is to read like a textbook chapter, not a bullet summary. Each problem file is designed to explain:

what the problem really is. why naive solutions fail. how to solve step by step. how to reason about correctness. how to discuss it in interview language.

## Exclusions You Requested

excluded: Poker Game. excluded: Party Times. excluded as already done: Contractor + Skills matching. excluded as already done: Google Places API practical.

## Recommended Read Order

### Coding First

`coding/rt_01_nested_markup_parser/README.md`. `coding/rt_02_rich_text_mentions_links/README.md`. `coding/oa_01_session_pass_ranking/README.md`. `coding/oa_02_event_rollup_watermark/README.md`. `coding/oa_03_log_dedup_sliding_window/README.md`.

### Then Debugging

`debugging/dbg_01_cursor_pagination_duplication/README.md`. `debugging/dbg_02_async_lost_update_race/README.md`. `debugging/dbg_03_retry_double_write_bug/README.md`. `debugging/dbg_04_auth_cache_lockout_bug/README.md`. `debugging/dbg_05_stream_json_decode_crash/README.md`.

### Then Backend Practical

`backend_practical/bp_01_webhook_idempotent_ingestion/README.md`. `backend_practical/bp_02_order_station_assignment_api_sql/README.md`. `backend_practical/bp_03_sse_task_stream_service/README.md`. `backend_practical/bp_04_multitenant_rbac_service/README.md`. `backend_practical/bp_05_external_provider_failover_gateway/README.md`. `backend_practical/bp_06_batch_job_orchestrator_api/README.md`.

### Then Inferred From `scale-agentex`

Read each inferred topic in this order:

Coding editorial (`README.md`). Debugging editorial (`DEBUGGING_README.md`).

Topics:

`inferred_from_agentex/inf_01_temporal_vs_base_race_fix/README.md`. `inferred_from_agentex/inf_01_temporal_vs_base_race_fix/DEBUGGING_README.md`. `inferred_from_agentex/inf_02_redis_stream_replay_and_offsets/README.md`. `inferred_from_agentex/inf_02_redis_stream_replay_and_offsets/DEBUGGING_README.md`. `inferred_from_agentex/inf_03_auth_cache_negative_entry_policy/README.md`. `inferred_from_agentex/inf_03_auth_cache_negative_entry_policy/DEBUGGING_README.md`. `inferred_from_agentex/inf_04_cursor_pagination_contracts/README.md`. `inferred_from_agentex/inf_04_cursor_pagination_contracts/DEBUGGING_README.md`. `inferred_from_agentex/inf_05_transactional_rollback_boundary/README.md`. `inferred_from_agentex/inf_05_transactional_rollback_boundary/DEBUGGING_README.md`. `inferred_from_agentex/inf_06_streaming_delta_accumulation_protocol/README.md`. `inferred_from_agentex/inf_06_streaming_delta_accumulation_protocol/DEBUGGING_README.md`.

## Suggested Usage On Plane

Read coding editorials in order without skipping examples. Read corresponding debugging editorials right after to learn failure diagnosis language. For inferred section, read coding then debugging per topic pair.

This sequence is optimized for interview transfer: implementation first, diagnosis second.
