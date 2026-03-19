import time
import hashlib
import jwt # PyJWT
import logging
from typing import Dict

# Configuration Constants
TOTAL_BUCKETS = 1000
JWT_SECRET = "super-secret-key-at-scale-ai"
EVENT_ID = "bruno_mars_2026"

class IngressService:
    """
    Ingress handles the 20M 'Join' requests. 
    It is stateless and can be scaled to 1,000+ pods.
    """
    def __init__(self, redis_client):
        self.redis = redis_client

    def join_queue(self, user_id: str) -> str:
        """
        The 'Entry Point' for the user.
        """
        # 1. Capture high-precision join time (Nanoseconds)
        joined_at = time.time_ns()

        # 2. BUCKETING: Hash the user to one of 1,000 logical buckets.
        # This spreads the 20M writes across all physical Redis shards.
        bucket_id = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % TOTAL_BUCKETS
        bucket_key = f"queue:{EVENT_ID}:bucket:{bucket_id}"

        # 3. WRITE TO REDIS (O(log N))
        # We add the user to their assigned bucket.
        self.redis.zadd(bucket_key, {user_id: joined_at})

        # 4. GENERATE TOKEN
        # We sign the join time into a JWT. 
        # The user will present this to the CDN to check their status.
        token_payload = {
            "user_id": user_id,
            "event_id": EVENT_ID,
            "joined_at": joined_at,
            "exp": time.time() + 3600 # 1 hour expiry
        }
        
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        return token

# Mock for System Design
if __name__ == "__main__":
    # Simulate a user joining from Brazil
    service = IngressService(None) 
    print(f"Generated Token: {service.join_queue('user_brazil_123')}")
