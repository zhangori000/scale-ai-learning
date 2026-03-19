# Ticketmaster System Architecture

This project implements a high-scale, distributed ticket booking system capable of handling 20M+ concurrent users (the "Bruno Mars" scenario).

## System Flow (The Lifecycle of a Ticket)

1. **Phase 1: Traffic Absorption (Waiting Room)**
   - **Ingress:** Stateless API sharding users into Redis buckets.
   - **Edge Bouncing:** CDN-level filtering to offload 99% of polling traffic.
   - **Gatekeeper:** Central orchestrator draining the waiting room into the active shopper set.

2. **Phase 2: Real-time Contention (Seat Selection)**
   - **Map Service:** Highly-cached (Redis) seat status (Free, Locked, Sold).
   - **Locking:** Distributed Redis locks (with TTL) to prevent double-booking.
   - **Concurrency:** Optimistic concurrency control (OCC) to ensure ACID compliance during state transitions.

3. **Phase 3: Checkout & Fulfillment (Orders)**
   - **Payment Bridge:** Asynchronous integration with payment gateways (Stripe/PayPal).
   - **Transactional DB:** PostgreSQL for final ownership and financial audits.
   - **Notification:** Webhooks to notify users of successful purchases.

## Current Progress
- [x] **Waiting Room Module:** Redis-sharded ZSETs, Gatekeeper, and Edge Bouncing logic.
- [ ] **Seat Selection Module:** Distributed locking and map state synchronization.
- [ ] **Ordering Module:** ACID-compliant checkout flows.
- [ ] **Search Module:** Elasticsearch-backed venue/event lookup.
