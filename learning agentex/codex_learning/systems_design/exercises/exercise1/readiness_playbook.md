# Exercise 1 Readiness Playbook (Definitive)

Use these statements as non-negotiable engineering rules for this exercise.

## 1. Requirements rules

1. You MUST persist USER messages before publishing events.
2. You MUST treat TaskMessages as canonical history.
3. You MUST treat events as triggers, never as source-of-truth history.

## 2. Delivery semantics rules

1. You MUST assume at-least-once event delivery.
2. You MUST implement dedupe before any side effects.
3. You MUST ignore delivery payload offsets as recovery boundaries.

## 3. Cursor and recovery rules

1. You MUST read pending events from committed cursor state.
2. You MUST move cursor forward only after successful side effects.
3. You MUST reject cursor regression.

## 4. State ownership rules

1. You MUST scope state by `(task_id, agent_id)`.
2. You MUST block cross-agent writes to state.
3. You MUST make state updates idempotent under retries.

## 5. Scaling rules

1. You MUST partition processing by `(task_id, agent_id)` or equivalent ownership key.
2. You MUST design for hot partition detection and throttling.
3. You MUST define replay strategy before production rollout.

## 6. Observability rules

1. You MUST emit metrics for:
   - event lag
   - duplicate skips
   - cursor commit latency
   - retry count
2. You MUST log `task_id`, `agent_id`, `event_id`, and cursor transitions on every commit.
3. You MUST alert on stuck cursor lag and DLQ growth.

## 7. Production hardening order

1. Durable dedupe store
2. Optimistic concurrency on state
3. Transactional outbox
4. Dead letter queue
5. Replay tooling and runbooks

