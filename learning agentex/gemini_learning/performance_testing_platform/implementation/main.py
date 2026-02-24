import asyncio
from src.engine.models import TestPlan, TestPhase, ApiTarget
from src.engine.orchestrator import PerformanceOrchestrator

async def main():
    # Example: A high-volume test plan
    plan = TestPlan(
        project_name="High_Volume_Demo",
        concurrency_limit=100,
        phases=[
            # 1. Provisioning: Run 10 sequential setup calls (no metrics)
            TestPhase(
                name="Provision_Batch",
                type="provisioning",
                mode="sequential_batch",
                track_metrics=False,
                targets=[
                    ApiTarget(name="Auth", url="https://httpbin.org/get", total_requests=10)
                ]
            ),
            # 2. Execution: Run 50 interleaved requests (tracked)
            TestPhase(
                name="Load_Test",
                type="execution",
                mode="round_robin",
                total_requests=50,
                track_metrics=True,
                targets=[
                    ApiTarget(name="Search", url="https://httpbin.org/get", rps=10),
                    ApiTarget(name="Profile", url="https://httpbin.org/get", rps=10)
                ]
            )
        ]
    )

    orchestrator = PerformanceOrchestrator(plan)
    stats = await orchestrator.run_plan()

    print("\n" + "="*40)
    print("       MASSIVE SCALE PERFORMANCE REPORT")
    print("="*40)
    print(f"Total Tracked: {stats.count}")
    print(f"P99 Latency:   {stats.p99:.2f}ms")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
```
