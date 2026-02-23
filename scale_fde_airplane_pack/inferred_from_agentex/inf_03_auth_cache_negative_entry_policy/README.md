# INF-03 Coding Round Editorial: Auth Cache Negative Entry Policy

This chapter teaches a deep, interview-ready implementation of authentication caching that is fast under normal load and safe during backend incidents.

Grounded source files:

`scale-agentex/agentex/src/api/authentication_middleware.py`. `scale-agentex/agentex/src/api/authentication_cache.py`. `scale-agentex/agentex/src/api/middleware_utils.py`.

## The Actual Problem

Auth caching is easy to add and easy to get wrong.

The dangerous failure mode is cache poisoning:

backend verifier has temporary outage. middleware treats temporary failure as invalid credential. negative cache stores failure. valid users are denied until TTL expires.

So the true problem is not "add cache." It is "classify failures correctly before caching."

## Mental Model

Every auth verification outcome must be one of three classes:

`VALID`: credential is confirmed valid. `INVALID`: credential is confirmed invalid. `TEMP_FAILURE`: verifier unavailable, timeout, or internal error.

Only one of these (`INVALID`) belongs in short negative cache.

## Codebase Insight

Current middleware uses a sentinel like `__FAILED_AUTH__` for negative caching in some paths. That can be fine if and only if insertion policy is strict.

Current cache implementation (`AsyncTTLCache`) is solid: async lock, TTL, bounded size. The key improvement area is policy, not data structure.

## Why Interviewers Ask This

They test your judgment on reliability vs performance.

A naive answer can reduce DB traffic while creating user lockout during incidents. A strong answer preserves both throughput and correctness.

## Step 0: Define Caching Policy Table

Write this first:

VALID -> positive cache (`ttl=300s`, example). INVALID -> negative cache (`ttl=5-15s`). TEMP_FAILURE -> no negative cache.

This one table drives correct implementation.

## Step 1: Refactor Verifier To Typed Outcome

Do not return raw HTTP responses from verifier internals.

```python
class AuthResult(Enum):
    VALID = "valid"
    INVALID = "invalid"
    TEMP_FAILURE = "temp_failure"

@dataclass
class VerifyOutcome:
    result: AuthResult
    principal_id: str | None = None
```

Typed outcomes prevent accidental misclassification.

## Step 2: Implement Verifier With Explicit Mapping

```python
async def verify_api_key(api_key: str) -> VerifyOutcome:
    try:
        row = await repo.lookup(api_key)
        if row is None:
            return VerifyOutcome(result=AuthResult.INVALID)
        return VerifyOutcome(result=AuthResult.VALID, principal_id=row.agent_id)
    except TimeoutError:
        return VerifyOutcome(result=AuthResult.TEMP_FAILURE)
    except Exception:
        return VerifyOutcome(result=AuthResult.TEMP_FAILURE)
```

## Step 3: Separate Positive And Negative Caches

Why separate?

different TTLs. clearer observability. less accidental key collision between states.

## Step 4: Middleware Decision Flow

```python
outcome = await verify_api_key(api_key)

if outcome.result is AuthResult.VALID:
    await positive_cache.set(api_key, outcome.principal_id, ttl=300)
    allow_request(outcome.principal_id)
elif outcome.result is AuthResult.INVALID:
    await negative_cache.set(api_key, "invalid", ttl=10)
    deny_401()
else:
    deny_503_without_negative_cache()
```

The no-cache branch for temporary failure is the key protection.

## Step 5: Rotation And Revocation Handling

Positive cache can outlive key state changes.

Add invalidation on:

key created. key rotated. key revoked.

If invalidation hooks are not available, reduce positive TTL.

## Step 6: Status Code Strategy

Be explicit whether temporary auth backend failures return `503` or `401` with internal reason code.

Operationally, `503` is cleaner for incident triage.

## Step 7: Worked Incident Timeline

Without fix:

12:00 verifier timeout. valid key cached negative. 12:01 verifier recovers. valid key still denied until 12:05 TTL expiry.

With fix:

12:00 verifier timeout. no negative cache insertion. 12:01 verifier recovers. next request succeeds immediately.

This timeline often convinces interviewers quickly.

## Step 8: Implementation Order

introduce typed outcome model. update verifier mapping. split positive/negative cache APIs. enforce middleware decision policy. add metrics and tests.

## Step 9: Tests You Must Include

Test 1: invalid credential negative-caches briefly.

Test 2: temporary verifier failure does not poison cache.

Test 3: valid credential positive-cache hit bypasses backend.

Test 4: rotation invalidates old positive cache.

Test 5: concurrent requests keep consistent cache entries.

## Common Mistakes

same TTL for positive and negative entries. caching transient 5xx outcomes as invalid. no invalidation for key lifecycle events. no metrics to detect poisoning.

## Interview Wrap-Up Script

"I separate identity truth from verifier availability. The cache policy is outcome-driven: valid gets medium positive TTL, invalid gets short negative TTL, and temporary failures are never negative-cached. That preserves performance under load and avoids lockout after transient outages."
