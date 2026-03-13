import threading
import time
import queue
import random
import json

# --- MOCK INFRASTRUCTURE ---

# Mock S3 (Object Storage) - Stores actual video file paths
s3_storage = {
    "inbox": {},   # Raw uploads
    "final": {}    # Transcoded chunks
}

# Mock Postgres (Source of Truth) - Persistent metadata
postgres_db = {}

# Mock Redis (Cache) - Fast lookups for the Feed
redis_cache = {}

# Mock Kafka (The Belt) - Parallel task queues
kafka_upload_tasks = queue.Queue()
kafka_status_updates = queue.Queue()

# --- WORKER SERVICES ---

def transcoder_worker():
    """
    Simulates Fleet A: The Transcoding Service.
    Takes a raw video, 'chops' it, and uploads to final S3.
    """
    while True:
        task = kafka_upload_tasks.get()
        if task is None: break
        
        video_id = task['video_id']
        raw_path = task['path']
        
        print(f"[Worker: Transcoder] Processing video {video_id}...")
        
        # Simulate CPU/GPU heavy work (2 seconds)
        time.sleep(2)
        
        # Simulate creating chunks and manifest
        manifest_url = f"https://cdn.tiktok.com/{video_id}/manifest.m3u8"
        s3_storage["final"][video_id] = manifest_url
        
        print(f"[Worker: Transcoder] Video {video_id} chunks uploaded to S3 Final.")
        
        # Signal completion
        kafka_status_updates.put({"video_id": video_id, "type": "TRANSCODE", "status": "SUCCESS"})
        kafka_upload_tasks.task_done()

def safety_worker():
    """
    Simulates Fleet B: The Safety & ML Service.
    Scans for copyright and safety.
    """
    while True:
        # We also listen to the same tasks for parallel processing
        # In a real system, this would be a separate Kafka Consumer Group
        time.sleep(1) # Offset to simulate parallel flow
        # For simplicity, we'll just simulate a quick 1-second scan
        # (In reality, this worker would be triggered by the same initial Kafka message)
        pass

def finalizer_service():
    """
    Simulates the State Machine that updates the DB and Redis.
    """
    while True:
        update = kafka_status_updates.get()
        video_id = update['video_id']
        
        # In a real system, we'd wait for BOTH Transcode and Safety to finish.
        # For this mock, we assume Transcode is the main blocker.
        
        print(f"[Finalizer] Updating DB and Redis for video {video_id}...")
        
        # 1. Update Postgres (Permanent Record)
        postgres_db[video_id]['status'] = 'READY'
        postgres_db[video_id]['url'] = s3_storage["final"][video_id]
        
        # 2. Update Redis (Instant Feed Retrieval)
        redis_cache[video_id] = {
            "url": postgres_db[video_id]['url'],
            "author": postgres_db[video_id]['author'],
            "likes": 0
        }
        
        print(f"[Finalizer] Video {video_id} is now LIVE!")
        kafka_status_updates.task_done()

# --- API GATEWAY SIMULATION ---

def upload_video_api(user_id, file_name):
    """
    Simulates the user hitting the 'POST' button.
    """
    video_id = random.randint(1000, 9999)
    print(f"\n[API Gateway] Received upload from User {user_id}: {file_name}")
    
    # 1. Store in S3 Inbox
    raw_path = f"s3://raw-inbox/{file_name}"
    s3_storage["inbox"][video_id] = raw_path
    
    # 2. Create Initial DB Entry (Status: PENDING)
    postgres_db[video_id] = {
        "author": user_id,
        "status": "PENDING",
        "timestamp": time.time()
    }
    
    # 3. Drop into Kafka (The Belt)
    print(f"[API Gateway] Task queued for background workers (Video ID: {video_id}).")
    kafka_upload_tasks.put({"video_id": video_id, "path": raw_path})
    
    return video_id

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # Start background workers (Threads)
    threading.Thread(target=transcoder_worker, daemon=True).start()
    threading.Thread(target=finalizer_service, daemon=True).start()
    
    print("--- TIKTOK UPLOAD MOCK SYSTEM STARTED ---")
    
    # Simulate a user uploading a video
    vid_id = upload_video_api("user_zhang", "my_funny_cat.mp4")
    
    # Immediately check Redis (It should be empty because workers are still running)
    print(f"\n[Instant Check] Checking Redis for video {vid_id}...")
    print(f"Redis says: {redis_cache.get(vid_id, 'NOT_READY')}")
    
    # Wait for the workers to finish the 'Heavy' work
    print("\n[Wait] Waiting for background processing...")
    time.sleep(4)
    
    # Check Redis again (Now it should be ready)
    print(f"\n[Final Check] Checking Redis for video {vid_id}...")
    result = redis_cache.get(vid_id)
    if result:
        print(f"Video is LIVE! Manifest Link: {result['url']}")
        print(f"Full Redis Entry: {json.dumps(result, indent=2)}")
    
    print("\n--- SIMULATION COMPLETE ---")
