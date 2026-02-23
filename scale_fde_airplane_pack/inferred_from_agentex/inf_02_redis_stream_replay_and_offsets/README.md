# INF-02 Coding Round Editorial: Redis Stream Replay and Offset Handling

This chapter is a full walkthrough for one of the most common backend interview traps: streaming works during the happy path, but reconnect behavior is inconsistent and nobody can explain exactly why. The goal is to make you comfortable enough that if an interviewer gives you this problem cold, you can build a correct solution from first principles.

Grounded source files in the Agentex codebase:

`scale-agentex/agentex/src/adapters/streams/adapter_redis.py`. `scale-agentex/agentex/src/domain/use_cases/streams_use_case.py`. `scale-agentex/agentex/src/api/routes/tasks.py`.

## What Problem Are We Actually Solving?

At first glance, the prompt sounds simple: "stream events to the client." But production streaming has a second, harder requirement: reconnect correctness.

When client connections drop and reconnect, the server must answer one precise question:

"From which event should I resume, and what do I do if that position is no longer available?"

If you do not define this clearly, you get two bad outcomes:

Silent data loss: events are skipped after reconnect. Silent duplication: same event appears multiple times with no dedupe strategy.

Both outcomes happen in real systems even when the code "looks fine."

## Mental Model Before Code

Think of this as three moving positions that must stay coherent:

Redis stream position: the server's source-of-truth ID sequence. Server read position: the `last_id` used in each `XREAD` call. Client receive position: the last event that actually reached the client.

If these positions drift without explicit contract, reconnect semantics become accidental.

## Small Vocabulary Primer (So We Do Not Hand-Wave)

Redis Stream ID: monotonic identifier like `1700000000000-0`. SSE: server sends text frames over HTTP (`text/event-stream`). Resume cursor: event ID the client sends back on reconnect. Retention trim: old stream events removed because max length is bounded.

You should be able to define these in one sentence each during interview.

## Why This Is A Hard Interview Question

Most candidates can stream live data. Fewer can design replay semantics under trim and disconnect boundaries.

Interviewers are testing whether you can do both:

Build the pipeline. Define correctness policy for failure paths.

## Codebase Tour: What Agentex Already Gives You

From `adapter_redis.py`, writes are bounded:

```python
await self.redis.xadd(
    name=topic,
    fields={"data": data_json},
    maxlen=self.environment_variables.REDIS_STREAM_MAXLEN,
    approximate=True,
)
```

Important consequence: history is finite. Old cursors can expire.

From read path in `adapter_redis.py`:

```python
response = await self.redis.xread(
    streams={topic: last_id},
    count=count,
    block=timeout_ms,
)
```

Important consequence: Redis returns entries strictly after `last_id`.

From `streams_use_case.py`, stream loop tracks `last_id` and emits SSE data with keepalive behavior.

From `tasks.py`, route exposes this as a streaming endpoint.

So the core building blocks already exist. The missing piece in many interview variants is explicit replay contract.

## The Naive Solution (And Why It Fails)

Naive version:

On connect, start at `$` always. Stream live events only. Ignore reconnect cursor.

Why it fails:

If client disconnects for 5 seconds and 20 events occur, all 20 are lost. System looks healthy but user state is stale.

Another naive version:

Accept cursor. If invalid, silently restart from `$`.

Why it fails:

Client thinks it resumed from a concrete point. Server actually skipped unknown range. Silent correctness bug.

## Step 0: Define The Contract In Plain English

Do this before writing any code.

Contract:

No cursor -> live-only stream from now (`$`). Valid cursor -> replay events with ID greater than cursor. Expired cursor (trimmed history) -> explicit response (`409 cursor_expired`) or explicit gap event.

The critical part is explicitness. No hidden fallback.

## Step 1: Decide Resume Cursor Input

Choose one input path and be consistent:

HTTP `Last-Event-ID` header (SSE-native). Query param `cursor`.

Either is acceptable. Just document precedence if both are present.

Example resolution logic:

```python
def resolve_resume_id(request):
    return request.headers.get("Last-Event-ID") or request.query_params.get("cursor")
```

## Step 2: Emit SSE `id:` On Every Event

If you do not emit event IDs, browser cannot send meaningful resume cursor.

SSE frame shape should be:

```python
yield f"id: {event_id}\ndata: {payload}\n\n"
```

This single line is often missing in weak solutions.

## Step 3: Build Replay-Aware Stream Loop

Skeleton:

```python
async def stream_task_events(topic: str, resume_id: str | None):
    last_id = resume_id or "$"

    while True:
        rows = await redis.xread(streams={topic: last_id}, count=50, block=2000)
        if not rows:
            yield ":ping\n\n"
            continue

        for _, messages in rows:
            for msg_id, fields in messages:
                payload = decode_payload(fields)
                if payload is None:
                    continue
                yield f"id: {msg_id}\ndata: {json.dumps(payload)}\n\n"
                last_id = msg_id
```

Why this order? `last_id` progresses monotonically with emitted events.

## Step 4: Handle Expired Cursor Case

Because retention is bounded, `resume_id` may refer to deleted history.

You need one explicit policy. Pick one.

Policy A (strict, recommended in enterprise APIs):

return `409 cursor_expired`. client must reload snapshot and restart stream.

Policy B (lossy continuity):

jump to `$`. emit control event like `gap_detected`.

Never hide which policy you chose.

## Step 5: Define Delivery Semantics Honestly

SSE does not provide strong per-message acknowledgement back to server in most designs.

So practical semantics are usually:

server provides at-least-once replay support via event IDs. client dedupes by `id`.

If interviewer asks "exactly once?" answer:

"Exactly-once transport is unrealistic here. We implement exactly-once effect at consumer state layer via idempotent event IDs."

That answer is strong.

## Step 6: Add Robust Payload Handling

From codebase, payload is JSON inside Redis field `data`.

Decoder should be defensive:

check field exists. decode bytes to utf-8. parse JSON. on failure, log and continue.

Do not crash entire stream because one payload is malformed.

## Step 7: Add Operational Controls

Interviewers like practical controls:

batch size (`count`) to cap per-iteration load. block timeout to avoid hot spin. keepalive ping for idle proxies. retention maxlen tuned to reconnect window.

State the retention tradeoff explicitly:

small maxlen saves memory. large maxlen improves replay window.

## Step 8: Worked Timeline Example

Imagine stream IDs:

E1: `100-0`. E2: `101-0`. E3: `102-0`.

Client receives E1, E2, then disconnects.

Reconnect sends cursor `101-0`.

Server reads `XREAD` with `last_id=101-0` and returns E3 onward.

If E2 and E3 were trimmed before reconnect and cursor is too old, server returns explicit `cursor_expired` per contract.

This simple timeline is excellent in interviews.

## Step 9: Full Implementation Sequence (What To Code First)

Add resume cursor resolver in route. Pass resume cursor into stream use case. Emit SSE `id:` lines. Add cursor-expiry policy path. Add tests.

Coding in this order avoids backtracking.

## Step 10: Tests That Prove You Are Done

Test 1: live connect without cursor starts from new events only.

Test 2: reconnect with valid cursor replays strictly after cursor.

Test 3: malformed payload is skipped and stream continues.

Test 4: expired cursor triggers explicit policy response.

Test 5: duplicate reconnect attempts remain deterministic.

Test 6: keepalive works during idle periods.

## Common Mistakes To Avoid

Storing cursor in memory only and losing it across reconnect. Forgetting `id:` in SSE frame. Silently falling back when cursor invalid. Returning giant unbounded batches. Crashing stream loop on one bad JSON payload.

## Interview Wrap-Up Script

"I solve Redis replay as a contract problem before a coding problem. I define resume semantics for valid, missing, and expired cursors; emit stable SSE event IDs; and replay from strict greater-than cursor via `XREAD`. Because retention is bounded, I add explicit cursor-expired behavior instead of silent fallback. Then I validate with reconnect, trim, and malformed-payload tests so correctness is observable and repeatable."
