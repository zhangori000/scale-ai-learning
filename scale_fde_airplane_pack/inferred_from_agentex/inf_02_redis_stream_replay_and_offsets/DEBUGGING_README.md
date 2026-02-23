# INF-02 Debugging Editorial: Redis Stream Replay and Offset Handling

This chapter is a deep debugging narrative for reconnect correctness in Redis-backed SSE streams.

## 1. Incident Shape

Users report one of three outcomes after reconnect:

1. missing updates
2. duplicate updates
3. random-looking jumps

All three usually come from one root category: replay contract mismatch between client cursor behavior and server stream semantics.

## 2. First Principle

You cannot debug stream replay until you can answer:

"What exactly does resume mean in this API?"

If this is undefined, every behavior can be argued as "expected" and nothing is fixable.

## 3. Contract Audit Checklist

Audit these links in sequence:

1. client stores last event id?
2. client sends it on reconnect (`Last-Event-ID` or query cursor)?
3. server accepts and propagates cursor?
4. server emits `id:` in each SSE frame?
5. server uses strict `>` replay semantics?

A broken link anywhere makes replay unreliable.

## 4. Retention Boundary Reality

Redis Streams often run with bounded retention (`MAXLEN`). Old IDs disappear.

If reconnect cursor references trimmed history, replay is impossible. The API must return explicit stale-cursor behavior (`cursor_expired` style outcome) instead of silent fallback.

Silent fallback causes hidden data loss.

## 5. Cursor Advancement Timing

Investigate where server updates internal `last_id` relative to send path.

- advance-before-send can cause missed delivery on transport failure
- advance-after-send can increase duplicate replay potential

Neither is universally "wrong," but semantics must be explicit and paired with client dedupe strategy.

## 6. Deterministic Reproduction Script

1. publish known sequence A, B, C
2. consume A, begin B
3. force disconnect during B boundary
4. reconnect with previous cursor
5. compare observed stream with expected contract

Run this repeatedly to remove coincidence.

## 7. Decode Fault Isolation

Malformed payloads can mimic replay issues by terminating stream loops early.

Ensure per-message decode exceptions are isolated and do not kill stream.

## 8. Patch Components

A robust patch generally includes:

1. explicit resume cursor input
2. SSE `id:` emission
3. strict replay from `>` cursor
4. stale-cursor policy for trimmed history
5. per-record decode isolation

## 9. Verification Matrix

Test matrix should include:

- reconnect with valid cursor
- reconnect with stale cursor
- duplicate reconnect attempts
- malformed record in middle of stream
- idle heartbeat behavior

## 10. Observability You Need

Metrics:

- resume_attempts_total
- cursor_expired_total
- stream_decode_error_total
- reconnect_gap_reports_total (if client telemetry exists)

Logs should always include stream topic and cursor values for forensic replay.

## 11. Interview Delivery Paragraph

"I debugged replay by tracing cursor propagation from client storage to SSE emission and Redis read boundaries. The bug was a contract mismatch under retention and reconnect timing. I fixed it with explicit resume semantics, stale-cursor handling, and deterministic replay tests using controlled disconnect scenarios."

## 12. Closing Thought

Replay bugs feel random until contract and boundaries are explicit. Once you define those boundaries, debugging becomes mechanical.
