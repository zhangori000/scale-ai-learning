# SDK Fundamentals: The "Stainless" Pattern

The `scale-agentex-python` repo is a **Client SDK**. It is fundamentally different from the `scale-agentex` repo (the Server).

*   **The Server (`scale-agentex`)**: Implements the logic, talks to MongoDB, runs Temporal.
*   **The SDK (`scale-agentex-python`)**: Is a wrapper around `httpx` that makes calling the server feel like "native" Python.

The SDK uses the **Stainless Pattern** (a high-quality auto-generation standard). Here are the 3 concepts you must know.

---

## 1. The Resource Pattern (Hierarchy)
Instead of having one giant `Client` class with 500 methods, the SDK breaks it down into "Resources."
*   `client.tasks`: Handles Task endpoints.
*   `client.agents`: Handles Agent endpoints.

In the code, you'll see `cached_property` used to lazily load these resources only when needed.

## 2. Casting and Modeling (Typed Responses)
When you call `client.tasks.create()`, you don't get a raw dictionary back. You get a **Pydantic Model** (e.g., a `Task` object).
The SDK uses a `cast_to=...` parameter internally to automatically convert the JSON response into a typed Python object.

## 3. The Stream Iterator (SSE Consumption)
The server sends SSE data (`data: {json}

`). 
The SDK provides a `Stream` class that handles:
1.  Connecting to the server.
2.  Decoding the binary chunks into lines.
3.  Parsing the `data:` prefix.
4.  Yielding Python objects.

---

## Key Files to Map in your Head:
*   `src/agentex/_client.py`: The main entry point.
*   `src/agentex/resources/`: The "verbs" (create, list, update).
*   `src/agentex/types/`: The "nouns" (Task, Agent, Message).
*   `src/agentex/_streaming.py`: The logic for handling real-time data.
