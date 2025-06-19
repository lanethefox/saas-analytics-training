"""
Cache service for Redis integration
"""

import redis
import json
import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client = None
        self._connect()
        
    def _connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            self.client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            self.client = None
            
    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        try:
            if self.client:
                self.client.ping()
                return True
        except:
            pass
        return False
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
            
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
            
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.client:
            return
            
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.client:
            return
            
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")