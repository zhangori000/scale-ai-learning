# Context 01: Async Concurrency Primer For This Pack

Concurrency bugs in backend systems are usually not complicated mathematically. They are complicated operationally. The underlying bug is often simple: two workers read state A, both compute state B, and whichever write lands last wins. The damage is subtle because you do not get an exception. You get silent corruption.

In asynchronous Python services, this appears whenever there is a read-modify-write sequence over shared state without serialization or atomic update semantics. Any `await` between read and write increases risk because the scheduler can switch tasks.

There are three broad strategies to prevent this class of bug.

The first strategy is single-writer serialization. You route all updates for one entity key through one worker or one queue partition. This is usually easiest to reason about and is common in workflow engines.

The second strategy is storage-level atomicity. You avoid read-modify-write in application code and use operations like `SET x = x + 1` in a single SQL statement or a compare-and-swap primitive.

The third strategy is optimistic concurrency control. You read a version, write only if version matches, and retry if mismatch. This is useful when contention exists but not always high.

When discussing concurrency in interviews, do not only state one pattern. Explain why that pattern fits the workload. For high write contention by entity key, single-writer or atomic storage operations are usually preferable. For distributed systems that cannot guarantee ordering, idempotency and conflict handling become mandatory.

For this pack, keep one mental invariant: if your system can replay, retry, or receive duplicate delivery, your handlers must be idempotent and your progress cursor must move only after durable success.
