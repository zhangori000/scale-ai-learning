# DBG-05: Stream JSON Decode Crash in Consumer Loop (Debugging Essay)

This chapter explores a reliability bug where one malformed stream record kills the entire SSE stream. It is a classic liveness-versus-correctness boundary issue.

Broken loop shape:

```python
async for message_id, fields in redis_messages:
    data = json.loads(fields["data"])
    yield to_sse(data)
```

If one payload is invalid JSON, exception escapes loop, stream terminates, client disconnects, and all subsequent good messages are lost until reconnect.

The key design principle for stream consumers is fault isolation:

"A bad single record should be observable and skippable, not fatal to the whole stream session."

Debugging sequence:

reproduce with one malformed record followed by one valid record. confirm stream stops before valid record. inspect exception handling scope. verify no per-record try/except inside loop.

Patch pattern:

decode per message within try/except. on decode error: increment metric, structured log, continue loop. on successful decode: emit SSE frame with id.

Patched implementation:

```python
import json

async def stream_events(redis_messages, metrics, logger):
    async for message_id, fields in redis_messages:
        raw = fields.get("data")
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            data = json.loads(raw)
        except Exception as exc:
            metrics.inc("stream.decode_error")
            logger.warning(
                "stream decode failure",
                extra={"message_id": message_id, "error": str(exc)},
            )
            continue

        yield f"id: {message_id}\\ndata: {json.dumps(data)}\\n\\n"
```

Why this patch is correct:

liveness preserved for subsequent records. malformed input is measured and logged. replay/diagnosis remains possible via message ID.

Regression test:

```python
async def test_malformed_record_isolated():
    msgs = [
        ("1-0", {"data": "{bad json"}),
        ("1-1", {"data": '{"ok": true}'}),
    ]

    async def gen():
        for m in msgs:
            yield m

    out = []
    async for frame in stream_events(gen(), metrics=FakeMetrics(), logger=FakeLogger()):
        out.append(frame)

    assert len(out) == 1
    assert '"ok": true' in out[0]
```

Do not forget observability in production:

decode error count. decode error rate by topic. first-seen malformed payload samples.

Interview close:

"I fixed this by moving decode handling to per-record isolation. One malformed payload now increments a metric and is skipped, while stream liveness is preserved for subsequent valid events."
