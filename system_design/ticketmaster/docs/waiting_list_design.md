# The Post-Sell-Out Waiting List (Post-Contention Orchestration)

While the initial sale is about **Milliseconds (Redis)**, the waiting list is about **Stability and Durability (Postgres + Kafka)**.

## 1. The Inventory Pipeline (Kafka)

We decouple the "Seat Opening" (Refund, Expiry, or Payment Failure) from the "Notification" using a Message Queue (Kafka).

1. **Trigger:** A seat status changes in the `seats` table (SQL) to `AVAILABLE`.
2. **Event:** A message is published to the `inventory_available` Kafka topic.
3. **Consumption:** The `WaitingListService` consumes the message and identifies the next user in line using `SELECT ... FOR UPDATE SKIP LOCKED` to ensure no two workers offer the same seat to different users.

## 2. The 24-Hour Offer Flow

| Step | Component | Action |
| :--- | :--- | :--- |
| **A. Reserve** | PostgreSQL | Update user status to `OFFERED` and map the `seat_id`. |
| **B. Lock** | Redis | Set a 24-hour `seat_lock` to keep it off the public map. |
| **C. Notify** | External API | Send Email (SendGrid) and SMS (Twilio) with a signed claim link. |
| **D. Claim** | SeatService | User follows link and enters a **Private Checkout**. |

## 3. Resilience: The "Three Worker" Pattern

To ensure the system is "Anti-Fragile," we use three separate background processes:

1. **The Primary Worker (Happy Path):** Consumes Kafka messages and sends offers immediately.
2. **The Sweep Cron (Expiry):** Runs every minute to reclaim seats from users who didn't claim their 24h offer.
3. **The Reconciliation Worker (Sanity Check):** Scans for "Limbo" states (e.g. a seat is `AVAILABLE` but no offer was sent). It fixes inconsistencies across the Distributed System (Postgres vs. Redis vs. Notifications).

## 4. Product-First UX: Payment Retries & CS Holds

We avoid "Ripping seats away" from loyal fans.

- **PAYMENT_RETRY State:** If a card fails, the user gets 30 minutes to fix it. The seat remains `LOCKED` for them.
- **CS_HOLD State:** A Customer Service agent can manually pause the expiry clock while investigating a dispute, preventing the automated system from releasing the seat mid-conversation.
