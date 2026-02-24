import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class MetricSnapshot:
    count: int
    errors: int
    p50: float
    p95: float
    p99: float
    min_lat: float
    max_lat: float

class MetricsRegistry:
    def __init__(self):
        # We store raw latencies in a list. 
        # In production, use HdrHistogram (e.g., 'hdrpy') to save memory!
        self.latencies: List[float] = []
        self.errors: int = 0
        self.start_time = time.time()

    def record(self, latency_ms: float, is_error: bool = False):
        if is_error:
            self.errors += 1
        else:
            self.latencies.append(latency_ms)

    def snapshot(self) -> MetricSnapshot:
        """
        Calculates stats and returns a snapshot.
        WARNING: Sorting a large list is slow. In prod, use HdrHistogram.
        """
        count = len(self.latencies)
        if count == 0:
            return MetricSnapshot(0, self.errors, 0, 0, 0, 0, 0)

        # Sort to find percentiles
        sorted_lat = sorted(self.latencies)
        return MetricSnapshot(
            count=count,
            errors=self.errors,
            p50=sorted_lat[int(count * 0.50)],
            p95=sorted_lat[int(count * 0.95)],
            p99=sorted_lat[int(count * 0.99)],
            min_lat=sorted_lat[0],
            max_lat=sorted_lat[-1]
        )

    def reset(self):
        self.latencies = []
        self.errors = 0
        self.start_time = time.time()
