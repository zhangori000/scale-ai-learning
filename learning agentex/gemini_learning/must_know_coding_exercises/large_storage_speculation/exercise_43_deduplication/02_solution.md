# Solution: Content-Addressable Storage (Deduplication)

This is the technology behind `git` (the content-addressable database) and high-scale storage systems like Amazon S3 (internally).

## The Solution

```python
import hashlib

class DeduplicatingStorage:
    def __init__(self):
        self.phys_storage = {} 
        self.upload_count = 0

    def upload(self, content: str) -> str:
        # 1. Generate the 'Fingerprint' of the data
        content_bytes = content.encode()
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        
        uri = f"hash://{content_hash}"
        
        # 2. Check for existence (Deduplication)
        if content_hash not in self.phys_storage:
            print(f"  [Storage] First time seeing this content. Saving...")
            self.phys_storage[content_hash] = content
            self.upload_count += 1
        else:
            print(f"  [Storage] Content already exists (Cache Hit). Skipping upload.")
            
        return uri
```

## Why this is likely Scale AI's path:
1. **Massive Cost Savings**: For a platform with thousands of agents analyzing the same data sources (e.g., a shared corporate handbook), deduplication can reduce storage costs by 80-90%.
2. **Instant "Uploads"**: If the hash already exists, the "upload" happens in milliseconds because no data actually moves.
3. **Data Integrity**: Since the URI *is* the hash, you can verify that the file hasn't been tampered with by re-calculating the hash after download.
