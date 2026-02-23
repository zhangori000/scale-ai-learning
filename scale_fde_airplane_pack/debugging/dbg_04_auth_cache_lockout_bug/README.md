# DBG-04: Auth Cache Lockout from Negative Caching (Debugging Essay)

This chapter addresses an operationally painful bug class: legitimate users remain unauthorized after key rotation or transient auth backend issues. The system appears fast because cache hits are high, but correctness is broken.

Observed behavior:

failed auth decisions are cached. requests check cache before backend verification. after rotation/outage, valid users still receive `401` for several minutes.

The likely root cause is negative-cache poisoning: failures that should be temporary are cached as persistent invalid decisions with long TTL.

Three failure categories must be separated:

definitive invalid credential. valid credential. temporary verifier/backend failure.

If category 3 is cached as category 1, lockout occurs.

Debugging flow:

inspect cache entries for affected keys. compare lockout duration with negative TTL. correlate first lockout timestamp with backend health incidents. verify whether verifier exceptions are being mapped to negative cache writes.

Patch policy:

positive cache TTL moderate (for example 300s). negative cache TTL short (for example 10s). never negative-cache temporary backend errors. invalidate auth cache on key rotate/create/revoke events.

Patch sketch:

```python
NEGATIVE_TTL_SEC = 10
POSITIVE_TTL_SEC = 300

async def verify_api_key(cache, db, api_key):
    hit = await cache.get(api_key)
    if hit is not None:
        if hit == "NEGATIVE":
            return None
        return hit

    try:
        principal = await db.lookup_key(api_key)
    except TemporaryAuthBackendError:
        # do not poison cache
        raise

    if principal is None:
        await cache.set(api_key, "NEGATIVE", ttl=NEGATIVE_TTL_SEC)
        return None

    await cache.set(api_key, principal, ttl=POSITIVE_TTL_SEC)
    return principal
```

Why this works:

short negative TTL limits harm for true invalid keys. temporary failures no longer create long lockout shadows. explicit invalidation removes stale positive/negative entries during key lifecycle changes.

Regression tests:

invalid key -> fast repeated reject, then expiration. temporary backend error -> no negative cache insertion. rotated key becomes accepted immediately after backend recovery/invalidation.

Operational counters:

`auth_negative_cache_hit_total`. `auth_temp_backend_error_total`. `auth_cache_invalidation_total`.

Interview close:

"I treated this as a policy bug, not a performance bug. Negative cache entries were too sticky and conflated temporary verifier failures with true invalid credentials. I separated failure classes, shortened negative TTL, skipped caching transient errors, and added rotation-driven invalidation."
