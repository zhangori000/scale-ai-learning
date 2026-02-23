# Context 03: Auth Cache Primer (Positive And Negative Caching)

Authentication checks are often expensive because they may involve database lookups, key verification, and external auth gateways. Caching is therefore necessary for latency and throughput. The difficult part is not positive caching. The difficult part is negative caching.

Positive caching stores successful verification outcomes. This is straightforward. If a credential was valid recently, it is likely still valid for a short period.

Negative caching stores failed verifications. This is dangerous because a failed check can become valid soon after, for example when a key is rotated, propagated, or restored after temporary backend inconsistency. Long-lived negative cache entries can lock out real users.

A robust auth cache therefore distinguishes between definitive failure and transient failure. A definitive failure such as "credential does not exist" may be cached briefly. A transient failure such as upstream timeout should not be cached as invalid.

Another subtle issue is cache key design. Any key material containing secrets should be hashed before use in in-memory maps or logs. Header-based cache keys should include only authentication-relevant headers to avoid cache pollution and accidental cardinality explosion.

In interviews, a strong answer includes both policy and incident prevention. Policy means TTL strategy and invalidation triggers. Incident prevention means proving you will not cache backend outages as invalid identities.
