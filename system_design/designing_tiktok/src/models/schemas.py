from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Practical Tip: Use Pydantic for "Fail-Fast" Data Validation ---
# This ensures that if the database or another service sends bad data,
# our app catches it immediately instead of failing with a random error later.

class VideoMetadata(BaseModel):
    video_id: str
    author_id: str
    hls_url: str
    tags: List[str]
    like_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

class FeedRequest(BaseModel):
    user_id: str
    cursor: Optional[str] = None
    count: int = 10

class FeedResponse(BaseModel):
    videos: List[VideoMetadata]
    next_cursor: Optional[str]
    latency_ms: float
