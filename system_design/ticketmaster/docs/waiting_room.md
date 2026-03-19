# Ticketmaster: The "Bruno Mars" Scenario (20M Users / 60k Seats)

This system design focuses on the **Virtual Waiting Room** and the **Gatekeeper Transition** logic, designed to protect the core database from a thundering herd of 20 million concurrent users.

## 1. The "Big Math" Justification

| Metric | Value | Rationale |
| :--- | :--- | :--- |
| **Total Inbound Requests** | 20,000,000 | The peak thundering herd at 10:00:00 AM. |
| **Request Payload** | ~1 KB | Standard HTTP headers + session cookies. |
| **Network Throughput** | 20 GB / 5s = **4 GB/s** | This requires a massive horizontal scale of stateless Ingress nodes. |
| **Redis Memory (Queue)** | 20M x 32B = **640 MB** | Memory is NOT the bottleneck; Network I/O is. |
| **Redis Write Load** | 2,000,000 ops/s | To handle this in 10s, we use **1,000 buckets** spread across a Redis Cluster. |
| **Polling Pressure** | 20M users @ 5s poll | **4,000,000 Requests/sec**. Only a CDN Edge can handle this. |

## 2. Core Components

### A. Ingress API (`ingress_api.py`)
- **Stateless Horizontal Scale:** Can be spawned into 1,000+ pods in K8s.
- **Bucketing:** Hashes `user_id` into one of 1,000 Redis ZSET buckets (e.g., `queue:bucket:452`).
- **Tokenization:** Returns a signed JWT containing the user's precise `joined_at` timestamp.

### B. The Gatekeeper (`gatekeeper_worker.py`)
- **Capacity Monitoring:** Polls the Main Room's capacity (active checkouts).
- **Fairness Draining:** Uses `ZPOPMIN` to pull 10 users from each of the 1,000 buckets in a round-robin cycle.
- **State Transition:** Moves admitted User IDs from the ZSET (Waiting) to a Global SET (Admitted).
- **CDN Push:** Updates the `Global Admitted Timestamp` in the CDN's KV store.

### C. The Edge Bouncer (`edge_bouncer.js`)
- **No-Origin Polling:** Intercepts 20M polls at the CDN level.
- **O(1) Decision:** Compares the user's JWT timestamp vs. the `Global Admitted Timestamp`.
- **Latency:** Microsecond response time; keeps 19.9M "waiters" entirely off our backend infrastructure.

## 3. The Lifecycle of a Request

1. **JOIN:** User hits `/join`. Ingress assigns them to `bucket:7` with `timestamp: 10:00:01.400`.
2. **WAIT:** User's browser polls `/poll`. The CDN Edge Worker sees the current `threshold` is `10:00:00.800`. User is told "WAIT."
3. **ADMIT:** Gatekeeper drains 1,000 people. The new `threshold` becomes `10:00:01.500`. This is pushed to the CDN KV.
4. **PASS:** On the next poll, the CDN Edge Worker sees `1.400 <= 1.500`. User is redirected to the **Seat Selection Map**.

## 4. Key Takeaway for Interviews
This design shifts the bottleneck from **Database Write Contention** (impossible at 20M) to **CDN-Level Read Offloading**. We only let in as many people as our transactional DB (PostgreSQL) can actually handle, ensuring the site never "crashes" even if 20M people are hammering it.
