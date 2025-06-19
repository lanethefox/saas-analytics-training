#!/usr/bin/env python3
"""
Test script to verify ML API can start
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    from models.churn_predictor import ChurnPredictor
    print("✓ ChurnPredictor imported successfully")
except Exception as e:
    print(f"✗ Failed to import ChurnPredictor: {e}")

try:
    from models.clv_predictor import CLVPredictor
    print("✓ CLVPredictor imported successfully")
except Exception as e:
    print(f"✗ Failed to import CLVPredictor: {e}")

try:
    from models.health_scorer import HealthScorer
    print("✓ HealthScorer imported successfully")
except Exception as e:
    print(f"✗ Failed to import HealthScorer: {e}")

try:
    from features.feature_service import FeatureService
    print("✓ FeatureService imported successfully")
except Exception as e:
    print(f"✗ Failed to import FeatureService: {e}")

try:
    from utils.database import DatabaseConnection
    print("✓ DatabaseConnection imported successfully")
except Exception as e:
    print(f"✗ Failed to import DatabaseConnection: {e}")

try:
    from utils.cache import CacheService
    print("✓ CacheService imported successfully")
except Exception as e:
    print(f"✗ Failed to import CacheService: {e}")

print("\nAll imports successful! The ML API should be able to start.")