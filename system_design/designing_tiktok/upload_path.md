# TikTok Upload Architecture: The Fast Path

This document outlines the specialized "Upload Pipeline" for TikTok, focusing on durability, speed, and parallel processing.

---

## 1. High-Level Pipeline (The Flow)

The upload path is not a single step. It is a **State Machine** that moves a video from "Raw" to "Ready."

### Stage A: Ingest (The Gateway)
1. **API Ingest:** The user's phone sends a raw `.mp4` file (e.g., 20MB).
2. **S3 Inbox:** The file is immediately saved in a "Raw" S3 bucket.
3. **Database Entry:** A row is created in the **Postgres Video Shard** with `status: PENDING`.
4. **Kafka Trigger:** A message is dropped into the `upload_tasks` Kafka topic: `{"video_id": 999, "bucket_path": "s3://raw/vid999.mp4"}`.

### Stage B: Parallel Processing (The Workers)
Multiple specialized worker fleets listen to the same Kafka message:

*   **Fleet 1: Transcoders (The Choppers):**
    *   Chops the video into **2-second segments**.
    *   Creates 3 resolutions: **1080p, 720p, 480p**.
    *   Saves the **90 resulting files** (30 chunks * 3 resolutions) to the "Ready" S3 bucket.
*   **Fleet 2: Safety & Copyright (The Guards):**
    *   Scans frames for nudity/violence.
    *   Fingerprints the audio to check for copyrighted music.

### Stage C: Finalization (The Ready Flag)
1. **State Collector:** A service waits for "Success" messages from both the Transcoder and Safety fleets.
2. **Postgres Update:** The `status` is flipped to `READY`.
3. **Redis Push:** The **Manifest URL** (the HLS `.m3u8` file) is saved in **Redis** for instant feed retrieval.

---

## 2. Infrastructure Math (Peak Load)

*   **Peak Traffic:** 1,000 uploads per second.
*   **Transcoding Delay:** 10 seconds per video.
*   **Worker Fleet:** ~10,000 concurrent "Worker Slots" (on specialized ASICs/GPUs).
*   **Kafka Partitions:** 100+ partitions to ensure one "Lame" worker doesn't block the whole world.

## 3. The "Zero Delay" Secret
The uploader sees the video on their profile **immediately** because the app plays the **Local File** from their phone's memory. The rest of the world only sees the video once the `READY` flag is set in the database (approx. 5-15 seconds later).
