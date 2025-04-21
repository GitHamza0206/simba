import redis.asyncio as redis
import json
from typing import Optional, Any

class RedisService:
    def __init__(self):
        self.redis = None
        
    async def init(self):
        """Initialize Redis connection"""
        self.redis = redis.from_url(
            f"redis://localhost:6379",
            decode_responses=True
        )
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.redis:
            await self.init()
        value = await self.redis.get(key)
        return json.loads(value) if value else None
        
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in Redis with TTL"""
        if not self.redis:
            await self.init()
        await self.redis.set(key, json.dumps(value), ex=ttl)
        
    async def delete(self, key: str):
        """Delete value from Redis"""
        if not self.redis:
            await self.init()
        await self.redis.delete(key)
        
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.redis:
            await self.init()
        return await self.redis.exists(key) > 0 