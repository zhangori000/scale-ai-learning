import asyncio
import time
import aiohttp
from typing import Callable, Optional
from .metrics import MetricsRegistry

class LoadGenerator:
    def __init__(self, target_url: str, rps: int, duration_sec: int, concurrency_limit: int = 100):
        self.target_url = target_url
        self.rps = rps
        self.duration_sec = duration_sec
        self.metrics = MetricsRegistry()
        
        # KEY ARCHITECTURAL COMPONENT: The Semaphore
        # This prevents us from spawning 10,000 tasks if the server hangs.
        # If the semaphore is full, the 'tick' loop will wait before firing new requests.
        self.sem = asyncio.Semaphore(concurrency_limit)

    async def _make_request(self, session: aiohttp.ClientSession, request_id: int):
        """
        The actual worker task.
        """
        async with self.sem: # Acquire a slot. If full, we wait here.
            start = time.time()
            is_error = False
            try:
                async with session.get(self.target_url) as response:
                    # We must read the body to ensure the request completes
                    await response.read()
                    if response.status >= 400:
                        is_error = True
            except Exception as e:
                is_error = True
            finally:
                duration_ms = (time.time() - start) * 1000
                self.metrics.record(duration_ms, is_error)

    async def run(self):
        print(f"--- STARTING LOAD TEST: {self.rps} RPS for {self.duration_sec}s ---")
        
        # We reuse one session for connection pooling (Keep-Alive)
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            tasks = []
            request_count = 0
            
            # The "Tick" Loop
            # We calculate exactly when the next batch should fire.
            while (time.time() - start_time) < self.duration_sec:
                loop_start = time.time()
                
                # Fire a batch of requests for this second
                # (For higher precision, we could tick every 100ms)
                for _ in range(self.rps):
                    # Fire and forget (don't await _make_request immediately)
                    # The Semaphore inside _make_request handles the backpressure.
                    task = asyncio.create_task(self._make_request(session, request_count))
                    tasks.append(task)
                    request_count += 1
                
                # Sleep for the remainder of the second
                elapsed = time.time() - loop_start
                sleep_time = max(0, 1.0 - elapsed)
                await asyncio.sleep(sleep_time)
                
                # Periodic log
                print(f"  [TICK] Time: {int(time.time() - start_time)}s | Active Tasks: {len([t for t in tasks if not t.done()])}")

            # Wait for trailing tasks to finish (Drain)
            print("--- DRAINING REMAINING TASKS ---")
            await asyncio.gather(*tasks, return_exceptions=True)
            
        print("--- TEST COMPLETE ---")
        return self.metrics.snapshot()
