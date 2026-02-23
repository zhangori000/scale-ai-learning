# Context 05: Transactions And Outbox Primer

Database transactions protect atomicity for operations within the same database boundary. They do not protect side effects in external systems such as message brokers or third-party APIs.

A common failure pattern is this sequence: the service writes DB state, calls external API, then crashes before marking completion. On retry, the external side effect may be duplicated. Conversely, if external API succeeds but DB commit fails, systems diverge.

The transactional outbox pattern addresses this by splitting the problem. In one transaction, the service writes business state and an outbox event row. After commit, a background worker publishes outbox events to external systems. If publishing fails, the worker retries safely. This converts a distributed atomicity problem into a local atomicity plus retriable delivery problem.

Rollback tests are essential because they verify behavior under failure paths, not just happy paths. A good rollback test intentionally raises after performing writes and then asserts no partial state leaked.

In interviews, the best response is to describe both boundary and mechanism. Boundary means what is inside one transaction. Mechanism means how side effects are handled after commit, usually with outbox and idempotent consumers.
