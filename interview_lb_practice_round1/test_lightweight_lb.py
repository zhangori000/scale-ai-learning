from __future__ import annotations

import unittest

from lightweight_lb import LightweightLoadBalancer, TaskPriority, WorkerStatus


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self._t = start

    def __call__(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


class LightweightLoadBalancerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.lb = LightweightLoadBalancer(
            heartbeat_timeout_s=5.0,
            default_lease_timeout_s=2.0,
            clock=self.clock,
        )

    def test_priority_dispatch_order(self) -> None:
        self.lb.register_worker("w1", capacity=1)

        low = self.lb.enqueue_task({"name": "low"}, priority=TaskPriority.LOW)
        high = self.lb.enqueue_task({"name": "high"}, priority=TaskPriority.HIGH)
        critical = self.lb.enqueue_task({"name": "critical"}, priority=TaskPriority.CRITICAL)

        a1 = self.lb.dispatch(max_assignments=1)[0]
        self.assertEqual(a1.task_id, critical)
        self.lb.ack("w1", critical, success=True)

        a2 = self.lb.dispatch(max_assignments=1)[0]
        self.assertEqual(a2.task_id, high)
        self.lb.ack("w1", high, success=True)

        a3 = self.lb.dispatch(max_assignments=1)[0]
        self.assertEqual(a3.task_id, low)
        self.lb.ack("w1", low, success=True)

    def test_worker_state_active_overloaded_lost(self) -> None:
        self.lb.register_worker("w1", capacity=1)
        self.lb.enqueue_task({"id": 1}, priority=TaskPriority.MEDIUM)

        assignment = self.lb.dispatch(max_assignments=1)[0]
        self.assertEqual(assignment.worker_id, "w1")
        snap = self.lb.snapshot()
        self.assertEqual(snap["workers"]["w1"]["status"], WorkerStatus.OVERLOADED.value)

        self.lb.ack("w1", assignment.task_id, success=True)
        snap = self.lb.snapshot()
        self.assertEqual(snap["workers"]["w1"]["status"], WorkerStatus.ACTIVE.value)

        self.clock.advance(6.0)
        self.lb.tick()
        snap = self.lb.snapshot()
        self.assertEqual(snap["workers"]["w1"]["status"], WorkerStatus.LOST.value)

    def test_failover_when_worker_lost(self) -> None:
        self.lb.register_worker("w1", capacity=1)
        self.lb.register_worker("w2", capacity=1)
        task_id = self.lb.enqueue_task({"job": "A"}, priority=TaskPriority.HIGH)

        a1 = self.lb.dispatch(max_assignments=1)[0]
        self.assertIn(a1.worker_id, {"w1", "w2"})

        # Simulate only one worker becoming lost.
        lost_worker = a1.worker_id
        healthy_worker = "w2" if lost_worker == "w1" else "w1"
        self.clock.advance(6.0)
        self.lb.heartbeat(healthy_worker)
        self.lb.tick()

        # Re-dispatch reclaimed task to healthy worker.
        a2 = self.lb.dispatch(max_assignments=1)[0]
        self.assertEqual(a2.task_id, task_id)
        self.assertEqual(a2.worker_id, healthy_worker)

    def test_dynamic_worker_join_unblocks_queue(self) -> None:
        # No workers initially, task stays pending.
        self.lb.enqueue_task({"job": "A"}, priority=TaskPriority.HIGH)
        self.assertEqual(self.lb.dispatch(max_assignments=5), [])

        # Worker joins later and can take pending work.
        self.lb.register_worker("late-worker", capacity=2)
        assignments = self.lb.dispatch(max_assignments=5)
        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0].worker_id, "late-worker")

    def test_lease_timeout_requeues_task(self) -> None:
        self.lb.register_worker("w1", capacity=1)
        self.lb.register_worker("w2", capacity=1)
        task_id = self.lb.enqueue_task(
            {"job": "timeout"},
            priority=TaskPriority.MEDIUM,
            max_retries=1,
            lease_timeout_s=1.0,
        )

        first = self.lb.dispatch(max_assignments=1)[0]
        self.assertEqual(first.task_id, task_id)

        # No ack. Lease expires.
        self.clock.advance(1.5)
        self.lb.heartbeat("w1")
        self.lb.heartbeat("w2")
        self.lb.tick()

        second = self.lb.dispatch(max_assignments=1)[0]
        self.assertEqual(second.task_id, task_id)


if __name__ == "__main__":
    unittest.main()
