# Day 12 - Practical: Observability (Monitoring and Tracing)

Scale AI has 1,000 services. If "Task Creation" is slow, is it the Database? The Auth Service? The ML Model? This is a **Distributed Tracing** lesson.

## 1. The Scenario: The "Unknown Slowdown"
Scale AI's API for `POST /v1/tasks` is taking 2 seconds. The customer is angry. They want it under 200ms.

**The Complexity:** 
- **Many Services:** `API` -> `Auth` -> `Billing` -> `Task` -> `DB`.
- **Many Teams:** 10 teams own these services.
- **Many Environments:** It's slow in `production` but fast in `staging`.

---

## 2. The Solution: Distributed Tracing (OpenTelemetry)
We don't "guess." We use a `Trace ID` to see exactly where the time is being spent.

### The "Scale AI" Observability Strategy:
1.  **The Trace ID:** The Ingestor (API) generates a `UUID` and puts it in the `X-Trace-ID` header.
2.  **The Span:** Every service "Appends" its own data (e.g. `Auth start -> Auth end`).
3.  **The Export:** All services push their spans to a "Tracing Collector" (e.g. Jaeger or Honeycomb).

### What the Trace looks like:
- **`POST /tasks` (Total: 2000ms)**
  - `auth_check` (50ms)
  - `billing_check` (50ms)
  - `db_insert_task` (**1800ms**) <- **THE PROBLEM!**
  - `queue_publish` (100ms)

**Result:** We found the bottleneck in 5 seconds. It's the **Database**.

---

## 3. 🧠 Key Teaching Points:
*   **The "Slow DB" Bug**: 99% of the time, the problem is a **Missing Index** (Day 10 lesson!). A trace makes this obvious because the "DB Span" is much larger than the "Python Span."
*   **Log Correlation**: We don't just "Trace." We "Log with Trace ID." If we find a slow trace, we can search our logs for `TRACE_ID=123` to see the exact error or warning that happened during that request.
*   **Sampling**: At Scale, we don't trace 100% of requests (it's too expensive!). We might trace **1% of successes** and **100% of errors**. This is **Head-based Sampling**.
*   **Service Maps**: Modern observability tools (like Datadog) use traces to build a "Map" of every service in the company. This shows you "Who talks to whom."
*   **FDE Tip**: When an interviewer says "The API is intermittently slow," your first response should be: "I would check the **P99 Latency** and the **Distributed Traces** to see if the slowness is caused by a specific 'Cold Start' or a 'Slow Dependency'."
*   **Scale's Best Practice**: Always include the `Trace ID` in your HTTP response headers. This allows the customer to send you the ID when they report a bug!
