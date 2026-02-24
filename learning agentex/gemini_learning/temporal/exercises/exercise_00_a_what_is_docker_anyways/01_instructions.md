# Exercise: Build a Mock Docker Engine

Docker is essentially **"A Zip file with an extra set of instructions on how to run it."**

## The Problem (Why Docker exists)
Imagine developer Alice has Python 3.10 and database version A. Developer Bob has Python 3.12 and database version B. Alice's Temporal code crashes on Bob's computer because "the versions are different."

## The Goal
In this exercise, we will build a "Docker Engine" in pure Python.

## Core Concepts (The Mocks)
1.  **The Image (The Blueprint):** A dictionary that stores the Code, the Python Version, and the Environment Variables.
2.  **The Registry (The Warehouse):** A place (a dictionary) where we "push" and "pull" Images from.
3.  **The Container (The Instance):** A "running" copy of an image. It has its own unique "ID" and "Port."
4.  **The Engine (The System):** The code that can `pull` an image and `run` it into a Container.

## The Task
Complete the `DockerEngine.run()` method. It should take an image from the registry, "boot it up" as a Container, and assign it a unique ID.

## Starter Code
```python
import uuid

# --- 1. The Image (A Blueprint) ---
class DockerImage:
    def __init__(self, name, code, env_vars=None):
        self.name = name
        self.code = code  # The "Temporal Brain" code
        self.env_vars = env_vars or {}

# --- 2. The Registry (The Warehouse) ---
REGISTRY = {
    "temporal-server": DockerImage(
        name="temporal-server",
        code="print('--- [TEMPORAL BRAIN] Running on port 7233 ---')",
        env_vars={"DB_TYPE": "postgres"}
    )
}

# --- 3. The Container (A Running Instance) ---
class Container:
    def __init__(self, container_id, image, port_mapping):
        self.id = container_id
        self.image = image
        self.port_mapping = port_mapping # e.g. "8000:7233"
        self.is_running = False

    def start(self):
        print(f"[CONTAINER {self.id}] Starting image: {self.image.name}...")
        print(f"[CONTAINER {self.id}] Environment: {self.image.env_vars}")
        exec(self.image.code) # Simulate running the code inside the box
        self.is_running = True

# --- 4. The Docker Engine (The Controller) ---
class DockerEngine:
    def __init__(self):
        self.active_containers = {}

    def run(self, image_name, host_port):
        """
        TODO:
        1. Check if image_name exists in REGISTRY.
        2. If it does, 'pull' the image.
        3. Create a new Container object.
        4. Generate a unique ID for it (use uuid.uuid4()).
        5. Map the 'host_port' to the internal image port (let's say 7233).
        6. Start the container and add it to self.active_containers.
        """
        pass

# --- 5. Execution ---
engine = DockerEngine()

print("--- Step 1: Alice runs the Temporal Brain on Port 7233 ---")
engine.run("temporal-server", host_port=7233)

print("
--- Step 2: Bob runs ANOTHER Temporal Brain on Port 9000 ---")
engine.run("temporal-server", host_port=9000)
```

---
### When you are ready, check the solution file!
