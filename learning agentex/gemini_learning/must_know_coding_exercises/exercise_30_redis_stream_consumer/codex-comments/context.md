# Codex Context: Exercise 30 (Redis Stream Consumer)

This exercise is directly motivated by real `scale-agentex` stream code:

1. `scale-agentex/agentex/src/domain/use_cases/streams_use_case.py`
   - `read_messages(...)` validates each message with Pydantic and catches `ValidationError` so bad payloads do not crash the whole stream reader.
   - `stream_task_events(...)` advances `last_id` after each message is processed in the loop, then yields SSE data.
2. `scale-agentex/agentex/src/adapters/streams/adapter_redis.py`
   - Uses Redis `XREAD` with `last_id` and yields `(message_id, data)` entries.
   - Parsing errors are handled per-message, not as fatal stream failure.
3. `scale-agentex/agentex/docs/docs/concepts/task.md`
   - Emphasizes forward-only cursor safety and resumable processing.

Why this pattern exists:

1. At-least-once delivery means you must persist/advance progress carefully.
2. Poison-pill messages (invalid schema) must be skipped without wedging the consumer forever.
3. Cursor movement must be per-message and forward-only.

