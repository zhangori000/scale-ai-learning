# TikTok System Design: Interactions & Data Tiering

## 1. Overview of Interactions (Likes, Saves, Shares)
Interactions are the "Lifeblood" of the algorithm and the source of truth for creator payments. They must handle massive write bursts while ensuring eventual consistency for the UI and strict consistency for payments.

### The "Write Path" (Real-time Engagement)
1.  **Interaction Service:** Receives the `POST /interaction` request.
2.  **Kafka Producer:** Pushes the raw interaction event to a `user_interactions` topic.
3.  **UI Feedback:** Returns `200 OK` to the mobile app immediately.

---

## 2. The Three Data Tiers

### Tier 1: Hot (Real-time Analytics & UI)
*   **Technology:** Redis (Master-Replica Cluster) + Apache Flink.
*   **Workflow:** Flink consumes from Kafka -> Batches likes (e.g., 100 likes per batch) -> Increments Redis counters.
*   **Purpose:** Showing the "Like Count" on the video screen.
*   **Consistency:** Eventual Consistency. Users might see slightly different numbers for a few seconds.

### Tier 2: Warm (User Profile & History)
*   **Technology:** ScyllaDB (or Cassandra).
*   **Workflow:** A "Scylla-Sink" worker consumes from Kafka and writes to the `user_interactions` table.
*   **Purpose:** Powering the "Liked Videos" or "Saved Videos" tab in the user's profile.
*   **Indexing:** Partitioned by `user_id`, sorted by `created_at` (Clustering Key).
*   **Consistency:** High-availability with tunable consistency.

### Tier 3: Cold (Auditing & Payments)
*   **Technology:** S3/HDFS + Apache Spark.
*   **Workflow:** Kafka Connect sinks all events to S3 in Parquet/Avro format.
*   **Purpose:** Once a day, a Spark Batch Job runs to calculate official counts, detect bot fraud, and process creator payouts.
*   **Consistency:** Strong Consistency (The Absolute Source of Truth).

---

## 3. Extensibility Design
To avoid creating separate services for every new interaction (Like, Save, Tip, Super-Like), we use a **Generic Interaction Schema**.

### Generic Interaction Entity
```python
class InteractionType(str, Enum):
    LIKE = "LIKE"
    SAVE = "SAVE"
    SHARE = "SHARE"
    COMMENT = "COMMENT"
    TIP = "TIP"

class Interaction(BaseModel):
    id: UUID
    user_id: str
    target_id: str # Video_ID or Comment_ID
    type: InteractionType
    metadata: Dict[str, Any] # For comment text, tip amount, etc.
    created_at: datetime
```

### Architectural Principles (Inspired by Scale-Agentex)
1.  **Domain/Repository Pattern:** Logic is separated from the database.
2.  **Strict Typing:** Using Python's `typing` and `Pydantic` for safety.
3.  **Asynchronous I/O:** Every network call is `async`.
4.  **Idempotency:** Every request includes a `request_id` to prevent double-counting interactions on retry.
