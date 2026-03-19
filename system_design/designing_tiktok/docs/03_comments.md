# TikTok System Design: Comments & Hierarchical Data

## 1. The Hierarchy Challenge
TikTok uses a **Two-Level Nested Model** to balance user experience and system performance.
*   **Level 1 (Top-Level):** Direct comments on the video.
*   **Level 2 (Replies):** Replies to a top-level comment.
*   **Rule:** If a user replies to a reply, it is "flattened" into Level 2 and uses an `@mention` to indicate the recipient. This avoids "Infinite Recursion" which is a database killer.

---

## 2. Storage Strategy (ScyllaDB/Cassandra)
We use a Wide-Column NoSQL database for its massive write throughput and predictable read latency.

### The Schema
*   **Partition Key:** `video_id` (Ensures all comments for one video live on the same physical server).
*   **Clustering Key:** `(parent_id, created_at, comment_id)`
    *   `parent_id`: Grouping replies under their root comment.
    *   `created_at`: Sorting by time within the group.

| **Partition Key** (`video_id`) | **Clustering Key** (`parent_id`, `created_at`) | **Value** (`text`, `author`, `likes`) |
| :--- | :--- | :--- |
| `vid_123` | `root`, `10:00:00` | "First!" (likes: 500) |
| `vid_123` | `c_abc`, `10:05:00` | "I agree!" (likes: 10) |

---

## 3. The "Hybrid" Ranking Engine (The Top Comment Problem)
We cannot sort by `like_count` directly in the database because it changes too fast, leading to "Disk Thrashing."

### The Solution: Redis ZSETs
1.  **Persistence (Scylla):** Stores the actual text and metadata.
2.  **Ranking (Redis):** For trending videos, we maintain a **Sorted Set (ZSET)** in Redis.
    *   **Key:** `comments:top:{video_id}`
    *   **Member:** `comment_id`
    *   **Score:** `like_count`

### The "Fetch Top Comments" Flow
1.  **Rank:** `ZREVRANGE comments:top:vid_123 0 20` -> Returns Top 20 `comment_ids`.
2.  **Hydrate:** `SELECT * FROM comments WHERE video_id='vid_123' AND comment_id IN (...)`
3.  **Result:** High-speed, perfectly sorted comments with zero database sorting overhead.

---

## 4. Real-time Synchronization (Flink's Role)
How do we keep Redis and Scylla in sync?
1.  **Interaction Service:** Pushes `COMMENT_LIKE` to Kafka.
2.  **Flink Worker:**
    *   Consumes likes in a **1-second window**.
    *   `ZINCRBY` in Redis (Real-time update).
    *   `UPDATE ... SET likes = likes + N` in Scylla (Eventually consistent source of truth).

---

## 5. Moderation & Shadow Banning
*   **Synchronous:** ML Toxicity scan on `POST`. Reject if score is > 0.9.
*   **Asynchronous:** Deep scan for spam/copyright.
*   **Shadow Ban:** If a user is flagged as a troll, set `is_hidden = true`. The comment only shows up for the author, preventing them from knowing they are banned while protecting the community.

---

## 6. Pagination (The Cursor Pattern)
Never use `OFFSET`. Use **Cursors**.
*   **Request:** `GET /comments?vid=123&cursor=last_like_100_last_id_abc`
*   **Query:** `WHERE (likes < 100) OR (likes = 100 AND id < 'abc') LIMIT 20`
*   **Benefit:** Constant time (O(1)) performance regardless of how deep the user scrolls.
