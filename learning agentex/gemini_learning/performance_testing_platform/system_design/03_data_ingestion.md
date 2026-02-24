# Chapter 3: Data Ingestion & Metrics (The "Firehose")

When you run 10,000 RPS, you are generating 10,000 data points per second.
*   **Latency:** `23ms`
*   **Status:** `200`
*   **Size:** `1.2kb`

## 1. The "Log to File" Trap
**Do NOT** verify performance by writing every request to a log file (`logging.info(...)`).
*   **Disk I/O Blocking:** Writing to disk is slow. You will slow down your load generator ("Coordinated Omission"), making the server look slower than it is.
*   **Size:** 1M requests = 100MB of logs per minute.

## 2. The Solution: In-Memory Aggregation
Instead of saving every number, we save a **Histogram**.
*   **Buckets:** Count how many requests took 0-10ms, 10-20ms, 20-30ms...
*   **HdrHistogram:** A specialized data structure that records values with high precision (e.g., 3 significant digits) using very little memory. It can tell you the P99.99 latency without storing all the raw numbers.

## 3. The Metrics Pipeline
1.  **Worker Node:**
    *   Maintains a local `HdrHistogram`.
    *   Every 1 second, it "Snapshots" the histogram and resets it.
    *   Sends the snapshot (a binary blob or JSON summary) to the Aggregator.
2.  **Aggregator (Central Service):**
    *   Receives snapshots from 50 workers.
    *   **Merges** the histograms (Histogram math allows adding!).
    *   Writes the *merged* result to a Time-Series DB (Prometheus/InfluxDB).

## 4. Why P99 matters?
*   **Average (Mean):** Useless. If 99 requests take 1ms and 1 takes 10s, average is ~100ms. It hides the disaster.
*   **P99 (99th Percentile):** "99% of my users saw a response faster than X." This catches the outliers.

## 5. Handling "Provisioning" Metrics
The architecture must support **Tags** or **Phases**.
*   Request A: `{"phase": "setup", "endpoint": "/login", "latency": 500}` -> **Discard or Separate Dashboard**.
*   Request B: `{"phase": "run", "endpoint": "/api/data", "latency": 20}` -> **Main Dashboard**.
