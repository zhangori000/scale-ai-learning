import time
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass

class RedisPipeline:
    """
    Simulates a Redis Pipeline for batching multiple ZPOPMIN calls.
    Reduces network overhead from 1,000 round-trips to 1 or 2.
    """
    def __init__(self):
        self.commands = []

    def zpopmin(self, key: str, count: int):
        self.commands.append(("zpopmin", key, count))

    def zrange_withscores(self, key: str, start: int, end: int):
        self.commands.append(("zrange", key, start, end))

    def execute(self) -> List:
        # Simulation: returns mock results for each command.
        # This is a critical performance optimization in real Redis usage.
        return [([("user_id", time.time_ns())]) for _ in range(len(self.commands))]

class RedisClient:
    def pipeline(self) -> RedisPipeline:
        return RedisPipeline()

    def sadd(self, key: str, *members: str):
        pass

@dataclass
class GatekeeperConfig:
    total_buckets: int = 1000
    batch_size_per_bucket: int = 5
    poll_interval_seconds: float = 1.0
    event_id: str = "bruno_mars_2026"

class GatekeeperWorker:
    """
    The Gatekeeper drains the 'Waiting Room' and updates the 'Global Watermark'
    to allow users at the Edge to advance.
    """
    def __init__(self, config: GatekeeperConfig, redis: RedisClient, cdn_kv):
        self.config = config
        self.redis = redis
        self.cdn_kv = cdn_kv
        self.global_watermark: int = 0

    def process_one_cycle(self):
        # 1. BATCHED DRAINING (The Pipeline)
        # Instead of 1,000 individual network calls, we build a pipeline.
        pipe = self.redis.pipeline()
        for b_id in range(self.config.total_buckets):
            key = f"queue:{self.config.event_id}:bucket:{b_id}"
            pipe.zpopmin(key, self.config.batch_size_per_bucket)
        
        # 2. EXECUTE ALL (One Network Round-trip)
        raw_results = pipe.execute()
        
        admitted_users = []
        for bucket_results in raw_results:
            for user_id, timestamp in bucket_results:
                admitted_users.append(user_id)

        # 3. GLOBAL WATERMARK CALCULATION
        # To be STRICTLY fair, the threshold must be the MINIMUM of the 
        # EARLIEST timestamp remaining across all buckets.
        # This guarantees that ANY user with a timestamp <= watermark 
        # has definitely been processed.
        
        check_pipe = self.redis.pipeline()
        for b_id in range(self.config.total_buckets):
            key = f"queue:{self.config.event_id}:bucket:{b_id}"
            # ZRANGE bucket 0 0: peek at the very first (earliest) person in the bucket.
            check_pipe.zrange_withscores(key, 0, 0)
        
        remaining_heads = check_pipe.execute()
        
        # The watermark is the minimum of the head of every bucket.
        # (Mock handles case where a bucket might be empty)
        earliest_timestamps = [res[0][1] for res in remaining_heads if res]
        
        if earliest_timestamps:
            new_watermark = min(earliest_timestamps)
            if new_watermark > self.global_watermark:
                self.global_watermark = new_watermark
                # 4. PUSH TO CDN: Update the 'Admission Threshold'
                self.cdn_kv.put(f"threshold:{self.config.event_id}", self.global_watermark)
                logging.info(f"New Watermark: {self.global_watermark} (nanoseconds)")

        if admitted_users:
            # Move users to the active shoppers list in the main Redis.
            self.redis.sadd(f"active:{self.config.event_id}", *admitted_users)

    def run_forever(self):
        while True:
            self.process_one_cycle()
            time.sleep(self.config.poll_interval_seconds)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Mocking CDN KV for testing
    class MockKV: 
        def put(self, k, v): pass
    
    worker = GatekeeperWorker(GatekeeperConfig(), RedisClient(), MockKV())
    worker.process_one_cycle()
