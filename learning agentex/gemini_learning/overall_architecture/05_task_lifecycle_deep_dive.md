# Chapter 3: The Lifecycle of a Task (How it works under the hood)

When you send a request to `/tasks`, a complex chain of events happens. This is the **Systems Design** in action.

### 1. The Gateway (FastAPI)
*   The UI calls `POST /tasks`.
*   The API validates your input using **Pydantic**.
*   The API saves the initial state (e.g., "PENDING") to **PostgreSQL**.

### 2. The Orchestrator (Temporal)
*   FastAPI doesn't call the Agent directly (that would be risky if the Agent is slow).
*   Instead, it tells **Temporal** to start a `TaskWorkflow`.
*   Temporal "remembers" that this task exists in its own internal database.

### 3. The Bridge (Activity)
*   Temporal picks a "Worker" to run a piece of code called an **Activity**.
*   This Activity's job is to talk to your Agent code.
*   It uses **JSON-RPC** (a standard protocol) to call your Agent's URL (e.g., `http://localhost:8080/create_task`).

### 4. The Agent (Your Logic)
*   Your Python code (using the `agentex-sdk`) receives the JSON-RPC call.
*   It starts an LLM call (e.g., to OpenAI).
*   As the LLM generates text, the SDK **streams** that text back to the platform in real-time.

### 5. The Response (Events & Messages)
*   The platform receives these "Deltas" (small chunks of text).
*   It emits **Events** (to update the UI) and eventually saves a final **Message** to **MongoDB**.
*   The task state is updated to "COMPLETED" in PostgreSQL.

### 6. Observability (Spans)
*   During this entire process, **OpenTelemetry** is recording every single step as a "Span."
*   If the agent took 10 seconds to respond, you can look at the Spans and see:
    *   2s: Temporal overhead.
    *   7s: OpenAI network call.
    *   1s: Platform processing.

---

### Why is this good design?
1.  **Durable:** If the platform crashes at Step 3, Temporal will **automatically restart** the Activity and retry the call to the Agent.
2.  **Scalable:** You can run 10,000 tasks at the same time because the platform doesn't "wait" synchronously; it uses a queue-based system.
3.  **Visible:** By separating the "Task" (the job) from the "Message" (the content) and the "Span" (the trace), developers can debug complex AI behaviors without guessing.
