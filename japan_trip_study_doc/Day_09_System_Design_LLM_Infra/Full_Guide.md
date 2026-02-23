# Day 09: System Design - LLM & ML Infrastructure
**Focus:** Designing the backbone of Scale AI's model evaluation and data labeling engine.

## 01. The Problem: The "LLM Evaluation Service"
**Scenario:** Scale AI needs to build a service that "evaluates" model outputs. Imagine we have 1,000 Model-A outputs and 1,000 Model-B outputs. We need to send them to humans (labelers) to decide which one is better.

**The Complexity:**
- **Scale:** 10 million evaluations per day.
- **Cost:** Human labeling is expensive. We need to reuse existing labels.
- **Latency:** The model output might take 30 seconds to generate.
- **Consistency:** Multiple labelers might see the same pair. We need to resolve their disagreements.

---

## 02. The Architecture: The "Async Evaluation Factory"

### High-Level Flow
1. **The Request:** Model outputs are pushed to a `Queue` (SQS/Kafka).
2. **The Ingestor:** Reads the queue, stores the raw outputs in a `Task Table` (Postgres).
3. **The Deduplicator:** Before creating a new task, checks a `Cache` (Redis) to see if we've already evaluated this exact pair of outputs.
4. **The Assignment Engine:** Finds available labelers and "assigns" the task to them. 
5. **The Consistency Checker:** If two labelers disagree, the task is automatically sent to a 3rd "Senior Labeler" for a final decision.

---

## 03. Component Breakdown (The "Scale AI" Choices)

### Data Storage: Postgres + S3
- **Postgres:** For structured task metadata (task_id, status, assigned_to).
- **S3:** For the actual model output (often massive JSONs or text). Never store raw 1MB model outputs in a SQL column! Store the **S3 URL** in the DB.

### The Queue: Why SQS/Kafka?
- "We need **Asynchronous Processing**. If 100,000 evaluations come in at once, we don't want the API to crash. We put them in a queue and let the workers process them at their own pace. This is **Load Leveling**."

### The Cache: Redis Bloom Filter
- "To save costs, we need to know if we've seen this pair before. A **Bloom Filter** in Redis is incredibly fast and memory-efficient for 'probabilistic set membership'—it can tell us 'I've definitely NOT seen this' or 'I MIGHT have seen this' in constant time."

---

## 04. Interview Dialogue: "Deep Dive into LLM Latency"

### Q: "LLM responses take 30 seconds to generate. How does your API handle this?"
**A:** "I would use **SSE (Server-Sent Events)** or a **Webhook**.
1. The user POSTs an evaluation request.
2. I return a `202 Accepted` immediately with a `request_id`.
3. My backend works in the background.
4. When finished, I either 'push' the result back to the user via a **Webhook** or the user 'subscribes' to a stream via **SSE** to see the result as it's ready."

### Q: "What happens if a labeler crashes while they have a task?"
**A:** "I use **Lease-based Locking**. When a labeler starts a task, I set a `claimed_until` timestamp in the database (e.g., `now + 10 minutes`). If they don't submit within 10 minutes, a background 'Janitor' process clears the `claimed_by` field, making the task available for someone else to pick up."

### Q: "How do you handle disagreement between 5 different labelers?"
**A:** "I would use a **Consensus Algorithm** like Majority Vote or Weighted Average (where more experienced labelers have a higher 'weight'). If the 'Confidence Score' is below a certain threshold (e.g., 3 vs 2), the system automatically triggers a 'Manual Audit' step."
