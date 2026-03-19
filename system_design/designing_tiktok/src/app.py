from fastapi import FastAPI, Depends, BackgroundTasks, Request
import time
import asyncio
from typing import List, Optional
from .models.schemas import FeedRequest, FeedResponse, VideoMetadata
from .services.recommendation import RecEngine
from .services.interactions import InteractionService
from .services.comments import CommentService
from .domain.entities import Interaction, InteractionType, Comment

# --- Practical Tip: Dependency Injection ---
# In high-scale systems, we inject "Services" into our "Endpoints."
# This makes it easy to swap the real ML engine for a mock during testing.

app = FastAPI(title="TikTok Full-Service Simulation")

# Global singletons for services
rec_engine = RecEngine()
interaction_service = InteractionService()
comment_service = CommentService()

def get_rec_engine():
    return rec_engine

def get_interaction_service():
    return interaction_service

def get_comment_service():
    return comment_service

# --- Practical Tip: Middleware ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# --- Background Telemetry (Kafka Simulator) ---
async def log_telemetry(user_id: str, video_ids: List[str]):
    await asyncio.sleep(0.01)
    print(f"[Telemetry] Sent exposure log for user {user_id} to Flink.")

# --- Interaction Endpoints ---

@app.post("/v1/interactions")
async def post_interaction(
    interaction: Interaction,
    background_tasks: BackgroundTasks,
    service: InteractionService = Depends(get_interaction_service),
    comments: CommentService = Depends(get_comment_service)
):
    # Core Logic
    await service.post_interaction(interaction)
    
    # If this is a comment like, also update the ranking in Redis (Flink Simulation)
    if interaction.type == InteractionType.COMMENT_LIKE:
        # We assume metadata contains video_id for now
        video_id = interaction.metadata.get("video_id")
        if video_id:
            background_tasks.add_task(comments.increment_like, video_id, str(interaction.target_id))
    
    return {"status": "success", "id": interaction.id}

@app.get("/v1/users/{user_id}/likes")
async def get_user_likes(
    user_id: str,
    service: InteractionService = Depends(get_interaction_service)
):
    likes = await service.get_user_likes(user_id)
    return {"user_id": user_id, "likes": likes}

# --- Comment Endpoints ---

@app.post("/v1/comments")
async def post_comment(
    comment: Comment,
    service: CommentService = Depends(get_comment_service)
):
    await service.post_comment(comment)
    return {"status": "success", "id": comment.id}

@app.get("/v1/videos/{video_id}/comments")
async def get_comments(
    video_id: str,
    sort_by: str = "top", # or "recent"
    service: CommentService = Depends(get_comment_service)
):
    comments_list = await service.get_comments(video_id, sort_by=sort_by)
    return {"video_id": video_id, "comments": comments_list}

# --- Feed Endpoints ---

@app.post("/v1/feed", response_model=FeedResponse)
async def get_tiktok_feed(
    request_body: FeedRequest,
    background_tasks: BackgroundTasks,
    engine: RecEngine = Depends(get_rec_engine)
):
    start_time = time.time()
    feed_videos = await engine.get_feed(request_body.user_id)
    background_tasks.add_task(log_telemetry, request_body.user_id, [v.video_id for v in feed_videos])
    latency = (time.time() - start_time) * 1000
    return FeedResponse(
        videos=feed_videos,
        next_cursor="cursor_abc_123",
        latency_ms=latency
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
