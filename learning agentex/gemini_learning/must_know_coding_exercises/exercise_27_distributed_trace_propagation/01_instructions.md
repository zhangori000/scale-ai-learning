# Exercise: Distributed Trace Propagation (The "Trace ID" Journey)

In `scale-agentex`, a single user request travels through many services:
1.  **Platform API** (FastAPI)
2.  **Temporal Worker** (Python)
3.  **The Agent** (External Python Service)

To debug a single request, we need a **Trace ID** that follows the request everywhere. This is called **Context Propagation**.

## The Problem
If Service A calls Service B, Service B doesn't know anything about Service A's local memory or `ContextVars`. We must **inject** the Trace ID into the HTTP Headers and **extract** it on the other side.

## The Goal
Build a `TracePropagator` that ensures a single ID is preserved across 3 simulated services.

## Requirements
1.  **Trace Storage:** Use `contextvars` to store the ID locally in each service.
2.  **Injector:** `inject_headers(headers_dict)`: Reads ID from context and adds `"x-trace-id"` to the dictionary.
3.  **Extractor:** `extract_context(headers_dict)`: Reads `"x-trace-id"` and sets it in the local context.
4.  **The services:**
    *   `Service_Platform`: Generates a new ID, calls `Worker`.
    *   `Service_Worker`: Extracts ID, calls `Agent`.
    *   `Service_Agent`: Extracts ID, prints final log.

## Starter Code
```python
import contextvars
import uuid
from typing import Dict

# --- 1. Global Context ---
trace_id_ctx = contextvars.ContextVar("trace_id", default="no-trace")

# --- 2. The Propagator (YOUR JOB) ---
class TracePropagator:
    @staticmethod
    def inject_headers(headers: Dict[str, str]):
        """TODO: Add 'x-trace-id' from context to headers"""
        pass

    @staticmethod
    def extract_context(headers: Dict[str, str]):
        """TODO: Read 'x-trace-id' from headers and SET context"""
        pass

# --- 3. The Simulated Services ---

def service_agent(headers: Dict[str, str]):
    # 1. Extract context from incoming headers
    TracePropagator.extract_context(headers)
    
    # 2. Log something
    print(f"  [AGENT]  Final Log - Trace ID: {trace_id_ctx.get()}")

def service_worker(headers: Dict[str, str]):
    # 1. Extract context from incoming headers
    TracePropagator.extract_context(headers)
    print(f"  [WORKER] Received task. Trace ID: {trace_id_ctx.get()}")
    
    # 2. Prepare to call Agent
    out_headers = {}
    TracePropagator.inject_headers(out_headers)
    
    # 3. Network Call
    service_agent(out_headers)

def service_platform():
    # 1. Start a new Trace
    new_id = f"trace-{str(uuid.uuid4())[:4]}"
    trace_id_ctx.set(new_id)
    print(f"  [PLATFORM] Starting Request. Trace ID: {new_id}")
    
    # 2. Prepare to call Worker
    out_headers = {}
    TracePropagator.inject_headers(out_headers)
    
    # 3. Network Call
    service_worker(out_headers)

# --- 4. Execution ---
print("--- Starting Distributed Request ---")
service_platform()
```
