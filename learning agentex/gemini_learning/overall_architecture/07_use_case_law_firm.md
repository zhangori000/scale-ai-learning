# Use Case: Law Firm (Legal Ops)

How would a real-world enterprise like a top-tier Law Firm use the `scale-agentex` repository?

### 1. The Problem
A law firm has 10,000 contracts to review for a new regulation. If a lawyer spends 15 minutes on each, it will take 2,500 hours. A simple "ChatGPT" prompt is too risky because:
*   **Context:** It might "hallucinate" a clause that isn't there.
*   **Reliability:** If the script crashes after 5,000 documents, how do you know where it stopped?
*   **Auditability:** How can you prove to a client exactly *how* the AI decided a contract was "high risk"?

### 2. The Agentex Solution
The firm builds a custom **"Contract Auditor Agent"** and registers it with the Agentex platform.

#### Step A: Task Ingestion (`POST /tasks`)
The firm's internal legal portal sends a batch of 10,000 requests to Agentex:
```json
{
  "name": "regulation-check-2024",
  "params": {
    "s3_bucket": "legal-contracts-2024",
    "rule_set": "GDPR_Compliance_v2"
  }
}
```

#### Step B: Durable Orchestration (Temporal)
Agentex starts 10,000 **Temporal Workflows**. 
*   If the server restarts at 2 AM, Temporal "pauses" all 10,000 jobs.
*   When the server comes back, it resumes exactly where it was. No contract is missed.

#### Step C: The Agent's Work (ACP Protocol)
The Agentex platform calls the firm's Agent. The Agent:
1.  Downloads the PDF from S3.
2.  Calls **Claude-3-Opus** (the model) to summarize the "Liability" clause.
3.  Calls a **RAG (Retrieval-Augmented Generation)** database to check against past cases.
4.  Sends an **Event** back to the platform: `{"status": "ANALYSIS_COMPLETE", "risk_score": 0.85}`.

#### Step D: Human-in-the-Loop
Since the risk score is high (0.85), the Agentex platform marks the task as **"Awaiting Approval."**
A senior partner logs into the **Agentex-UI**, sees the high-risk contract, and looks at the **Spans (Traces)** to see exactly what the AI found. They click "Approved" or "Fix."

### 3. The Result
*   The firm reduces review time by 90%.
*   They have a full **Audit Trail** for every document.
*   The system is "bulletproof" because it uses the platform's durable execution and observability.
