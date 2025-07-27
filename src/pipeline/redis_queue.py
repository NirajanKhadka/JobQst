import os
import json
from typing import Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    try:
        import aioredis
    except ImportError:
        aioredis = None

class RedisQueue:
    def __init__(self, queue_name: str, deadletter_name: Optional[str] = None):
        self.queue_name = queue_name
        self.deadletter_name = deadletter_name or f"{queue_name}:deadletter"
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = None

    async def connect(self):
        if not self.redis:
            if aioredis is None:
                raise ImportError("Redis client not available. Install redis or aioredis package.")
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)

    async def enqueue(self, job: dict):
        await self.connect()
        await self.redis.rpush(self.queue_name, json.dumps(job))

    async def dequeue(self, timeout: int = 5) -> Optional[dict]:
        await self.connect()
        job = await self.redis.blpop(self.queue_name, timeout=timeout)
        if job:
            _, data = job
            return json.loads(data)
        return None

    async def move_to_deadletter(self, job: dict):
        await self.connect()
        await self.redis.rpush(self.deadletter_name, json.dumps(job))

    async def close(self):
        if self.redis:
            await self.redis.close()
            self.redis = None
