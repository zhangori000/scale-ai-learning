# INF-03 Debugging Editorial: Auth Cache Negative Entry Policy

This chapter explains how to debug authorization lockouts caused by incorrect negative-cache behavior.

## 1. Incident Pattern

System behavior:

- known-valid credentials suddenly receive `401`
- lockout persists even after auth backend is healthy
- duration often aligns with cache TTL

This TTL-aligned symptom is a strong indicator of cache poisoning.

## 2. Core Diagnostic Question

Ask one question early:

"Are failed authentications being served from cache, and if so, why were they cached?"

If failures are cache-served, root cause is policy classification, not immediate backend state.

## 3. Failure Class Separation

A robust auth system distinguishes:

1. definitive invalid credential
2. definitive valid credential
3. temporary verification failure (timeout/5xx/outage)

Poisoning occurs when class 3 is cached as class 1.

## 4. Timeline Correlation Method

Collect four timestamps:

1. first auth backend degradation
2. first cached deny event
3. backend recovery time
4. final lockout disappearance

If (4 - 3) approximately equals negative TTL, you have strong evidence of poisoned negative cache.

## 5. Code-Path Audit

Inspect middleware branches where failed verification writes cache entries.

Look for logic like "if verification failed then cache NEGATIVE" without status/error classification.

That pattern is unsafe.

## 6. Reproduction Harness

Reproduce with controlled sequence:

1. valid key request during induced verifier timeout
2. verify failure response
3. restore verifier
4. retry same key immediately

If immediate retry still denied from cache, poisoning is confirmed.

## 7. Patch Principles

1. negative-cache only definitive invalid credentials
2. do not negative-cache temporary verifier failures
3. keep negative TTL short
4. invalidate auth cache on key rotation/revocation events

## 8. Validation Strategy

After patch, rerun timeline sequence:

- outage request fails but does not poison cache
- first post-recovery request succeeds

Also validate true-invalid credentials still benefit from short negative cache.

## 9. Metrics and Alarms

Add/track:

- negative_cache_hit_total
- temp_verifier_failure_total
- negative_cache_write_total by reason
- post-rotation-auth-failure rate

This prevents slow reintroduction of lockout behavior.

## 10. Interview Delivery Paragraph

"I treated this as a cache policy bug. Temporary verification failures were being cached as invalid credential decisions, creating lockout shadows after recovery. I separated failure classes, limited negative caching to definitive invalid outcomes with short TTL, and validated immediate recovery behavior through outage-timeline tests."

## 11. Closing Thought

Authentication cache bugs are rarely fixed by TTL tweaks alone. They are fixed by correct semantic classification of failure modes.
