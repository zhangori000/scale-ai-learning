from __future__ import annotations
import asyncio
from typing import Dict, List, Set
from ..domain.entities import Interaction, InteractionType
from ..domain.exceptions import IdempotencyError, TargetNotFoundError

# --- Patterns from Scale-Agentex: Service-Oriented Logic ---

class InteractionService:
    def __init__(self):
        # Mocking Tier 1: Hot Cache (Redis)
        self.hot_counters: Dict[str, Dict[InteractionType, int]] = {}
        
        # Mocking Tier 2: Warm Storage (ScyllaDB/Cassandra)
        # Indexed by user_id for fast profile retrieval
        self.user_history: Dict[str, List[Interaction]] = {}
        
        # Mocking Idempotency Cache
        self.processed_requests: Set[str] = set()

    async def post_interaction(self, interaction: Interaction):
        """
        Simulate the write path: Kafka -> Flink -> Redis/Scylla.
        """
        # Step 1: Idempotency Check
        if interaction.request_id and interaction.request_id in self.processed_requests:
            print(f"[Interaction] Duplicate request {interaction.request_id}. Ignoring.")
            return # Silent fail or raise IdempotencyError

        if interaction.request_id:
            self.processed_requests.add(interaction.request_id)

        # Step 2: Push to Kafka (Simulated)
        print(f"[Kafka] Producing event: {interaction.type} for {interaction.target_id}")
        
        # Step 3: Flink/Redis Hot Path Update (Asynchronous)
        await self._update_hot_cache(interaction)
        
        # Step 4: Scylla Warm Path Update (Asynchronous)
        await self._update_warm_storage(interaction)

    async def _update_hot_cache(self, interaction: Interaction):
        # In reality, this happens in Flink, but we mock it here.
        await asyncio.sleep(0.01) # Mock Redis latency
        if interaction.target_id not in self.hot_counters:
            self.hot_counters[interaction.target_id] = {t: 0 for t in InteractionType}
        
        self.hot_counters[interaction.target_id][interaction.type] += 1
        print(f"[Redis] Incremented {interaction.type} for {interaction.target_id} to {self.hot_counters[interaction.target_id][interaction.type]}")

    async def _update_warm_storage(self, interaction: Interaction):
        # In reality, this happens in a Scylla-Sink worker.
        await asyncio.sleep(0.02) # Mock Scylla latency
        if interaction.user_id not in self.user_history:
            self.user_history[interaction.user_id] = []
        
        # Append to the list (Scylla writes are appends)
        self.user_history[interaction.user_id].append(interaction)
        print(f"[Scylla] Added {interaction.type} for {interaction.target_id} to user {interaction.user_id} history.")

    async def get_user_likes(self, user_id: str) -> List[Interaction]:
        """
        Fast retrieval from Scylla for the user's profile tab.
        """
        await asyncio.sleep(0.01)
        history = self.user_history.get(user_id, [])
        return [i for i in history if i.type == InteractionType.LIKE]
