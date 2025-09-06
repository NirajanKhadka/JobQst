"""
Minimal RedisQueue stub used in tests and components that expect a Redis-backed queue.
Implements an in-memory async-compatible interface to avoid external Redis dependency in tests.
"""

import asyncio
import json
from typing import Any, Optional


class _InMemoryRedis:
    def __init__(self):
        # Simple dict of list queues
        self._lists = {}

    async def llen(self, name: str) -> int:
        return len(self._lists.get(name, []))

    async def lrange(self, name: str, start: int, end: int):
        data = self._lists.get(name, [])
        # end is inclusive in Redis
        if end == -1:
            end = len(data) - 1
        return data[start:end + 1]

    async def lindex(self, name: str, index: int):
        data = self._lists.get(name, [])
        try:
            return data[index]
        except IndexError:
            return None

    async def lrem(self, name: str, count: int, value: Any):
        # Remove up to count occurrences
        items = self._lists.get(name, [])
        removed = 0
        new_items = []
        for item in items:
            if removed < count and item == value:
                removed += 1
                continue
            new_items.append(item)
        self._lists[name] = new_items
        return removed

    async def rpush(self, name: str, value: Any):
        self._lists.setdefault(name, []).append(value)
        return len(self._lists[name])


class RedisQueue:
    def __init__(self, queue_name: str = "jobs:main"):
        self.queue_name = queue_name
        self.deadletter_name = f"{queue_name}:deadletter"
        self.redis: Optional[_InMemoryRedis] = None

    async def connect(self):
        if self.redis is None:
            self.redis = _InMemoryRedis()

    async def close(self):
        # No-op for in-memory stub
        pass

    async def enqueue(self, item: dict):
        await self.connect()
        await self.redis.rpush(self.queue_name, json.dumps(item))

    async def dequeue(self, timeout: int = 0) -> Optional[dict]:
        await self.connect()
        # Simulate blocking pop with polling if timeout > 0
        end_time = asyncio.get_event_loop().time() + timeout
        while True:
            if await self.redis.llen(self.queue_name) > 0:
                items = await self.redis.lrange(self.queue_name, 0, 0)
                first = items[0]
                await self.redis.lrem(self.queue_name, 1, first)
                try:
                    return json.loads(first)
                except Exception:
                    return None
            if timeout <= 0 or asyncio.get_event_loop().time() >= end_time:
                return None
            await asyncio.sleep(0.1)

    async def move_to_deadletter(self, item: dict):
        await self.connect()
        await self.redis.rpush(self.deadletter_name, json.dumps(item))

