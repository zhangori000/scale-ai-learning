# Chapter 4: Distributed Orchestration (The "General")

To simulate 1 million users, you need 50 servers. How do you control them?

## 1. The Controller Pattern
*   **The Controller:** The single source of truth. It holds the "Test Plan."
*   **The Agents:** Dumb workers that listen for orders.

## 2. Sharding the Load
User wants: `Total RPS = 10,000`.
We have `5 Workers`.
*   **Naive Sharding:** Each worker gets `2,000 RPS`.
*   **Dynamic Sharding:** What if Worker 3 is slow? The controller needs to monitor "Actual RPS" and tell Worker 4 to speed up. (Complex, usually Phase 2 feature).

## 3. Synchronization (The "Go" Signal)
If Worker A starts at 12:00:00 and Worker B starts at 12:00:05, your "Ramp Up" curve will be wrong.
*   **Barrier Synchronization:**
    1.  Controller sends "Prepare Job X" to all workers.
    2.  Workers initialize threads/connections and reply "Ready".
    3.  Controller waits for 100% Ready.
    4.  Controller sends "START at 12:00:10 UTC".
    5.  Workers sleep until exactly that timestamp.

## 4. Failure Handling
*   **Worker Death:** If a worker crashes, the Controller detects a heartbeat loss.
    *   *Option A:* Fail the test (Strict).
    *   *Option B:* Re-distribute the load to remaining workers (Resilient).
*   **Target Death:** If the target returns 503s, workers should NOT stop (unless error rate > threshold). We are *testing* failure, after all.

---

# Summary of Design
We have built a system that is:
1.  **Precise:** Uses AsyncIO and Scheduled Ticks.
2.  **Scalable:** Uses Distributed Workers and Aggregated Histograms.
3.  **Clean:** Separates "Setup" noise from "Test" signal.
4.  **Resilient:** Handles concurrency limits to prevent self-DOS.

Next, we will code the **Worker Node** (The Engine) in Python.
