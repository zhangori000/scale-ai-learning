# What is Scale-Agentex?

Scale-Agentex is a comprehensive, full-stack **platform and development framework** for building, testing, and scaling AI agents. It's not just a single application, but rather an entire ecosystem designed to take agents from simple "L1" (Level 1) chatbots to "L5" autonomous systems.

## The Core Components

The repository is structured into several key parts:

### 1. The Backend (`/agentex`)
This is the "brain" of the platform.
*   **Tech Stack:** Python 3.12+, FastAPI.
*   **Infrastructure:** 
    *   **PostgreSQL:** For structured relational data (e.g., configurations, metadata).
    *   **Redis:** For fast caching and transient state management.
    *   **MongoDB:** For flexible document storage (e.g., chat histories, agent state).
    *   **Temporal:** A critical component for **durable workflows**. It ensures that if an agent's task is interrupted (e.g., a server crash or a network failure), it can resume exactly where it left off.
    *   **OpenTelemetry (OTEL):** For deep tracing and observability of agent calls.

### 2. The Frontend UI (`/agentex-ui`)
This is the "cockpit" where developers interact with their agents.
*   **Tech Stack:** Next.js (TypeScript), Tailwind CSS, Shadcn UI.
*   **Purpose:** 
    *   Provides a chat-like interface to test agents.
    *   Allows monitoring of agent tasks and message history.
    *   Visualizes agent "traces" (logs and step-by-step execution details) for debugging.

### 3. The SDK and CLI (`agentex-sdk`)
A set of developer tools to build your own agents.
*   **CLI:** Commands like `agentex init` to scaffold new agents and `agentex agents run` to start them locally.
*   **SDK:** A Python library that provides the **ACP (Agent-to-Client Protocol)**. This protocol ensures that all agents, no matter how complex, talk to the platform in a standardized way.

## So, "Is it a UI app?"

Yes and no.
*   **Yes:** It *includes* a powerful UI app (`agentex-ui`) for developers.
*   **No:** It is much more than that. It is a **backend-heavy infrastructure** platform. You don't just "run the UI"; you run a suite of services (Postgres, Mongo, Temporal, etc.) that together support the lifecycle of many different AI agents.

## Why use it?

If you are just building a simple chatbot that answers one question at a time, Agentex might be overkill. However, if you need:
1.  **Durable Execution:** Long-running tasks that shouldn't fail if a server restarts.
2.  **Standardization:** A consistent way to deploy many different types of agents.
3.  **Observability:** Knowing exactly what your agent was thinking at every step of its execution.
4.  **Async Workflows:** Moving beyond simple request-response to background tasks and complex orchestration.

Then Agentex provides the industrial-grade plumbing to make that happen.
