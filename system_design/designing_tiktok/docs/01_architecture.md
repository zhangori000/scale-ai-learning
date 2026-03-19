# TikTok System Design: High-Level Architecture

## 1. Core Workflow Overview

### The Upload Path (The "Producer")
1.  **Ingestion:** User uploads video via Mobile App -> API Gateway.
2.  **Blob Storage:** Video bytes go to S3 (or similar Object Store).
3.  **Job Orchestration:** A Message Queue (Kafka) triggers parallel workers:
    *   **Transcoder:** Creates .m3u8 (HLS) in 1080p, 720p, 480p.
    *   **Moderation:** ML scans for NSFW, copyright, etc.
    *   **ML Embedding:** Thumbnail/Tags turned into Vectors (for the Vector DB).
4.  **Completion:** All workers finish -> Metadata Service marks video `ACTIVE`.
5.  **Index Update:** Video ID pushed to **ElasticSearch** (keyword search) and **Milvus** (similarity search).

### The Watch Path (The "Consumer")
1.  **Feed Request:** `GET /feed?user_id=123` hits Feed Service.
2.  **Mult-Stage Recommendation:**
    *   **Retrieval (20ms):** Pull 1,000 "Candidate" IDs from ElasticSearch/Milvus/Follow-Service.
    *   **Ranking (150ms):** Score 1,000 IDs using Neural Network + User/Video Features (from Redis).
3.  **Response:** Feed Service returns a JSON list of 10-20 Video IDs + CDN URLs.
4.  **Playback:** Phone downloads small chunks (.ts files) from the **CDN (Edge)**.

## 2. Key Industrial Components

### The "Global Candidate Pool"
*   **What it is:** The "Universe" of all ready-to-watch videos.
*   **Discovery Bucket:** Every new video gets its first 1,000 views here.
*   **Database:** 
    *   **ElasticSearch:** For keyword, location, and language-based finding.
    *   **Milvus/Pinecone:** For "people like you watched this" (vector similarity).

### The "Feature Store" (The Brain)
*   **Role:** Storage for real-time stats (like count, loop count, user interests).
*   **Database:** **Redis** (Hot data) + **Cassandra** (Historical features).
*   **The Flink Loop:** User Actions (Likes) -> Kafka -> **Flink** (Real-time aggregation) -> Feature Store Update.

---

# Data Storage & Scaling (LSM Trees & Hot Keys)

## 1. LSM Trees: Why the Database "Doesn't Feel It"
In B-Trees (SQL), every write is "Random I/O" (slow). In **LSM Trees** (Cassandra/ScyllaDB/RocksDB):
1.  **MemTable:** Writes hit RAM first. (Fast)
2.  **WAL:** Write-Ahead Log appends to disk. (Fastest)
3.  **SSTables:** Immutable sorted files on disk. 
4.  **Compaction:** Background threads merge files later.
*   **Outcome:** The DB can handle millions of writes per second because it's always "appending," never "editing" old data.

## 2. The "Hot Key" Problem
When a video goes viral, 100M people request Video ID `vid_999` metadata at once. 
*   **Solution 1: Read Replicas.** 1 Master for writes, 100 Replicas for reads.
*   **Solution 2: L1 (Local) Caching.** Feed Nodes store `vid_999` metadata in their own RAM for 10 seconds.
*   **Solution 3: Edge Caching (CDN).** The actual metadata JSON can be cached at the CDN level.

## 3. Sharding & Partitioning
*   **User Data:** Partitioned by `user_id`. (All of Bob's data on Node A).
*   **Video Feed:** Partitioned by `user_id` (The Feed). Sorted by `timestamp` (The Clustering Key).
*   **Benefit:** To get a user's feed, you only hit **one node**, not the whole cluster.
