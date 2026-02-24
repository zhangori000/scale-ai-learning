# Chapter 1: Requirements & High-Level Architecture

## 1. The Core Problem
Performance testing is not just "spamming an endpoint." It is a scientific experiment.
*   **Variable Control:** We need to precisely control the *Rate* (RPS) and *Volume* (Concurrency).
*   **Orchestration:** Tests often have phases: "Warm-up" -> "Sustain" -> "Spike" -> "Cool-down".
*   **State:** A test might need to "Login" (Step A) before it can "Buy Item" (Step B). We only care about the latency of Step B, but Step A is required to get there.

## 2. Functional Requirements
1.  **Configurable Load:** Users define `RPS`, `Duration`, `Ramp-up Time`.
2.  **Multi-Step Workflows:** Support `setup` (provisioning) and `teardown` phases.
3.  **Metrics Isolation:** Ability to ignore metrics from the `provision` step.
4.  **Concurrency Control:** Manage thread pools to avoid "Coordinated Omission" (where the test client becomes the bottleneck).

## 3. High-Level Architecture (The "Bird's Eye View")

```text
[User UI] -> [Control Plane API] -> [Job Queue (Redis)]
                                        |
                                        v
                                 [Worker Nodes]
                                (The Load Generators)
                                        |
                                        v
                                 [Target System]
```

### The Components
1.  **Control Plane (The Brain):** Accepts test configs (YAML/JSON), validates them, and splits them into "Job Shards."
2.  **Worker Nodes (The Muscle):** Stateless containers that pull a "Shard" (e.g., "Generate 500 RPS for 5 mins") and execute it.
3.  **Metrics Ingestor (The Scribe):** A high-throughput stream (Kafka/Redpanda) that receives raw latency data from workers.
4.  **Aggregator (The Analyst):** A time-series DB (Prometheus/Timescale) that computes P99, P95, and Error Rates.

## 4. Key Design Decisions
*   **Why not just one big script?** A single machine runs out of CPU/Network ports at around 10k-50k RPS. To hit 1M RPS, you need **Distributed Load Generation**.
*   **Push vs. Pull:**
    *   *Push (Gatling/Locust):* Workers try to send requests as fast as possible.
    *   *Open System:* Requests are generated at a fixed rate, regardless of server response time. This is more realistic for API testing.
