from typing import List, Optional, Literal, Dict, Union
from pydantic import BaseModel, Field

class ApiTarget(BaseModel):
    name: str
    url: str
    method: Literal["GET", "POST", "PUT", "DELETE"] = "GET"
    rps: int = 10
    total_requests: Optional[int] = None # If set, this target runs for exactly X requests
    payload: Optional[Dict] = None

class TestPhase(BaseModel):
    name: str
    type: Literal["provisioning", "execution"]
    # round_robin: Interleave API A, B, A, B...
    # sequential_batch: Finish all of A, then all of B...
    mode: Literal["round_robin", "sequential_batch"] = "round_robin"
    
    # Load Control: Use either duration OR total_requests
    duration_sec: Optional[int] = None
    total_requests: Optional[int] = None
    
    targets: List[ApiTarget]
    track_metrics: bool = True

class TestPlan(BaseModel):
    project_name: str
    concurrency_limit: int = 1000 # Max active requests
    phases: List[TestPhase]
