import time
from typing import List, Any

class TicketmasterRedisClient:
    """
    Enhanced Redis Client supporting Lua scripts for atomic operations.
    """
    def __init__(self):
        self.storage = {} # Mock storage {key: (value, expiry)}
        self.active_sets = {} # Mock storage {key: set(user_ids)}

    def eval_lua(self, script_name: str, keys: List[str], args: List[Any]) -> Any:
        """
        Simulates Redis Lua execution. In a real system, this is one atomic
        operation on the Redis server.
        """
        key = keys[0]
        
        if script_name == "RELEASE_LOCK":
            # if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) end
            if self.get(key) == args[0]:
                return self.delete(key)
            return 0

        if script_name == "EXTEND_LOCK":
            # if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('expire', KEYS[1], ARGV[2]) end
            if self.get(key) == args[0]:
                return self.expire(key, args[1])
            return 0
        
        return None

    def sismember(self, key: str, member: str) -> bool:
        return member in self.active_sets.get(key, set())

    def set(self, key: str, value: str, nx=False, ex=None) -> bool:
        if nx and key in self.storage:
            return False
        self.storage[key] = (value, time.time() + (ex or 3600))
        return True

    def get(self, key: str) -> Any:
        val_tuple = self.storage.get(key)
        if not val_tuple: return None
        val, expiry = val_tuple
        if time.time() > expiry:
            del self.storage[key]
            return None
        return val

    def delete(self, key: str) -> int:
        if key in self.storage:
            del self.storage[key]
            return 1
        return 0

    def expire(self, key: str, seconds: int) -> int:
        if key in self.storage:
            val, _ = self.storage[key]
            self.storage[key] = (val, time.time() + seconds)
            return 1
        return 0
    
    def incr(self, key: str):
        pass
