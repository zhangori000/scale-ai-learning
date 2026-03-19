import asyncio
import random
import time
from typing import List, Dict
from ..models.schemas import VideoMetadata

# --- Practical Tip: Async Concurrency ---
# In a real system, the Retrieval stage hits 5 different DBs/Caches.
# If we do them one by one, latency = Sum of all.
# If we do them with `asyncio.gather`, latency = Max of any.

class RecEngine:
    def __init__(self):
        # Mocking our "Candidate Pool"
        self.mock_videos = [
            VideoMetadata(video_id=f"vid_{i}", author_id=f"user_{random.randint(1,100)}", hls_url=f"https://cdn.tiktok.com/v/{i}.m3u8", tags=["cat", "funny"])
            for i in range(1000)
        ]

    async def _retrieve_from_elasticsearch(self, tags: List[str]) -> List[VideoMetadata]:
        await asyncio.sleep(0.02) # Mock 20ms I/O latency
        return random.sample(self.mock_videos, 100)

    async def _retrieve_from_vector_db(self, user_id: str) -> List[VideoMetadata]:
        await asyncio.sleep(0.03) # Mock 30ms I/O latency
        return random.sample(self.mock_videos, 100)

    async def _rank_candidates(self, user_id: str, candidates: List[VideoMetadata]) -> List[VideoMetadata]:
        """
        Simulate an ML Ranking stage.
        In reality, this would call a GPU cluster (like TensorFlow Serving).
        """
        start_rank = time.time()
        # Mocking complex ML scoring logic:
        # We sort by a weighted score of 'likes' and a random 'personalization' factor.
        for video in candidates:
            # Adding some "Realism": High-scale systems often use randomized 
            # noise to avoid "Filter Bubbles."
            video.like_count = random.randint(0, 1000000)
        
        candidates.sort(key=lambda x: x.like_count, reverse=True)
        
        # Simulate CPU-heavy ML work
        await asyncio.sleep(0.1) 
        return candidates[:10] # Return Top 10

    async def get_feed(self, user_id: str) -> List[VideoMetadata]:
        start_time = time.time()

        # Step 1: Retrieval (Parallelized!)
        # This is where we hit Elasticsearch AND Milvus at the SAME TIME.
        print(f"[RecEngine] Retrieving candidates for {user_id}...")
        results = await asyncio.gather(
            self._retrieve_from_elasticsearch(["cat", "trending"]),
            self._retrieve_from_vector_db(user_id)
        )
        
        # Flatten the list of lists
        all_candidates = [vid for sublist in results for vid in sublist]
        unique_candidates = {v.video_id: v for v in all_candidates}.values()

        # Step 2: Ranking
        print(f"[RecEngine] Ranking {len(unique_candidates)} candidates...")
        final_feed = await self._rank_candidates(user_id, list(unique_candidates))

        print(f"[RecEngine] Total Latency: {(time.time() - start_time)*1000:.2f}ms")
        return final_feed
