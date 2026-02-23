# Day 11 - Practical: Real-Time Data Pipelines (Kafka and Streaming)

Scale AI processes 1 million images per day. We don't want to "Wait for the DB" for every single image. This is a **Stream Processing** lesson.

## 1. The Scenario
A customer uploads a 1,000-image dataset. We need to: (1) Resize the images, (2) Run a "Model" to detect objects, and (3) Store the results in a database.

**The Complexity:** 
- **Spiky Load:** 1,000,000 images at 9:00 AM, 0 images at 10:00 AM. 
- **Heavy Work:** Resizing and running the model takes 2 seconds per image.
- **Persistence:** The DB shouldn't be overwhelmed by 1 million `INSERT` calls.

---

## 2. The Solution: The Kafka "Buffer and Pipeline" Model
We don't do this in a single Python loop. We use **Kafka** as a "Shock Absorber."

### The "Scale AI" Data Pipeline:
1.  **Ingestor (FastAPI):** Just pushes the image URL to a Kafka Topic (`images_raw`).
2.  **Worker Cluster (Resizer):** Reads from `images_raw`, resizes, and pushes to `images_processed`.
3.  **Worker Cluster (ML Model):** Reads from `images_processed`, runs the model, and pushes to `detections`.
4.  **Database Sink:** Reads from `detections` and "Batches" the `INSERT` calls into Postgres.

### Why this is the "Gold Standard":
*   **Decoupling:** If the "ML Model" service crashes, the "Resizer" service can keep working and filling up the `images_processed` topic. Nothing is lost.
*   **Scalability:** If we have 1,000,000 images, we just start 100 "Resizer" workers. They'll "Drain" the queue.
*   **Backpressure:** If the Database is slow, the Sink worker just "Slows Down." It doesn't crash the entire API.

---

## 3. 🧠 Key Teaching Points:
*   **Topic vs. Queue**: In a Queue (SQS), once a message is read, it's "Gone." In a Topic (Kafka), the message stays there for 7 days. This allows us to "Replay" the entire pipeline if we find a bug in our ML model! 
*   **The "Batching Sink"**: Instead of 1,000,000 `INSERTs`, we collect 1,000 detections in memory and do ONE `INSERT INTO tasks (...) VALUES (...)` call. This is **1,000x faster** for the database.
*   **Partitioning**: Kafka divides a topic into "Partitions" (e.g. 10 partitions). Each partition can be read by ONE worker. This is how Kafka handles "Infinite" scale—just add more partitions.
*   **FDE Tip**: When a customer says "My data is taking 2 hours to process," your first check is the **Consumer Lag**. If the "Resizer" is at message #1,000,000 but the "Ingestor" is at message #10,000,000, you have a 9,000,000 message lag. **Start more workers!**
*   **Kafka-as-a-DB**: At Scale, Kafka isn't just a "Messaging Bus." It's a "Durable Log." It's the "Source of Truth" for the entire pipeline.
