from __future__ import annotations
import asyncio
import random
from typing import List, Dict, Optional
from ..domain.entities import Comment

class CommentService:
    def __init__(self):
        # Mocking ScyllaDB (Partitioned by video_id)
        self.db: Dict[str, List[Comment]] = {}
        
        # Mocking Redis ZSET (comments:top:{video_id})
        # Score is Like Count, Value is Comment ID
        self.top_comments_cache: Dict[str, Dict[str, int]] = {}

    async def post_comment(self, comment: Comment) -> Comment:
        """
        Write to Scylla and initialize Redis entry.
        """
        if comment.video_id not in self.db:
            self.db[comment.video_id] = []
        
        self.db[comment.video_id].append(comment)
        
        # Initialize in Redis ZSET
        if comment.video_id not in self.top_comments_cache:
            self.top_comments_cache[comment.video_id] = {}
        self.top_comments_cache[comment.video_id][str(comment.id)] = 0
        
        print(f"[CommentService] Posted comment {comment.id} on video {comment.video_id}")
        return comment

    async def get_comments(self, video_id: str, sort_by: str = "top") -> List[Comment]:
        """
        Hybrid retrieval logic.
        """
        if sort_by == "top":
            return await self._get_top_comments(video_id)
        else:
            return await self._get_recent_comments(video_id)

    async def _get_top_comments(self, video_id: str) -> List[Comment]:
        """
        Step 1: Get Top IDs from Redis.
        Step 2: Hydrate metadata from Scylla.
        """
        print(f"[CommentService] Fetching Top Comments from Redis for {video_id}")
        await asyncio.sleep(0.01) # Mock Redis latency
        
        video_zset = self.top_comments_cache.get(video_id, {})
        # Sort by score (likes) descending
        sorted_ids = sorted(video_zset.items(), key=lambda x: x[1], reverse=True)[:10]
        top_ids = [str(item[0]) for item in sorted_ids]
        
        # Hydrate from DB
        all_comments = self.db.get(video_id, [])
        return [c for c in all_comments if str(c.id) in top_ids]

    async def _get_recent_comments(self, video_id: str) -> List[Comment]:
        """
        Direct Scylla query (ordered by clustering key created_at).
        """
        print(f"[CommentService] Fetching Recent Comments from Scylla for {video_id}")
        await asyncio.sleep(0.02) # Mock Scylla latency
        all_comments = self.db.get(video_id, [])
        # Sort by timestamp descending
        return sorted(all_comments, key=lambda x: x.created_at, reverse=True)[:10]

    async def increment_like(self, video_id: str, comment_id: str):
        """
        Simulate Flink updating the like count.
        """
        # Update Redis ZSET (Fast path)
        if video_id in self.top_comments_cache:
            if comment_id in self.top_comments_cache[video_id]:
                self.top_comments_cache[video_id][comment_id] += 1
        
        # Update Scylla (Slow path)
        all_comments = self.db.get(video_id, [])
        for c in all_comments:
            if str(c.id) == comment_id:
                c.likes += 1
                break
