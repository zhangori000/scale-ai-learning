# Use Case: PhD Researcher (AI/LLM Research)

How would a PhD researcher at a top AI lab or university use the `scale-agentex` repository?

### 1. The Problem
A researcher is developing a new **Multi-Agent Reasoning** technique (e.g., "Chain of Thought" or "Debate" among three different AI models). 
*   **Challenge:** They need to compare how **GPT-4** and **Claude-3** debate each other.
*   **Measurement:** They need to track the "Step-by-Step" reasoning of each model to see where they agree or disagree.
*   **Volume:** They need to run this experiment 1,000 times to get statistically significant results.

### 2. The Agentex Solution
The researcher builds three separate Agents (e.g., "Debater-1," "Debater-2," and "Judge") and registers them with the Agentex platform.

#### Step A: Multi-Agent Choreography (`POST /tasks`)
The researcher's experiment script starts a new task in Agentex:
```json
{
  "name": "debate-experiment-v3",
  "params": {
    "topic": "Is AGI possible in 5 years?",
    "model_1": "gpt-4-turbo",
    "model_2": "claude-3-opus",
    "num_rounds": 5
  }
}
```

#### Step B: The "Sub-Agent" Workflow
The researcher writes a **Temporal Workflow** that:
1.  Calls `Debater-1.message_send(topic)`.
2.  Takes the response and calls `Debater-2.message_send(response_1)`.
3.  Repeats this 5 times.
4.  Finally, calls `Judge.message_send(all_responses)`.

#### Step C: Deep Observability (Spans & Traces)
The most valuable part for a researcher is the **Spans**. Agentex automatically records:
*   The exact **Prompt** sent to GPT-4.
*   The **Token Count** used.
*   The **Time** it took for the model to "think."
*   The **Raw JSON** output from the model.

#### Step D: Evaluation (Eval Service)
The researcher uses the **Agentex-UI** to look at the **Tracing View**. 
They can visually see the "Reasoning Chain" (Step 1 -> Step 2 -> Step 3).
If the debate failed, they can drill into the **Spans** to see if it was a "Network Error," a "Model Hallucination," or a "Logic Bug" in their code.

### 3. The Result
*   The researcher has a **Production-Ready** environment for their experiments.
*   They don't have to build their own "Tracing" or "History" database.
*   They can **share** their experimental results with other researchers by simply giving them a link to the Agentex-UI.
*   They can easily **swap models** (e.g., replace GPT-4 with a local Llama-3 instance) without changing the core platform code.
