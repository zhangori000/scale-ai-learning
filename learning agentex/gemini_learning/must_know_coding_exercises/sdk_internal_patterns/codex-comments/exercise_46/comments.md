# Exercise 46 Comments

## Verdict
This exercise captures the core buffering intuition correctly, but it is a subset of real SSE behavior in the SDK.

## Reference implementation
- `scale-agentex-python/src/agentex/_streaming.py`
  - `SSEDecoder._iter_chunks` and `SSEDecoder._aiter_chunks`
  - `SSEDecoder.decode`
  - `Stream` and `AsyncStream` integration that consumes decoded events and closes responses safely

## Definitive statements
1. The real decoder is stateful and spec-oriented, not just a `data:`-line JSON splitter.
2. Chunk assembly is robust to network fragmentation and handles `\r\r`, `\n\n`, and `\r\n\r\n` event delimiters.
3. Event dispatch happens only when a blank line terminates an SSE event.
4. The decoder supports `event`, `data`, `id`, and `retry` fields, plus comment lines (`:`) and unknown-field ignore behavior.
5. Multiple `data:` lines are accumulated and joined with newline before event emission.
6. `last_event_id` persists across events per SSE spec behavior.
7. Both sync and async byte iterators are first-class in the implementation.
8. JSON parsing is performed by `ServerSentEvent.json()` and stream wrappers, not by the line decoder itself.

## How the Gemini exercise adheres
- Adheres on the foundational pattern: keep a buffer, emit only complete events, carry incomplete tails forward.
- Deviates by omitting key SSE semantics (`event/id/retry/comments/multi-line data`) and by coupling decoding directly to JSON parsing.
