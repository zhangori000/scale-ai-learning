# Day 11 - System/Debug: Consumer Groups and Rebalancing

How do you scale a pipeline to 1,000 workers? This is a **Distributed Scaling** lesson.

## 1. The Scenario
Scale AI's Kafka topic `images_raw` has 1,000,000 messages waiting. We have 10 workers. Each worker is processing 1,000 images per minute. 

**The Math:** 10 workers * 1,000/min = 10,000/min. It will take 100 minutes to finish the backlog. The customer is angry. They want it done in **10 minutes**.

## 2. The Solution: Kafka Consumer Groups
You don't need a "Faster Worker." You need **More Partitions**.

### The "Scale AI" Kafka Scaling Strategy:
1.  **Increase Partitions:** Change the topic from 10 partitions to 100 partitions.
2.  **Add Workers:** Start 90 more workers in the same "Consumer Group" (e.g. `resizer-group`).
3.  **The Rebalance:** Kafka automatically says: "Okay, I have 100 partitions and 100 workers. Each worker gets 1 partition."

**Result:** 100 workers * 1,000/min = 100,000/min. The backlog is gone in 10 minutes.

---

## 3. 🧠 Key Teaching Points:
*   **The "Rebalance Storm" Bug**: When you add 90 workers, Kafka has to "Rebalance" the partitions. During the rebalance, **no work is done**. This can take 30 seconds. This is a classic "FDE Interview" problem: "My pipeline stops for 30s every time I scale up. Why?"
*   **The Partition Limit**: If you have 100 partitions, you can only have 100 workers. A 101st worker will sit there doing **nothing**. This is why we over-partition topics (e.g. 2,000 partitions for a high-volume topic) even if we only have 10 workers today.
*   **Exactly-Once Processing**: Kafka has a "Secret Superpower": **Transactional Producers**. It allows you to: (1) Read from Topic A, (2) Process, (3) Write to Topic B, and (4) Commit the "Offset" (the progress marker) in ONE transaction. If it fails, the "Offset" isn't moved, so we re-process.
*   **Consumer Lag**: This is the most important metric at Scale. `Lag = Current_Max_Offset - Current_Worker_Offset`. If Lag is increasing, your pipeline is **failing to keep up**.
*   **FDE Tip**: When a customer says "One specific partition is 10x slower than the others," your first check is the **Partition Key**. If you partition by `customer_id`, and "OpenAI" has 10,000,000 images while everyone else has 1,000, the "OpenAI Partition" will be a **Hot Partition**. Use a more balanced key (like `task_id`).
*   **Scale's Best Practice**: Always monitor `Consumer Lag` per partition, not just for the whole topic.
