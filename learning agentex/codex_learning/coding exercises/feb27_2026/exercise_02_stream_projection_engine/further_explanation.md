# Further Explanation: Reference Mapping to Agentex

## Reference files in your workspace
1. `scale-agentex-python/src/agentex/lib/core/services/adk/streaming.py`
2. `scale-agentex-python/src/agentex/lib/core/services/adk/messages.py`
3. `scale-agentex-python/src/agentex/_streaming.py`
4. `scale-agentex-python/examples/tutorials/test_utils/async_utils.py`

## Definitive statements
1. `streaming.py` already models `start`, `delta`, `full`, and `done` update lifecycle.
2. `DeltaAccumulator` in `streaming.py` proves that delta streams must be reduced into canonical content before finalization.
3. `messages.py` uses `asyncio.gather` for concurrent update emission, which means concurrency safety is not optional in surrounding logic.
4. `_streaming.py` demonstrates robust SSE decoding boundaries; transport reliability and projection correctness are separate concerns.
5. `async_utils.py` starts stream consumption before sending events, confirming real-world race windows around first-message delivery.

## Adherence vs extension
1. Adheres:
   - same stream update lifecycle concepts
   - same asynchronous execution environment
   - same need for final canonical message state
2. Intentional extension:
   - explicit per-message idempotency by `event_id`
   - strict `seq` monotonicity contract
   - explicit terminal-state rejection semantics
   - first-class audit history in projection store

## Senior engineering bar
You should be able to explain this without notes:
1. The transport layer (SSE decoding) guarantees event framing.
2. The projection layer guarantees deterministic state.
3. Reliability comes from both layers, not one.
