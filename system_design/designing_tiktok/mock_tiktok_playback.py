import time
import random

# --- MOCK SERVER-SIDE ---

# Mock Redis (What we built in Part 1/2)
redis_metadata = {
    101: {"id": 101, "url": "https://cdn.tk.com/v101.m3u8", "title": "Funny Dog"},
    102: {"id": 102, "url": "https://cdn.tk.com/v102.m3u8", "title": "Pizza Recipe"},
    103: {"id": 103, "url": "https://cdn.tk.com/v103.m3u8", "title": "Skateboard Trick"},
    104: {"id": 104, "url": "https://cdn.tk.com/v104.m3u8", "title": "NYC Sunset"},
    105: {"id": 105, "url": "https://cdn.tk.com/v105.m3u8", "title": "Coding Tips"}
}

def get_feed_api(user_id):
    """
    Simulates the Feed Service.
    Returns the metadata for the next 5 videos.
    """
    print(f"\n[Feed Service] Generating feed for User {user_id}...")
    # In reality, this would talk to the Recommendation Engine.
    # Here, we just pick 5 random videos from our Redis mock.
    video_ids = list(redis_metadata.keys())
    random.shuffle(video_ids)
    
    feed = [redis_metadata[vid] for vid in video_ids[:5]]
    return feed

# --- MOCK CLIENT-SIDE (The Phone) ---

class TikTokPlayer:
    def __init__(self, user_id):
        self.user_id = user_id
        self.feed_queue = []
        self.current_index = 0
        self.buffer = {}  # Mock Local Phone Memory (RAM)

    def fetch_feed(self):
        """Step 1: Get the list of video pointers from the server."""
        self.feed_queue = get_feed_api(self.user_id)
        print(f"[Phone] Received {len(self.feed_queue)} video URLs.")

    def prefetch_next_videos(self):
        """Step 2: Prefetch the first few seconds of upcoming videos."""
        # Prefetch the next 2 videos in the list
        for i in range(self.current_index + 1, self.current_index + 3):
            if i < len(self.feed_queue):
                video = self.feed_queue[i]
                if video['id'] not in self.buffer:
                    print(f"[Phone: Prefetch] Downloading first 2s of Video {video['id']} ({video['title']})...")
                    time.sleep(0.5)  # Simulate network trip to CDN
                    self.buffer[video['id']] = "READY_IN_RAM"

    def play_video(self):
        """Step 3: Play the video."""
        video = self.feed_queue[self.current_index]
        
        # Check if it was prefetched
        start_time = time.time()
        if self.buffer.get(video['id']) == "READY_IN_RAM":
            load_time = (time.time() - start_time) * 1000  # ms
            print(f"\n[Player] PLAYING: {video['title']} (ID: {video['id']})")
            print(f">>> ZERO DELAY! (Loaded from RAM in {load_time:.2f}ms)")
        else:
            # Cold load
            print(f"\n[Player] PLAYING: {video['title']} (ID: {video['id']})")
            print(">>> [Lag] Video not in buffer. Fetching from CDN...")
            time.sleep(1.5)  # Simulate cold network delay
            print(">>> [Ready] Video started after 1500ms.")

    def swipe(self):
        """User swipes up."""
        print("\n--- [User Swipe Up] ---")
        self.current_index += 1
        if self.current_index >= len(self.feed_queue):
            print("[System] End of feed. Fetching more...")
            self.fetch_feed()
            self.current_index = 0
        
        self.play_video()
        self.prefetch_next_videos()

# --- RUN SIMULATION ---

if __name__ == "__main__":
    print("--- TIKTOK FEED & PLAYBACK SIMULATION ---")
    
    player = TikTokPlayer("user_zhang")
    
    # Initial Start
    player.fetch_feed()
    
    # The very first video might have a tiny delay because nothing is prefetched yet
    player.play_video()
    
    # Now start prefetching while the user watches the first video
    player.prefetch_next_videos()
    
    # User swiping!
    time.sleep(2) # User watches for a bit
    player.swipe()
    
    time.sleep(2) # User watches for a bit
    player.swipe()
    
    time.sleep(2) # User watches for a bit
    player.swipe()
    
    print("\n--- SIMULATION COMPLETE ---")
