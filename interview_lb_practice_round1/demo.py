from __future__ import annotations

from pprint import pprint
from time import sleep

from lightweight_lb import LightweightLoadBalancer, TaskPriority


def main() -> None:
    lb = LightweightLoadBalancer(heartbeat_timeout_s=5.0, default_lease_timeout_s=3.0)

    print("1) Register workers")
    lb.register_worker("worker-a", capacity=2)
    lb.register_worker("worker-b", capacity=1)
    pprint(lb.snapshot())

    print("\n2) Enqueue mixed-priority tasks")
    lb.enqueue_task({"job": "report"}, priority=TaskPriority.LOW)
    lb.enqueue_task({"job": "incident"}, priority=TaskPriority.CRITICAL)
    lb.enqueue_task({"job": "billing"}, priority=TaskPriority.HIGH)
    lb.enqueue_task({"job": "analytics"}, priority=TaskPriority.MEDIUM)
    pprint(lb.snapshot())

    print("\n3) Dispatch tasks")
    assignments = lb.dispatch(max_assignments=3)
    for a in assignments:
        print(
            f"assigned task={a.task_id} priority={a.priority.name} "
            f"attempt={a.attempt} -> worker={a.worker_id}"
        )
    pprint(lb.snapshot())

    print("\n4) Ack one success, one retryable failure")
    lb.ack(assignments[0].worker_id, assignments[0].task_id, success=True)
    lb.ack(
        assignments[1].worker_id,
        assignments[1].task_id,
        success=False,
        retryable=True,
        error="temporary downstream timeout",
    )
    pprint(lb.snapshot())

    print("\n5) Simulate worker-b heartbeat loss and failover")
    sleep(6)
    lb.heartbeat("worker-a")
    lb.tick()
    pprint(lb.snapshot())

    print("\n6) Dynamic worker join")
    lb.register_worker("worker-c", capacity=2)
    reassigned = lb.dispatch(max_assignments=10)
    for a in reassigned:
        print(f"reassigned task={a.task_id} -> worker={a.worker_id}")
    pprint(lb.snapshot())


if __name__ == "__main__":
    main()
