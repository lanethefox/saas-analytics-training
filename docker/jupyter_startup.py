#!/usr/bin/env python3
"""
Jupyter Startup Script for SaaS Analytics Platform
Initializes common imports, database connections, and helper functions
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ML and stats
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier, CatBoostRegressor
import optuna
import shap
import mlflow
import mlflow.sklearn

# Database and data tools
import psycopg2
from sqlalchemy import create_engine
import redis
import duckdb

# Time series and forecasting
from prophet import Prophet
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose

# Utility imports
import os
import sys
import warnings
import logging
from datetime import datetime, timedelta
import json

# Configure display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', None)
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection helper
def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host="postgres",
        database="saas_platform_dev",
        user="saas_user", 
        password="saas_secure_password_2024"
    )

# SQLAlchemy engine helper
def get_db_engine():
    """Get SQLAlchemy engine for pandas"""
    return create_engine(
        "postgresql://saas_user:saas_secure_password_2024@postgres:5432/saas_platform_dev"
    )

# Redis connection helper
def get_redis_connection():
    """Get Redis connection"""
    return redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Common query helper
def query_db(sql, engine=None):
    """Execute SQL query and return DataFrame"""
    if engine is None:
        engine = get_db_engine()
    return pd.read_sql(sql, engine)

# Entity data helpers
def get_customers(limit=1000):
    """Get customer data from entity_customers table"""
    sql = f"SELECT * FROM entity_customers LIMIT {limit}"
    return query_db(sql)

def get_devices(limit=1000):
    """Get device data from entity_devices table"""
    sql = f"SELECT * FROM entity_devices LIMIT {limit}"
    return query_db(sql)

def get_subscriptions(limit=1000):
    """Get subscription data from entity_subscriptions table"""
    sql = f"SELECT * FROM entity_subscriptions LIMIT {limit}"
    return query_db(sql)

# MLflow helpers
def setup_mlflow():
    """Configure MLflow tracking"""
    mlflow.set_tracking_uri("http://mlflow:5000")
    return mlflow

# Print startup message
print("🚀 SaaS Analytics Platform - Jupyter Environment Ready!")
print("=" * 60)
print("📊 Database connections configured")
print("🤖 ML libraries imported")
print("📈 Visualization tools ready")
print("🔧 Helper functions available:")
print("   - get_db_connection() / get_db_engine()")
print("   - get_redis_connection()")
print("   - query_db(sql)")
print("   - get_customers() / get_devices() / get_subscriptions()")
print("   - setup_mlflow()")
print("=" * 60)
print("💡 Ready for Entity-Centric Analytics!")
