# Lesson 01: The Agent Task Lifecycle

To understand the systems design of `scale-agentex`, you must follow a single "Task" from the moment a user clicks "Send" in the UI to the moment the AI Agent responds.

### 1. High-Level Architecture
The system is divided into three main zones:
1.  **Client Zone (UI):** Where the user interacts (Next.js/React).
2.  **Platform Zone (The Brain):** Where the Backend API (FastAPI) and Durable Workflows (Temporal) live.
3.  **Agent Zone (The Logic):** Where your specific Python agent code runs (ACP protocol).

### 2. The Step-by-Step Flow
1.  **Request Ingestion (FastAPI):**
    *   The UI sends a POST request to `/tasks`.
    *   FastAPI validates the request using Pydantic.
    *   The task is saved to **MongoDB** (for history) and **PostgreSQL** (for relational tracking).
2.  **Orchestration (Temporal):**
    *   The API tells the **Temporal Server** to start a new `TaskWorkflow`.
    *   Temporal persists the workflow state. If the server crashes now, Temporal will resume it.
3.  **The Activity (The bridge):**
    *   The Workflow triggers an **Activity** called `ExecuteAgentTask`.
    *   This Activity uses the `AgentACPService` to talk to the actual agent.
4.  **The Call (JSON-RPC over HTTP):**
    *   The platform sends a JSON-RPC `create_task` request to the Agent's URL (usually `localhost:8080` during dev).
    *   The Agent processes the request, calls an LLM, and streams back "Deltas" (small chunks of text).
5.  **Event Feedback:**
    *   As the Agent streams, the Platform Zone receives these events and updates the task state in the databases.
    *   The UI (polling or via SSE) sees these updates and shows the typing animation to the user.
