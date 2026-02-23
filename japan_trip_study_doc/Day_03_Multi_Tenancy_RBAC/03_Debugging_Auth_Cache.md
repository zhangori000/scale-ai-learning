# Day 03 - System/Debug: The Auth Cache "Negative Poisoning" Bug

How do you cache authentication without breaking your system? This is a **Caching Strategy** lesson.

## 1. The Scenario
Scale AI's API is hit 1,000,000 times per minute. To save database cost, we cache the "User Lookup" from our Auth Database in **Redis**.

**The Bug:** The Auth Database goes down for 30 seconds. During those 30 seconds, 10,000 requests from *valid* users fail. Your code sees `DatabaseError`, can't find the user, and caches "User Not Found" for 5 minutes (a **Negative Result**). 

**Result:** The Auth DB is back up, but 10,000 *valid* users are locked out of their accounts for the next 5 minutes because the server "remembers" that they don't exist. This is **Negative Cache Poisoning**.

## 2. The Solution: Distinguishing Between "Not Found" and "Error"
You MUST separate your caching policy based on the **Result Type**.

### The "Scale AI" Correct Caching Policy:
1.  **SUCCESS (`VALID_USER`):** Cache for 1 hour.
2.  **NOT_FOUND (`INVALID_CREDENTIALS`):** Cache for 1 minute (short). This protects against "Brute Force" but recovers quickly if a user was just created.
3.  **SYSTEM_ERROR (`TIMEOUT`, `DB_DOWN`):** **DO NOT CACHE.** Return a `503 Service Unavailable` so the client knows to retry immediately when the DB is back.

### The Correct Implementation:
```python
async def get_user_cached(user_id: str):
    # 1. READ from Redis
    cached = await redis.get(f"auth:{user_id}")
    if cached == "NOT_FOUND":
        return None # Still return 401
    if cached:
        return json.loads(cached)

    try:
        # 2. READ from Database
        user = await db.fetch_user(user_id)
        if user:
            # SUCCESS: Long TTL
            await redis.set(f"auth:{user_id}", json.dumps(user), ex=3600)
            return user
        else:
            # NOT_FOUND: Very short TTL (protection)
            await redis.set(f"auth:{user_id}", "NOT_FOUND", ex=30)
            return None
            
    except DatabaseError:
        # 3. ERROR: Do NOT write to Redis!
        # This is the 'Safe' path. No poisoning.
        raise HTTPException(status_code=503, detail="Auth Service Unavailable")
```

---

## 3. 🧠 Key Teaching Points:
*   **Fail Fast, Recover Fast**: By returning a `503`, the client (or a load balancer like Nginx) knows that the failure is *temporary*. If you return a `401`, you're telling the client "This key is permanently bad."
*   **TTL (Time-To-Live)**: Use different TTLs for different states. Positive caching is for performance. Negative caching is for protection (against "Denial of Service").
*   **Cache Poisoning**: This is a classic "Scale-at-Scale" problem. When you have millions of users, "Transient Failures" (like a 30s DB blip) will happen. Your architecture must be designed to *not remember* those failures.
*   **Stale-While-Revalidate**: Another advanced Scale strategy: If the DB is down, serve the *old* cached user even if it's expired. This is better than a `503`. "Stale data is better than no data" in many Auth scenarios.
