"""
Customer Health Score Calculator
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthScorer:
    def __init__(self):
        self.model = None
        self.version = None
        self.last_trained = None
        self.performance_metrics = {}
        
    async def load_latest_model(self):
        """Load the latest health scoring model from MLflow"""
        try:
            # For now, use a mock model
            logger.info("Loading Health Scorer model")
            self.model = "mock_health_model"
            self.version = "1.0.0"
            self.last_trained = datetime.utcnow()
            self.performance_metrics = {
                "accuracy": 0.92,
                "precision": 0.89,
                "recall": 0.91
            }
            return True
        except Exception as e:
            logger.error(f"Error loading health model: {e}")
            return False
            
    async def calculate_health_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate customer health score"""
        try:
            # Mock health score calculation
            usage_score = min(features.get('usage_rate', 0.5) * 100, 100)
            engagement_score = min(features.get('engagement_rate', 0.5) * 100, 100)
            support_score = max(100 - features.get('support_tickets', 0) * 10, 0)
            payment_score = 100 if features.get('payment_status', 'current') == 'current' else 50
            
            # Calculate weighted average
            health_score = (
                usage_score * 0.3 +
                engagement_score * 0.3 +
                support_score * 0.2 +
                payment_score * 0.2
            )
            
            # Determine category
            if health_score >= 80:
                category = "Healthy"
            elif health_score >= 60:
                category = "At Risk"
            else:
                category = "Critical"
                
            # Generate recommendations
            recommendations = []
            if usage_score < 50:
                recommendations.append("Increase product adoption through training")
            if engagement_score < 50:
                recommendations.append("Schedule regular check-ins with customer")
            if support_score < 50:
                recommendations.append("Review and address support ticket backlog")
            if payment_score < 100:
                recommendations.append("Follow up on payment status")
                
            return {
                "score": health_score,
                "category": category,
                "factors": {
                    "usage": usage_score,
                    "engagement": engagement_score,
                    "support": support_score,
                    "payment": payment_score
                },
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            raise