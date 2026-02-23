# How to Solve This Ticketmaster Prompt in Interview

This guide is structured for practical interviews where they want user flow + components, not heavy infra math.

## 1) Clarify scope quickly (30-60 seconds)

Say:

1. "I'll optimize for correctness of ticket allocation and checkout lifecycle."
2. "I'll focus on user flow and component responsibilities."
3. "I'll avoid deep capacity math unless needed."

Confirm assumptions:

- one event or multi-event? (start with one event model, mention extension)
- seats are fungible count or seat map? (start with count model)
- payment provider is external and can fail/timeout

## 2) Key invariants (say these explicitly)

These are the rules that must always hold:

1. `available + reserved + sold = total`
2. Never oversell.
3. Payment success implies ticket ownership.
4. Expired unpaid holds must be released.
5. Waitlist notification order is FIFO (or priority policy if specified).

If you say these, interviewer sees strong systems thinking immediately.

## 3) High-level components

```text
[Client App]
    |
    v
[API Gateway]
    |
    +--> [Virtual Queue Service] ----> admission tokens
    |
    +--> [Ticket Service] <----> [Inventory Store]
    |          |                     (atomic counters / seat records)
    |          |
    |          +--> [Reservation(Hold) Service]
    |          |
    |          +--> [Payment Orchestrator] <--> [Payment Provider]
    |          |
    |          +--> [Waitlist Service]
    |
    +--> [Notification Service]
```

Minimal component roles:

- Virtual Queue: absorb traffic burst and gate entry fairly.
- Reservation/Hold: time-bound reserve before payment.
- Payment Orchestrator: idempotent payment finalize.
- Waitlist: ordered fallback demand queue.
- Notification: inform waitlist users when offers become available.

## 4) User flows to walk through

## Flow A: Traffic spike / rush

1. User joins virtual waiting room.
2. System admits users in batches.
3. Only admitted users can attempt hold creation.
4. This prevents DB and payment meltdown from a thundering herd.

## Flow B: Checkout hold + timeout

1. User requests N tickets.
2. If available, create hold with expiry (e.g., 2 min).
3. Reserved tickets are removed from `available`.
4. If timeout before successful pay, hold expires and inventory returns.

## Flow C: Sold out behavior

1. If no inventory for requested quantity, return sold-out response.
2. Offer waitlist join CTA.
3. Waitlist captures user + desired quantity + timestamp/order.

## Flow D: Payment guarantee

1. Payment is attempted only for active hold.
2. Use idempotency key to avoid double charge/duplicate purchase.
3. On success, convert hold -> purchase (ticket is guaranteed).
4. On failure, release hold and optionally notify waitlist.

## Flow E: Waitlist backfill

1. Tickets return due to hold expiry, cancellation, or refund.
2. Waitlist is processed in order.
3. Top eligible user receives an offer hold with short expiry.
4. If they do not pay in time, next waitlist user is offered.

## 5) Data model (interview-level)

## EventInventory

- `event_id`
- `total_tickets`
- `available_tickets`
- `sold_tickets`

## Hold

- `hold_id`
- `event_id`
- `user_id`
- `quantity`
- `status` (`active/expired/released/converted`)
- `expires_at`

## Purchase

- `purchase_id`
- `hold_id`
- `user_id`
- `quantity`
- `payment_status`
- `idempotency_key`

## WaitlistEntry

- `seq` (ordering)
- `event_id`
- `user_id`
- `quantity`
- `joined_at`

## 6) API sketch (good to mention)

- `POST /queue/join`
- `POST /queue/admit` (admin/system)
- `POST /holds` (create hold)
- `POST /payments/confirm` (idempotent)
- `POST /holds/expire/process` (background sweep)
- `POST /waitlist/join`
- `POST /purchases/{id}/cancel`

## 7) Failure and edge case handling

1. Payment provider times out:
   - retry with same idempotency key
   - eventual reconciliation job
2. Client retries after success:
   - return same purchase via idempotency index
3. Race for last ticket:
   - atomic hold creation only if sufficient available
4. Waitlist quantity too large:
   - either partial fill policy or keep position until enough inventory

## 8) How to narrate tradeoffs

Say:

1. "This mock is in-memory for clarity and interview speed."
2. "Production would persist inventory/holds/waitlist in DB."
3. "Atomic updates would use DB transactions or Redis Lua scripts."
4. "Queue and notification pipelines would be async/event-driven."

## 9) How this folder's Python mock helps you

`mock_ticketmaster.py` demonstrates:

1. virtual queue admission
2. hold timeout behavior
3. sold-out and waitlist join
4. payment idempotency
5. waitlist offer generation on ticket release

Use it to rehearse explaining flows while reading code.

## 10) 2-minute interview answer template

You can say:

1. "I split the problem into admission, reservation, payment, and waitlist."
2. "Admission uses virtual queue to smooth spikes."
3. "Reservation creates expiring holds so unpaid tickets are reclaimed."
4. "Payment confirm is idempotent and converts active hold to purchase, guaranteeing paid users get tickets."
5. "On release/cancel, inventory is returned and waitlist is offered in FIFO order."
6. "Invariant is no oversell: available + reserved + sold always equals total."
