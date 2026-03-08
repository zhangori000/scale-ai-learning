from __future__ import annotations

"""
This file mirrors docs' `run_worker.py`.
"""

from activities import get_all_activities
from temporal_runtime import AgentexWorker, MiniTemporalServer
from workflow import MyAgentWorkflow, CoinbaseWorkflow, CoindeskWorkflow


def build_worker(server: MiniTemporalServer, task_queue: str) -> AgentexWorker:
    worker = AgentexWorker(server=server, task_queue=task_queue)
    worker.register_workflow(MyAgentWorkflow)
    worker.register_workflow(CoinbaseWorkflow)
    worker.register_workflow(CoindeskWorkflow)
    worker.register_activities(get_all_activities())
    return worker
