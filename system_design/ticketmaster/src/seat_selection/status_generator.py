import json
import time
import zlib
import logging
from typing import Dict, List

class StatusGenerator:
    """
    Generates the 'Status Overlay' file (Layer 2) every second.
    This file is pushed to the CDN with a 1s TTL.
    """
    def __init__(self, redis_client, cdn_client, event_id="bruno_mars_2026"):
        self.redis = redis_client
        self.cdn = cdn_client
        self.event_id = event_id
        self.total_seats = 60000
        self.version = 0

    def generate_bitmask(self) -> bytes:
        """
        Encodes 60,000 seats into a compact bitmask.
        Each seat uses 2 bits: 0=Available, 1=Locked, 2=Sold.
        """
        # In a real system, we'd use a more efficient bit-packing library (like bitarray)
        # Here we simulate the process.
        bitmask = bytearray(15000) # 60k seats * 2 bits / 8 bits per byte
        
        # We fetch all locked keys from Redis (e.g. using SCAN or a dedicated set)
        # For the mock, let's assume we have a list of seat_ids.
        for i in range(self.total_seats):
            status = self._get_seat_status(i) # 0, 1, or 2
            byte_idx = (i * 2) // 8
            bit_offset = (i * 2) % 8
            bitmask[byte_idx] |= (status << bit_offset)
        
        return zlib.compress(bitmask)

    def _get_seat_status(self, seat_idx: int) -> int:
        """
        MOCK logic:
        0 = Available
        1 = Locked (Found in Redis seat_lock:ID)
        2 = Sold (Found in DB/Sold Set)
        """
        return 0 # Simplified for design

    def run_cycle(self):
        """
        Main loop: Read -> Compress -> Push to CDN.
        """
        self.version += 1
        compressed_data = self.generate_bitmask()
        
        # We push to a unique versioned URL to avoid stale cache issues at the edge.
        filename = f"status/{self.event_id}/v{self.version}.bin"
        self.cdn.upload(filename, compressed_data, ttl=1)
        
        # Update the 'latest' pointer (also cached for 1s)
        self.cdn.upload(f"status/{self.event_id}/latest.json", json.dumps({
            "version": self.version,
            "url": filename,
            "timestamp": time.time()
        }), ttl=1)

        logging.info(f"Generated status version {self.version}. Size: {len(compressed_data)} bytes.")

class MockCDN:
    def upload(self, path, data, ttl):
        # Simulation: Pushing to S3/Cloudflare KV
        pass
