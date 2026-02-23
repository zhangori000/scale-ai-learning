# Day 13 - Practical: FDE Case Study (The Full Implementation)

As an FDE, you'll be asked to build a "System" from scratch in 60 minutes. This is a **System Architecture** lesson.

## 1. The Scenario: The "Real-Time Labeling Monitor"
Scale AI's customer (e.g., Tesla) wants a dashboard that shows:
1.  **Current Stats:** How many tasks are "Completed" vs. "Pending"?
2.  **Top Labelers:** Who are the fastest 10 workers?
3.  **Real-Time:** The dashboard must update every **1 second**.

**The Constraints:**
- **Scale:** 10,000,000 tasks total.
- **Latency:** Must load in < 200ms.
- **Accuracy:** Must be 100% correct.

---

## 2. The Solution: The "Read-Optimized" Hybrid Design
You CANNOT query 10,000,000 rows every 1 second. You need **Materialized Views** and **Caching**.

### The "Scale AI" System Design:
1.  **The Writer (API):** Every time a task is completed, it updates the `tasks` table AND pushes an event to `Kafka`.
2.  **The Processor (Spark/Flink):** Reads Kafka and updates a **Redis Counter** (`completed_count`) and a **Redis Sorted Set** (`worker_leaderboard`).
3.  **The Reader (FastAPI):** When the dashboard loads, it doesn't query Postgres! It just queries **Redis**.

**Result:** The dashboard loads in **10ms** because it's just reading two numbers from memory.

---

## 3. 🧠 Key Teaching Points:
*   **The "Write-Through" Cache**: This is the pattern of updating the DB and the Cache at the same time. It's fast, but you must handle **Partial Failures** (Day 04 lesson!).
*   **Redis Sorted Sets (`ZADD`)**: This is the "Secret Superpower" for leaderboards. You can store 1,000,000 workers and their scores, and Redis can give you the "Top 10" in **O(log N)** time. This is 1,000x faster than a SQL `ORDER BY`.
*   **CQRS (Command Query Responsibility Segregation)**: This is a fancy way to say "Use different databases for Writing and Reading." Use **Postgres for Writing** (Truth) and **Redis for Reading** (Speed).
*   **FDE Tip**: When an interviewer says "Design a Real-Time Dashboard," your first response should be: "I would use **Materialized Aggregates in Redis** to avoid hitting the Primary Database."
*   **Scale's Best Practice**: For 99% of "Stats," don't query the source of truth. Query a **Pre-calculated Summary**.
*   **The "Recompute" Policy**: What if Redis dies? You MUST have a way to "Re-scan" the Postgres table and rebuild the Redis counters. This is a "Batch-to-Realtime" hybrid.
*   **The "Consistency" Lesson**: If a task is deleted from Postgres, you must also delete it from Redis. Use the **Transactional Outbox** (Day 04) to ensure both happen.
