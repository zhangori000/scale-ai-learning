# TikTok Feed & Playback: The Zero-Delay Secret

This document explains how TikTok achieves instant video starts and manages global bandwidth.

---

## 1. The Feed Request
When the app opens, it fetches the "Metadata Packet" for the first 5-10 videos.

**Request:** `GET /v1/feed?user_id=777`
**Response (Simplified JSON):**
```json
[
  {
    "video_id": "999",
    "manifest_url": "https://cdn.tiktok.com/999/manifest.m3u8",
    "preview_image": "https://cdn.tiktok.com/999/poster.jpg"
  },
  {
    "video_id": "888",
    "manifest_url": "https://cdn.tiktok.com/888/manifest.m3u8",
    "preview_image": "https://cdn.tiktok.com/888/poster.jpg"
  }
]
```

## 2. Zero-Delay Pillars

### A. Prefetching (Client-Side)
The mobile app maintains a **Pre-fetch Queue**. 
*   **Watch Video N:** The player plays the full buffer.
*   **Prefetch Video N+1:** The app downloads the first 2 seconds of the next video in the background.
*   **Prefetch Video N+2:** The app downloads the first 500KB of the 3rd video.

### B. Edge CDNs (The "Last Mile")
Videos are replicated to **Points of Presence (PoPs)**. 
*   **Cache Hit:** User in NYC gets the video from a server in Manhattan (5ms).
*   **Cache Miss:** Server in Manhattan fetches it from Virginia (50ms) and stores a copy for the next NYC user.

### C. Adaptive Bitrate (ABR)
The player monitors network speed every 2 seconds.
*   **Speed > 5Mbps:** Play 1080p.
*   **Speed < 1Mbps:** Seamlessly switch to 480p chunks. No spinner, just lower quality.

---

## 3. Data Flow
1. **App** -> **Feed Service** (Get List of URLs).
2. **App** -> **CDN** (Fetch first 2 seconds of Video 1 and Video 2).
3. **User Swipes** -> **Player** (Instantly switches to pre-fetched Video 2 buffer).
