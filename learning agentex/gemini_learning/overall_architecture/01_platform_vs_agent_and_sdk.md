# Chapter 1: The Platform vs. The Agent

To understand `scale-agentex`, you must understand the two main "players" in the system. 

### 1. The Platform (The "Manager")
When we say "the platform," we are talking about **this repository** (`scale-agentex`).
*   **What it is:** The "Office" where the work happens.
*   **What it provides:** 
    *   **The UI:** A place for users to chat with the agents.
    *   **The Database:** A memory for all tasks, messages, and traces.
    *   **The Orchestrator (Temporal):** A "Guarantee" that if something fails, it will be retried.
    *   **The API:** A standardized way for any client to talk to any agent.

### 2. The Agent (The "Worker")
The Agent is **NOT** in this repository. It is a separate Python program that you build on your own.
*   **What it is:** The "Expert" that does the actual thinking.
*   **What it does:** It receives instructions from the Platform, calls an AI model (like Claude or GPT), and sends the answer back.

### The Analogy: The Restaurant
*   **The Platform** is the **Restaurant Building**. It has the tables (the UI), the kitchen (the backend), and the waiters (the API).
*   **The Agent** is the **Chef**. You can have many different chefs (Italian, Japanese, French) in the same building. 
*   **The SDK** is the **Uniform and the Recipe Book** that the chefs must use so they can work in the restaurant's kitchen.

---

# Chapter 2: The SDK and Scaffolding

Since the Agent is your own code, how do you make it "talk" to the Platform? You use an **SDK** and a process called **Scaffolding**.

### 1. What is an SDK? (Software Development Kit)
An SDK is a **"Toolbox"** provided by Scale AI. 
*   **In real life:** If you're building furniture, the SDK is the "IKEA Tool Kit" that comes with the wood.
*   **In coding:** It's a library of pre-written code (`agentex-sdk`) that handles all the "boring" parts of being an agent. It knows how to format messages, how to handle errors, and how to "stream" text back to the platform.

### 2. What is Scaffolding? (Building the Skeleton)
When you are ready to build a new agent, you don't start with an empty file. You use a CLI command:
```bash
agentex init
```
This is called **Scaffolding**.
*   **What it does:** It automatically generates a folder with all the "Skeleton" files you need.
*   **What you get:** It gives you a `manifest.yaml` (config) and a `project/acp.py` (code).

### 3. Do we write the logic ourselves?
**Yes.** The "Scaffolding" gives you the **Skeleton**, but it doesn't give you the **Brain**.

*   **The Scaffolded Code:** It comes with a "Hello World" example. It has the correct "function names" (the protocol) that the platform expects.
*   **Your Job:** You must go into the `acp.py` file and write your own Python code. This is where you decide which AI model to call, what "tools" the agent has (like searching the web), and how it should behave.

### Summary: The "Brain" is Yours
Scale-Agentex provides the **Platform** (the infrastructure) and the **SDK** (the toolbox). The **Scaffolding** gives you the starting point. But the "Agent" itself is your own unique creation.
