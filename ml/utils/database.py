"""
Database connection utilities
"""

import asyncpg
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv("DATABASE_URL", "postgresql://saas_user:saas_secure_password_2024@postgres:5432/saas_platform_dev")
        
    async def connect(self):
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Error creating database pool: {e}")
            raise
            
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
            
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self.pool is not None
        
    async def execute_query(self, query: str, *args) -> Optional[Any]:
        """Execute a database query"""
        if not self.pool:
            raise Exception("Database not connected")
            
        async with self.pool.acquire() as connection:
            try:
                result = await connection.fetch(query, *args)
                return result
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                raise