# Day 01 - System/Debug: The Retry-Induced Double Charge Bug

This is a classic Scale AI interview problem. A user claims they were charged twice for the same task labeling batch.

## 1. The Scenario
The user's client (e.g., a script) sends a "Charge Payment" request. It times out after 1 second. The script correctly **retries** the request. Both requests eventually reach the server. 

**Wait, what happened?** The first request was NOT lost; the network was just slow. The server processes both and charges the user $100 + $100.

## 2. The Solution: Client-Generated Idempotency Keys
We can't solve this with timeouts alone. We need the client to say, "This is Request #12345."

### The Correct Fix:
1.  **The Header:** The client MUST send an `Idempotency-Key` (a UUID) in the header.
2.  **The Server Table:** We create an `idempotency_keys` table in our DB.
3.  **The Transaction:**
    ```python
    @app.post("/v1/charge")
    async def charge_user(
        amount: int, 
        idempotency_key: str = Header(...)
    ):
        async with db.transaction():
            # 1. Check if we've seen this key
            existing = await db.fetch_row(
                "SELECT response_body FROM idempotency_keys WHERE key = :k", 
                {"k": idempotency_key}
            )
            if existing:
                # IMPORTANT: Return the ORIGINAL response!
                return json.loads(existing["response_body"])

            # 2. If NEW, do the work (Call Stripe, update balance, etc.)
            response = await payment_gateway.charge(amount)

            # 3. Store the key AND the response
            await db.execute(
                "INSERT INTO idempotency_keys (key, response_body) VALUES (:k, :r)",
                {"k": idempotency_key, "r": json.dumps(response)}
            )
            return response
    ```

## 🧠 Why this works:
*   **Ambiguous Timeout:** A timeout doesn't mean "failure." It means "unknown." By using an idempotency key, we make "Retries" safe.
*   **Result Caching:** By storing the `response_body`, even if the first request succeeded and the client missed it, the second request gets the *same* success response. No double work, no double charge.
*   **Distributed State:** This is the ONLY way to solve double writes across a cluster of servers.
