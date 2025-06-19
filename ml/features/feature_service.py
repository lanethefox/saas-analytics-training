"""
Feature Service for real-time feature retrieval
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FeatureService:
    def __init__(self, db_service, cache_service):
        self.db = db_service
        self.cache = cache_service
        
    async def get_customer_features(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get all features for a customer"""
        try:
            # Check cache first
            cached_features = await self.cache.get(f"features:{account_id}")
            if cached_features:
                return cached_features
                
            # Mock feature retrieval
            features = {
                "account_id": account_id,
                "current_mrr": np.random.uniform(100, 1000),
                "growth_rate": np.random.uniform(-0.1, 0.3),
                "usage_rate": np.random.uniform(0.3, 1.0),
                "engagement_rate": np.random.uniform(0.2, 0.9),
                "support_tickets": np.random.randint(0, 10),
                "payment_status": np.random.choice(["current", "late", "overdue"]),
                "tenure_months": np.random.randint(1, 60),
                "user_count": np.random.randint(1, 100),
                "feature_adoption_rate": np.random.uniform(0.3, 1.0),
                "last_login_days": np.random.randint(0, 30),
                "industry": np.random.choice(["retail", "hospitality", "entertainment"]),
                "location_count": np.random.randint(1, 20)
            }
            
            # Cache features
            await self.cache.set(f"features:{account_id}", features, ttl=300)
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting features for {account_id}: {e}")
            return None
            
    async def refresh_customer_features(self, account_id: str):
        """Force refresh of customer features"""
        try:
            # Invalidate cache
            await self.cache.delete(f"features:{account_id}")
            
            # Re-fetch features
            return await self.get_customer_features(account_id)
            
        except Exception as e:
            logger.error(f"Error refreshing features for {account_id}: {e}")
            raise