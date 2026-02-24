import asyncio
import time
import aiohttp
from typing import AsyncIterator, List, Optional
from .models import TestPlan, TestPhase, ApiTarget
from .metrics import MetricsRegistry

class PerformanceOrchestrator:
    def __init__(self, plan: TestPlan):
        self.plan = plan
        self.metrics = MetricsRegistry()
        # The Semaphore acts as our 'Memory Guard'
        self.sem = asyncio.Semaphore(plan.concurrency_limit)

    async def _fire_request(self, session: aiohttp.ClientSession, target: ApiTarget, track: bool):
        """
        Executes a single request. 
        The semaphore is handled by the caller to keep logic clean.
        """
        start = time.time()
        is_error = False
        try:
            async with session.request(target.method, target.url, json=target.payload) as response:
                await response.read()
                if response.status >= 400:
                    is_error = True
        except Exception:
            is_error = True
        finally:
            if track:
                duration_ms = (time.time() - start) * 1000
                self.metrics.record(duration_ms, is_error)

    async def _request_generator(self, phase: TestPhase) -> AsyncIterator[ApiTarget]:
        """
        A memory-efficient generator that yields which target to call next.
        Handles 'round_robin' vs 'sequential_batch'.
        """
        if phase.mode == "sequential_batch":
            # Mode: Finish all of A, then all of B
            for target in phase.targets:
                count = target.total_requests or (target.rps * (phase.duration_sec or 1))
                print(f"  [GEN] Preparing batch of {count} for {target.name}")
                for _ in range(count):
                    yield target
        
        else: # Round Robin
            # Mode: Interleave A, B, A, B...
            # We use a simple while loop based on time or total count
            start_time = time.time()
            total_yielded = 0
            max_to_yield = phase.total_requests or float('inf')
            
            while total_yielded < max_to_yield:
                # Check duration if applicable
                if phase.duration_sec and (time.time() - start_time) > phase.duration_sec:
                    break
                
                # Yield one from each target in this 'tick'
                for target in phase.targets:
                    yield target
                    total_yielded += 1
                    
                # To maintain RPS, we need to pace the generator
                # (Simplified: logic for high-precision RPS pacing goes here)
                await asyncio.sleep(1 / sum(t.rps for t in phase.targets))

    async def _run_phase(self, session: aiohttp.ClientSession, phase: TestPhase):
        print(f"\n>>> PHASE START: {phase.name}")
        
        # We use a list to track active tasks, but we prune it constantly!
        active_tasks = set()
        
        async for target in self._request_generator(phase):
            # 1. Backpressure: Wait for a slot in the semaphore
            await self.sem.acquire()
            
            # 2. Spawn the task
            task = asyncio.create_task(self._fire_request(session, target, phase.track_metrics))
            active_tasks.add(task)
            
            # 3. Memory Cleanup: Remove finished tasks from our set
            # We add a callback to the task to remove itself when done
            def cleanup(t):
                active_tasks.discard(t)
                self.sem.release() # Release slot back to the pool
            
            task.add_done_callback(cleanup)

            # 4. Critical: Yield control to the loop so tasks can actually run
            if len(active_tasks) >= self.plan.concurrency_limit:
                # If we are at the limit, wait until at least one task finishes
                await asyncio.sleep(0.01)

        # Final Drain: Wait for the last few tasks of this phase
        if active_tasks:
            print(f"  [PHASE] Draining {len(active_tasks)} remaining tasks...")
            await asyncio.gather(*active_tasks, return_exceptions=True)
        
        print(f">>> PHASE COMPLETE: {phase.name}")

    async def run_plan(self):
        print(f"=== PROJECT: {self.plan.project_name} ===")
        # Keep-alive session
        async with aiohttp.ClientSession() as session:
            for phase in self.plan.phases:
                await self._run_phase(session, phase)
        
        return self.metrics.snapshot()
