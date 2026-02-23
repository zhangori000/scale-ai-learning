# Round 1 Interview Testimonial: Translation + Requirement Breakdown + Implementation

## 1) Translation of your Chinese text

Original:

> 第一轮：bq + Backend Practical  
> BQ问了之前的项目.后端选的Python，题意相似于实现一个轻量级的Load Balancer，需要  
> github上clone 指定的项目，需要实现的点包括：  
> a.Worker状态管理（如活跃/过载/失联）  
> 任务队列与优先级调度机制  
> 如何支持可扩展性（比如Worker 节点动态加入）  
> 需要从task分发逻辑、worker心跳机制、failover策略等方面展开设计，并在有限的时间内给出代码，要求还是挺高的

English translation:

- Round 1: behavioral questions (BQ) + backend practical.
- BQ asked about previous projects.
- Backend language was Python.
- The coding task was similar to implementing a lightweight load balancer.
- Candidates needed to clone a specified GitHub project.
- Required points included:
  1. Worker state management (active / overloaded / lost)
  2. Task queue with priority scheduling
  3. Scalability support (for example, dynamic worker-node join)
- You had to design task dispatch logic, worker heartbeat mechanism, and failover strategy, then deliver code in limited time. The bar was high.

## 2) What they were likely asking you to build

Given the testimonial, this is a classic distributed scheduler / lightweight balancer exercise:

1. **Workers register and heartbeat**
2. **Tasks are queued by priority**
3. **Dispatcher assigns tasks to best available workers**
4. **Worker failure is detected by heartbeat timeout**
5. **In-flight tasks are reclaimed and retried (failover)**
6. **New workers can join without system restart**

In short: an in-memory control-plane service for task routing, not an L4 network load balancer.

## 3) Check against `scale-agentex` repo

I checked the linked repo and found:

- Worker/task-queue orchestration exists (mainly around Temporal workers and task queues)
- No obvious standalone interview-style module that directly implements:
  - active/overloaded/lost worker registry
  - explicit priority dispatch scheduler
  - lease-based failover logic in one small service

Evidence examples:

- `scale-agentex/agentex/src/temporal/run_worker.py`
- `scale-agentex/agentex/docs/docs/temporal_development/core_concepts.md`
- `scale-agentex/agentex/docs/docs/concepts/architecture.md`

So it is reasonable to infer the interview provided a separate skeleton repo and asked candidates to implement these components.

## 4) Implementation included in this folder

Files:

- `lightweight_lb.py` - main implementation
- `test_lightweight_lb.py` - unit tests
- `demo.py` - runnable demo script

### Features implemented

1. **Worker state management**
   - `ACTIVE`
   - `OVERLOADED` (in-flight >= capacity)
   - `LOST` (heartbeat timeout)

2. **Priority queue scheduling**
   - `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
   - FIFO within same priority

3. **Dispatch strategy**
   - choose least-loaded healthy worker
   - capacity-aware assignment

4. **Heartbeat + liveness**
   - heartbeat updates worker activity
   - timeout marks worker lost

5. **Failover**
   - lease-based assignment
   - reclaim task if lease expires or worker is lost
   - retry budget with dead-letter fallback

6. **Scalability behavior**
   - dynamic worker registration at runtime
   - pending queue drains automatically after new workers join

## 5) How to run

From this folder:

```bash
python -m unittest test_lightweight_lb.py -v
python demo.py
```

No external dependencies required.

## 6) Interview explanation template (how to present this design)

Use this structure in interviews:

1. **Data model**
   - Worker registry
   - Priority task queue
   - Lease table for in-flight tasks
2. **State machine**
   - Worker: active/overloaded/lost
   - Task: pending/leased/success/dead-letter
3. **Dispatch policy**
   - priority first
   - then least-loaded healthy worker
4. **Failure model**
   - heartbeat timeout => worker lost
   - lease timeout => reclaim task
   - bounded retry + dead-letter
5. **Scalability**
   - worker join/leave without downtime
   - horizontal worker growth improves throughput
6. **Tradeoffs**
   - in-memory implementation is simple but not durable
   - production would persist queue/leases and use distributed coordination

## 7) If they ask for production follow-up

You can say:

1. Persist tasks/leases in Redis or Postgres.
2. Use optimistic locking or atomic Lua scripts for dispatch.
3. Add idempotency keys for exactly-once business semantics.
4. Add metrics: queue depth, dispatch latency, retry rate, worker utilization.
5. Add admission control/rate limiting and circuit breakers for downstreams.
