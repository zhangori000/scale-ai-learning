# Solution: Build a Mock Docker Engine

This solution demonstrates that Docker is just a **management system** that takes a static blueprint (the Image) and turns it into a living, running process (the Container).

## The Implementation

```python
import uuid

# --- 1. The Image (A Blueprint) ---
class DockerImage:
    def __init__(self, name, code, env_vars=None):
        self.name = name
        self.code = code  # The static "Temporal Brain" code
        self.env_vars = env_vars or {}

# --- 2. The Registry (The Warehouse) ---
# Imagine this is 'Docker Hub' (the website where you pull images from)
REGISTRY = {
    "temporal-server": DockerImage(
        name="temporal-server",
        code="print('  -> [TEMPORAL BRAIN] Running on port 7233...')",
        env_vars={"DB_TYPE": "postgres", "VERSION": "1.23.0"}
    ),
    "postgres-db": DockerImage(
        name="postgres-db",
        code="print('  -> [DATABASE] Listening for queries...')",
        env_vars={"DB_USER": "root"}
    )
}

# --- 3. The Container (A Running Instance) ---
class Container:
    def __init__(self, container_id, image, host_port, container_port):
        self.id = container_id
        self.image = image
        self.host_port = host_port
        self.container_port = container_port
        self.is_running = False

    def start(self):
        print(f"
[CONTAINER {self.id}] Status: BOOTING UP")
        print(f"[CONTAINER {self.id}] Mapping Host Port {self.host_port} to Internal Port {self.container_port}")
        print(f"[CONTAINER {self.id}] Loading Image: {self.image.name}")
        print(f"[CONTAINER {self.id}] Loading Environment Variables: {self.image.env_vars}")
        
        # This simulates the "isolated" process running the code
        # In real Docker, it's a separate Linux process. Here, it's just 'exec()'.
        exec(self.image.code)
        
        self.is_running = True
        print(f"[CONTAINER {self.id}] Status: RUNNING (Healthy)")

# --- 4. The Docker Engine (The Controller) ---
class DockerEngine:
    def __init__(self):
        self.active_containers = {}

    def run(self, image_name, host_port):
        """
        The key logic for 'docker run -p 7233:7233 temporal-server'
        """
        # 1. Pull the image from the registry (Docker Hub)
        if image_name not in REGISTRY:
            print(f"[ENGINE ERROR] Image '{image_name}' not found in registry!")
            return None
        
        image = REGISTRY[image_name]
        print(f"[ENGINE] Pulled image '{image_name}' (Size: 200MB)")

        # 2. Create a new Container (The 'instance')
        # Each one gets a unique 'id' so we can manage them.
        container_id = str(uuid.uuid4())[:8] # Short unique ID like 'a1b2c3d4'
        
        # 3. Port Mapping: The 'Internal' port 7233 doesn't change, 
        # but the 'External' (Host) port can be anything.
        new_container = Container(
            container_id=container_id,
            image=image,
            host_port=host_port,
            container_port=7233 # The internal Temporal port
        )

        # 4. Start it!
        new_container.start()
        
        # 5. Keep track of it in memory
        self.active_containers[container_id] = new_container
        return container_id

# --- 5. Execution ---
engine = DockerEngine()

# Alice runs the 'brain' on its standard port 7233
print("--- Alice's Server (Running Temporal) ---")
id_1 = engine.run("temporal-server", host_port=7233)

# Bob wants to run a DIFFERENT 'brain' on his computer. 
# He doesn't want it to conflict with Alice's port, so he uses 9000.
# BUT, inside the box, the code still thinks it's on 7233! This is the magic of Docker.
print("
--- Bob's Server (Running a second Temporal) ---")
id_2 = engine.run("temporal-server", host_port=9000)

# We can even run the Database as well!
print("
--- Running the Postgres Database ---")
id_3 = engine.run("postgres-db", host_port=5432)

print(f"
Total active containers: {len(engine.active_containers)}")
```

### Key Takeaways

1.  **Isolation:** When you run `temporal-server` on Alice's machine and Bob's machine, they are the **same folder** (the Image) but **different processes** (the Containers).
2.  **Immutability:** You cannot "change" an image. If you want to change the Temporal code, you build a **new image** and "push" it. Then everyone else "pulls" the update.
3.  **Port Mapping:** Notice how the `host_port` can change (7233 vs 9000), but the code *inside* the box always sees 7233. This prevents "Address already in use" errors between different apps!
4.  **Why we use it for Temporal:** Temporal needs a lot of "friends" to run (Postgres, ElasticSearch, etc.). Instead of making you install all of those manually, the Scale team just gives you a `docker-compose.yml` file that "pulls" all of those pre-built images for you.
