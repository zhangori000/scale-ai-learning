# Context 02: Streaming And SSE Primer

Server-Sent Events look simple because the wire format is simple text. But production streaming systems are defined by what happens when the network is unreliable, clients reconnect, and upstream events are malformed.

An SSE stream should be treated as a long-lived state machine. The main states are connected, receiving events, idle heartbeat, transient error, and disconnect. A robust implementation keeps the stream alive across recoverable errors and only terminates on explicit client disconnect or fatal server condition.

Replay semantics matter more than throughput for many agent UIs. A user refreshes and expects continuity. That means the server must support resume from a cursor or last event id, and it must define what happens if that cursor is too old and the underlying stream has been trimmed.

Backpressure is also real. If a client consumes slowly, the server must not allow unbounded memory growth. Typical controls are bounded read batch sizes, short pauses between batches, and connection timeouts.

Malformed event payloads are inevitable in distributed systems. A single bad payload should not crash every subscriber stream. Decode errors should be isolated per message and observed via metrics.

As you read streaming chapters in this pack, keep checking for these invariants: one, cursor progression only after successful send; two, heartbeat while idle; three, malformed payload isolation; four, explicit policy for stale cursors after retention trimming.
