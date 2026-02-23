# DBG-03: Retry-Induced Double Write (Debugging Essay)

This chapter analyzes a high-impact reliability bug: retries that duplicate side effects. The concrete scenario is payment capture. The endpoint retries after timeout, and some customers are charged twice.

Broken implementation:

```python
async def capture_payment(gateway, order_id, amount):
    for _ in range(3):
        try:
            return await gateway.charge(order_id=order_id, amount=amount)
        except TimeoutError:
            continue
    raise TimeoutError("capture failed")
```

Why this is unsafe:

A timeout does not tell you whether provider executed the charge. It only says client did not receive success response in time. If the provider already charged and response was lost, retry issues a second charge.

So this is not a retry-count issue. It is a missing idempotency contract issue.

Debugging sequence:

1. correlate duplicate charges with timeout/retry logs
2. inspect whether requests share logical operation identity (`order_id`)
3. verify provider API supports idempotency keys
4. confirm client code does not send stable key across retries

Correct fix:

Attach deterministic idempotency key per logical operation and reuse it for every retry attempt.

```python
async def capture_payment(gateway, order_id, amount, idem_key=None):
    key = idem_key or f"pay:{order_id}"
    for _ in range(3):
        try:
            return await gateway.charge(
                order_id=order_id,
                amount=amount,
                idempotency_key=key,
            )
        except TimeoutError:
            continue
    raise TimeoutError("capture failed")
```

This ensures repeated attempts collapse to one provider-side operation.

Second safety layer:

Persist operation status keyed by idempotency key in your DB. If your service restarts mid-flight, you can reconstruct state and avoid ambiguity.

Regression test pattern:

```python
async def test_timeout_retry_not_double_charge(fake_gateway):
    await capture_payment(fake_gateway, "o1", 100)
    assert fake_gateway.charge_count_for_key("pay:o1") == 1
```

Additional test:

- simulate timeout on first attempt, success on second
- verify exactly one financial side effect

Operational metrics to monitor after fix:

1. timeout rate
2. retry rate
3. duplicate-key replay rate
4. provider idempotency conflict responses

These metrics catch contract regressions quickly.

Interview close:

"I diagnosed the bug as ambiguous timeout semantics, not transient failure. I enforced idempotency by assigning one stable key per logical charge and reusing it across retries, then added regression tests that simulate timeout-before-response to prove no duplicate side effects occur."
