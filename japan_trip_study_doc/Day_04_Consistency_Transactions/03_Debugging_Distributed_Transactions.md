# Day 04 - System/Debug: Distributed Transactions (Saga Pattern)

How do you handle a "Labeling Pipeline" that spans three different services? This is a **Distributed Coordination** lesson.

## 1. The Scenario
Scale AI has three services:
1. **Billing Service:** Deducts credits from the user's account.
2. **Task Service:** Creates the labeling tasks.
3. **Notify Service:** Sends an email to the user.

**The Problem:** You cannot use a single SQL Transaction because these are three different databases. This is a **Distributed Transaction**.

## 2. The Solution: The Saga Pattern (Compensating Transactions)
A Saga is a sequence of local transactions. Each service does its work and tells the next service to start. If something fails, the previous services must **Undo** their work.

### The "Labeling Saga" Flow:
1.  **Step 1:** Billing Service reserves $100 (Status: `RESERVED`).
2.  **Step 2:** Task Service tries to create 1,000 tasks. **CRASH!** (The disk is full).
3.  **The Compensation:** The "Saga Manager" sees the failure and tells the Billing Service to `RELEASE_RESERVATION`.

### Why this is the ONLY way:
In a 2,000-person engineering org like Scale, you can't have "Distributed Locks" (which are slow and fragile). Sagas use **Events** and **Compensation** to maintain "Eventual Consistency."

## 3. Interview Dialogue: How to discuss Sagas

### Q: "Why not use Two-Phase Commit (2PC)?"
**A:** "2PC is a 'Blocking' protocol. If one service is slow, the entire cluster freezes. In a high-volume system like Scale AI, we prioritize **Availability** over **Immediate Consistency**. Sagas allow each service to commit its own data quickly and handle failures 'after the fact'."

### Q: "What happens if the 'Compensation' itself fails?"
**A:** "This is the 'Long-tail' of distributed systems. We use **Retries** and **Alerting**. If the Billing Service fails to release a reservation, we keep retrying with 'Exponential Backoff'. If it fails for 24 hours, an FDE (Forward Deployed Engineer) like me gets a PagerDuty alert to fix it manually."

### Q: "How do you track the state of a Saga?"
**A:** "I would use a **State Machine**. We store the 'Saga ID' in a database and track `STEP_1_COMPLETE`, `STEP_2_FAILED`, `COMPENSATION_SENT`. Systems like **Temporal.io** (which Scale uses heavily) are designed specifically to manage these state machines durably across crashes."

---

## 4. 🧠 Key Teaching Points:
*   **Compensating Transaction**: This is an "Undo" operation (e.g., a Refund for a Payment).
*   **Choreography vs. Orchestration**: 
    *   **Choreography**: Each service knows what to do next (Service A emits event -> Service B listens).
    *   **Orchestration**: A central "Brain" tells everyone what to do. At Scale, **Orchestration** is usually preferred for complex workflows.
*   **Observability**: Sagas are impossible to debug without **Distributed Tracing** (e.g., OpenTelemetry). You need a single `request_id` that you can trace across all three services to see where the saga died.
