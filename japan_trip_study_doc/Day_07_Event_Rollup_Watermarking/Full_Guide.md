# Day 07: Event Rollup & Watermarking
**Focus:** Processing high-volume data streams (like Scale's task event logs) with accuracy.

## 01. The Problem: "The Late Arrival"
**Scenario:** Scale AI receives 10,000 "Task Completed" events per second. You need to calculate "Tasks Completed per Minute" for a real-time dashboard.

**The Complexity:** 
- **Network Latency:** An event that happened at **12:00:59** might not reach your server until **12:01:05** due to a slow mobile connection. 
- **Duplicates:** If the user's internet flickers, their phone might send the same "Task Completed" event twice.
- **Out of Order:** Event B (12:01:00) might arrive *before* Event A (12:00:55).

If you just count events as they arrive, your "12:00" bucket will be wrong because you missed the late Event A.

---

## 02. The Solution: Deduplication + Watermarking
To solve this, we don't just "count." We build a **State Machine** for time.

1. **Global Dedupe:** Keep a set of `seen_event_ids`. If an ID comes again, ignore it.
2. **Event-Time Bucketing:** Group events by their **actual occurrence time**, not when they arrived.
3. **The Watermark:** This is a "clock" that lags behind the latest event. 
   - `watermark = max_event_time_seen - allowed_lateness`
   - If `allowed_lateness` is 10 seconds, and we just saw an event from **12:01:00**, our watermark is **12:00:50**.
   - **The Rule:** We only "finalize" (emit) a minute bucket once the watermark has passed the end of that minute.

---

## 03. The Working Code (Python Stream Processor)
This is a "Solution" that implements a production-grade rollup.

```python
from collections import defaultdict
from typing import List, Dict, Any

def process_event_stream(events: List[Dict[str, Any]], lateness_threshold: int):
    """
    events: List of {'id': str, 'timestamp': int, 'type': str}
    lateness_threshold: How many seconds to wait for late data.
    """
    seen_ids = set()
    buckets = defaultdict(int) # (minute_start, type) -> count
    finalized_results = []
    
    max_ts = 0
    open_minutes = set()
    finalized_minutes = set()
    late_drops = 0

    for event in events:
        # 1. Deduplication
        if event['id'] in seen_ids:
            continue
        seen_ids.add(event['id'])

        # 2. Update High Watermark
        ts = event['timestamp']
        max_ts = max(max_ts, ts)
        watermark = max_ts - lateness_threshold

        # 3. Assign to Minute Bucket
        minute_start = ts - (ts % 60)
        
        # 4. Handle "Too Late" Data
        if minute_start in finalized_minutes:
            late_drops += 1
            continue
        
        # 5. Aggregate
        buckets[(minute_start, event['type'])] += 1
        open_minutes.add(minute_start)

        # 6. Finalize Buckets
        # A minute [M, M+60) is ready if watermark >= M + 60
        ready_to_close = [m for m in open_minutes if watermark >= m + 60]
        
        for m in sorted(ready_to_close):
            # Extract all types for this minute
            for (b_min, b_type), count in list(buckets.items()):
                if b_min == m:
                    finalized_results.append({
                        "minute": m,
                        "type": b_type,
                        "count": count
                    })
                    del buckets[(b_min, b_type)]
            
            open_minutes.remove(m)
            finalized_minutes.add(m)

    return {
        "data": finalized_results,
        "dropped_late_count": late_drops
    }

# --- TEST CASE ---
events = [
    {"id": "A", "timestamp": 100, "type": "click"}, # Min 60
    {"id": "B", "timestamp": 110, "type": "click"}, # Min 60
    {"id": "C", "timestamp": 170, "type": "click"}, # Min 120 (Max=170, Watermark=140 if lateness=30)
    # Watermark 140 is > Min 60 + 60 (120), so Min 60 FINALIZES here.
    {"id": "D", "timestamp": 105, "type": "click"}, # ARRIVES LATE. Min 60 is finalized. DROP!
]
result = process_event_stream(events, lateness_threshold=30)
print(result)
```

---

## 04. Architectural Tradeoffs: How to Ace the Interview

### Q: Why not just use `arrival_time`? It's much simpler.
**A:** "Because `arrival_time` is a lie. If a batch of events is delayed by a network partition, `arrival_time` would put them all in the 'current' minute, creating a massive spike in the dashboard that never actually happened. **Event-time** is the only way to get a truthful representation of the world."

### Q: How do you choose the `lateness_threshold`?
**A:** "It's a tradeoff between **Latency** and **Accuracy**. 
- A **long threshold** (e.g., 5 mins) means we catch almost all late data, but our dashboard is 5 minutes behind real-time.
- A **short threshold** (e.g., 5 secs) means the dashboard is 'snappy', but we drop more late events. 
At Scale, we might use a short threshold for 'live' charts and a long threshold for 'final' billing."

### Q: What happens to the `seen_ids` set? Does it grow forever?
**A:** "In a real production system, yes, that's a memory leak. I would use a **Bloom Filter** for probabilistic deduping or a **TTL-based Redis set** to only keep IDs for the last hour, assuming events won't be more than an hour late."
