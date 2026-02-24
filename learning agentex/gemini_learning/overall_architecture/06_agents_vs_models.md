# Chapter 4: Agents vs. Models (The "Service" vs. The "Brain")

A common point of confusion is whether Agentex is a model like Claude or GPT. It is **not**.

### 1. The Model (The Raw Intelligence)
*   **Examples:** OpenAI's GPT-4, Anthropic's Claude 3, Google's Gemini Pro, or Meta's Llama 3.
*   **What it does:** It takes text as input and predicts the next piece of text. It has no "memory" of your specific business, no way to call your database, and it can't "run" by itself.

### 2. The Agent (The Service / The Worker)
*   **What it is:** A piece of Python code (often running on your server) that **uses** one or more models to perform a specific job.
*   **What it adds:** 
    *   **Tools:** The agent can call a Google Search API or a SQL database.
    *   **Logic:** It can say "If the LLM says the user is angry, send this to a human."
    *   **Memory:** It can look up the user's past 5 conversations before calling the model.

### 3. Agentex (The Platform / The Factory)
*   **What it does:** It provides the infrastructure to **host** and **connect** your Agents to the world.
*   **Why use it:** Instead of having 50 different Python scripts running on 50 different servers, you register them all with Agentex. Agentex then handles the API endpoints, the database for chat history, the real-time events, and the tracing.

### The "Complexity" (Endpoint Parameters)
When you call the Agentex API, you aren't just sending a prompt. You are sending a **structured request**. 

**Example: `POST /tasks` Parameters:**
*   `name`: A unique identifier for the task (e.g., "contract-audit-job-2024").
*   `params`: A dictionary of custom inputs for the agent (e.g., `{"document_url": "s3://legal/contract.pdf", "strict_mode": true}`).
*   `task_metadata`: Internal tracking info (e.g., `{"department": "legal-ops", "priority": "high"}`).

**Example: `POST /messages` Parameters:**
*   `content`: The message text.
*   `stream`: (Boolean) If `true`, the agent will send back text chunks as they are generated (the "typing" effect).
*   `task_params`: Allows you to update the task configuration mid-conversation.

**In short:** An Agent is a **long-running service** that lives on your infrastructure. Agentex is the **manager** that tells the Agent what to do and records everything it says and does.
