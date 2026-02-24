# Chapter 2: The Complete API Surface (Deep Dive)

The Agentex API is designed around **Resources** and **Protocols**. Most interactions happen via a specialized **Agent RPC** layer.

## 1. Core Resource Endpoints
These endpoints manage the "entities" stored in **PostgreSQL**.

### **Agents (`/agents`)**
*   **`GET /agents`**: List all registered agents.
    *   **Params**: `limit`, `page_number`, `order_by`, `order_direction`, `task_id` (filter by agents in a specific task).
*   **`GET /agents/{id}` / `/name/{name}`**: Fetch specific agent details.
*   **`POST /agents/register`**: Used by an agent process to "tell" the platform it exists.
    *   **Input**: `name`, `acp_url` (where the agent lives), `acp_type`, `description`.
*   **`POST /agents/{id}/rpc` / `/name/{name}/rpc`**: **CRITICAL**. This is how you actually "talk" to an agent.
    *   **Input (JSON-RPC)**: `method` (e.g., `task/create`, `message/send`), `params`.
    *   **Logic**: The platform receives this, validates permissions, and "forwards" the request to the Agent's code.

### **Tasks (`/tasks`)**
*   **`GET /tasks`**: List all task instances.
    *   **Params**: `agent_id`, `limit`, `page_number`, `relationships` (e.g., load the associated agent data).
*   **`GET /tasks/{id}/stream`**: Server-Sent Events (SSE) endpoint.
    *   **Logic**: The UI connects here to receive real-time updates (deltas) as the agent thinks.
*   **`PUT /tasks/{id}`**: Update metadata.
    *   **Input**: `task_metadata` (Dict).

### **Messages (`/messages`)**
*   **`GET /messages`**: Get history for a task.
    *   **Params**: `task_id`, `filters` (JSON string to filter by text, author, or status).
*   **`GET /messages/paginated`**: Used for "Infinite Scroll" in the UI.
    *   **Params**: `cursor` (encoded timestamp/ID), `direction` ("older" or "newer").
*   **`POST /messages`**: Manually insert a message into a task (bypass Agent logic).

---

## 2. Advanced Observability & State
These endpoints provide the "X-Ray" view and "Safety" features.

### **Spans (`/spans`)**
*   **`GET /spans`**: Fetch OpenTelemetry traces.
    *   **Logic**: Every LLM call is recorded as a "Span." This endpoint lets you see the exact input/output of the AI's internal steps.
*   **Storage**: PostgreSQL (for structured search) and potentially external OTEL collectors.

### **Checkpoints (`/checkpoints`) & States (`/states`)**
*   **Checkpoints**: Snapshots of an agent's memory at a specific point in time.
*   **States**: The "Current Working Memory" of an agent.
*   **Storage**: PostgreSQL.

### **Events (`/events`)**
*   **`GET /events`**: List fine-grained progress updates.
    *   **Logic**: Used to show "Agent is searching..." or "Agent is 50% done."

---

## 3. Operations & Infrastructure

### **Schedules (`/schedules`)**
*   **Logic**: Automate tasks to run periodically (e.g., "Run every Monday at 8 AM").
*   **Storage**: PostgreSQL + Temporal.

### **Deployment History (`/deployment_history`)**
*   **Logic**: Tracks when an agent's code was updated. Crucial for auditing "which version of the AI said this?"

### **Agent API Keys (`/agent_api_keys`)**
*   **Logic**: Manage security keys for individual agents to authenticate against the platform.

---

## Data Storage Map
| Resource | Primary Database | Key Purpose |
|----------|-------------------|-------------|
| **Agents / Tasks** | **PostgreSQL** | Relational integrity, fast lookups by ID/Name. |
| **Messages / Events** | **PostgreSQL** | Sequential history, though often designed to handle high-volume streaming. |
| **Workflow State** | **Temporal (Internal DB)** | Durability; "Remembers" the code's progress mid-execution. |
| **Large Blobs** | **MongoDB (Optional)** | If configured, handles large unstructured data payloads. |

---

## Logic Flow: How a Request is Handled
1.  **FastAPI Route** receives the HTTP request.
2.  **Authorization Middleware** checks if your API Key has permission for this resource.
3.  **Use Case** (in `src/domain/use_cases`) performs the business logic.
4.  **Repository** (in `src/domain/repositories`) talks to PostgreSQL using **SQLAlchemy** (Async).
5.  **Agent Forwarding** (if RPC) uses **HTTPX** to call the Agent's local/remote server.
