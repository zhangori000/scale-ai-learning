# Solution: Distributed Trace Propagation (The "Trace ID" Journey)

In `scale-agentex`, this logic is the backbone of **Observability**. It's how the platform knows that a specific log line in the Agent's code belongs to a specific button click in the UI. It's often handled using **OpenTelemetry (OTEL)**.

## The Implementation

```python
import contextvars
import uuid
from typing import Dict

# --- 1. Global Context ---
# This acts as 'Thread Local' storage but for async tasks.
trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="no-trace")

# --- 2. The Propagator (The Bridge) ---
class TracePropagator:
    """
    Handles the movement of IDs from 'Memory' to 'Network' and back again.
    """
    @staticmethod
    def inject_headers(headers: Dict[str, str]):
        """
        Takes the ID from local memory and puts it in an outgoing HTTP header.
        Called BEFORE a network call.
        """
        current_id = trace_id_ctx.get()
        headers["x-trace-id"] = current_id
        print(f"    (Propagator) INJECTED {current_id} into headers.")

    @staticmethod
    def extract_context(headers: Dict[str, str]):
        """
        Takes the ID from an incoming HTTP header and puts it in local memory.
        Called AFTER receiving a network call.
        """
        incoming_id = headers.get("x-trace-id", "no-trace")
        
        # This 'Sets' the context for THIS process/async task.
        trace_id_ctx.set(incoming_id)
        print(f"    (Propagator) EXTRACTED {incoming_id} from headers.")

# --- 3. The Simulated Services ---

def service_agent(headers: Dict[str, str]):
    """Simulates the Agent's Python process on a different server."""
    # 1. Extract context (The first thing we do!)
    TracePropagator.extract_context(headers)
    
    # 2. Perform Agent work
    print(f"  [AGENT]    Handling AI Logic. Current Context Trace ID: {trace_id_ctx.get()}")
    print(f"  [AGENT]    Log: 'Agent finished contract analysis.'")

def service_worker(headers: Dict[str, str]):
    """Simulates the Temporal Worker process."""
    # 1. Extract context from the Platform's call
    TracePropagator.extract_context(headers)
    print(f"  [WORKER]   Starting Activity. Current Context Trace ID: {trace_id_ctx.get()}")
    
    # 2. Some work happens...
    
    # 3. Prepare to call the next service (The Agent)
    out_headers = {}
    TracePropagator.inject_headers(out_headers)
    
    # 4. Simulated Network Call
    service_agent(out_headers)

def service_platform():
    """Simulates the FastAPI Backend process."""
    # 1. User clicks 'Send' - we generate a brand new Trace ID
    new_id = f"trace-{str(uuid.uuid4())[:4]}"
    trace_id_ctx.set(new_id)
    print(f"  [PLATFORM] Ingesting request. Generated Trace ID: {new_id}")
    
    # 2. Prepare to call the next service (The Worker)
    out_headers = {}
    TracePropagator.inject_headers(out_headers)
    
    # 3. Simulated Network Call (Platform -> Worker)
    service_worker(out_headers)

# --- 4. Execution ---
print("--- Starting Distributed Request Journey ---")
service_platform()

# Output should show the SAME ID in all 3 service logs!
```

### Key Takeaways from the Solution:

1.  **Network Boundaries:** Normal variables cannot cross from one server to another. Headers are the "Envelopes" that carry metadata across the network.
2.  **Context Isolation:** By using `ContextVar`, we ensure that if 100 people use the platform at the same time, their Trace IDs never get mixed up, even though the `TracePropagator` is shared.
3.  **End-to-End Visibility:** This is the difference between "I think there's a bug in the agent" and "I KNOW this specific user request failed at the agent because I can see its Trace ID in the agent's logs."
4.  **Why this matters for Scale-Agentex:** Distributed systems are a nightmare to debug without Tracing. In `src/api/authentication_middleware.py` and `src/adapters/http/adapter_httpx.py`, this propagation ensures that every single LLM call, database query, and agent event is linked together in one beautiful timeline in the UI.
