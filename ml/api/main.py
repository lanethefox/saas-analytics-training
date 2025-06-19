"""
FastAPI ML Model Serving API
Provides endpoints for real-time model inference and predictions
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import redis
import json
import logging
from datetime import datetime, timedelta
import os

from ..models.churn_predictor import ChurnPredictor
from ..models.clv_predictor import CLVPredictor
from ..models.health_scorer import HealthScorer
from ..features.feature_service import FeatureService
from ..utils.database import DatabaseConnection
from ..utils.cache import CacheService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SaaS Analytics ML API",
    description="Machine Learning API for customer analytics and predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
db_service = None
cache_service = None
feature_service = None
churn_model = None
clv_model = None
health_model = None

@app.on_event("startup")
async def startup_event():
    """Initialize services and load models on startup"""
    global db_service, cache_service, feature_service, churn_model, clv_model, health_model
    
    try:
        # Initialize database connection
        db_service = DatabaseConnection()
        await db_service.connect()
        
        # Initialize cache service
        cache_service = CacheService()
        
        # Initialize feature service
        feature_service = FeatureService(db_service, cache_service)
        
        # Load ML models from MLflow
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
        
        # Load latest models
        churn_model = ChurnPredictor()
        await churn_model.load_latest_model()
        
        clv_model = CLVPredictor()
        await clv_model.load_latest_model()
        
        health_model = HealthScorer()
        await health_model.load_latest_model()
        
        logger.info("ML API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_service
    if db_service:
        await db_service.disconnect()

# Pydantic models for request/response
class CustomerChurnRequest(BaseModel):
    account_id: str
    features: Optional[Dict[str, Any]] = None

class CustomerChurnResponse(BaseModel):
    account_id: str
    churn_probability: float
    churn_risk_category: str
    risk_factors: List[str]
    prediction_timestamp: datetime

class CLVRequest(BaseModel):
    account_id: str
    forecast_months: int = 12
    
class CLVResponse(BaseModel):
    account_id: str
    predicted_clv: float
    confidence_interval: Dict[str, float]
    monthly_forecast: List[Dict[str, Any]]
    forecast_timestamp: datetime

class HealthScoreRequest(BaseModel):
    account_id: str
    
class HealthScoreResponse(BaseModel):
    account_id: str
    health_score: float
    health_category: str
    contributing_factors: Dict[str, float]
    recommendations: List[str]
    score_timestamp: datetime

class BatchPredictionRequest(BaseModel):
    account_ids: List[str]
    model_type: str  # 'churn', 'clv', 'health'
    
class BatchPredictionResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    processed_count: int
    error_count: int
    processing_time_ms: float

# Health check endpoint
@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": db_service.is_connected() if db_service else False,
            "cache": cache_service.is_connected() if cache_service else False,
            "models_loaded": all([churn_model, clv_model, health_model])
        }
    }

# Model information endpoints
@app.get("/models/info")
async def get_model_info():
    """Get information about loaded models"""
    return {
        "churn_model": {
            "version": churn_model.version if churn_model else None,
            "last_trained": churn_model.last_trained if churn_model else None,
            "performance_metrics": churn_model.performance_metrics if churn_model else None
        },
        "clv_model": {
            "version": clv_model.version if clv_model else None,
            "last_trained": clv_model.last_trained if clv_model else None,
            "performance_metrics": clv_model.performance_metrics if clv_model else None
        },
        "health_model": {
            "version": health_model.version if health_model else None,
            "last_trained": health_model.last_trained if health_model else None,
            "performance_metrics": health_model.performance_metrics if health_model else None
        }
    }

# Churn prediction endpoints
@app.post("/predict/churn", response_model=CustomerChurnResponse)
async def predict_churn(request: CustomerChurnRequest):
    """Predict customer churn probability"""
    try:
        if not churn_model:
            raise HTTPException(status_code=503, detail="Churn model not loaded")
        
        # Get features for the customer
        if request.features:
            features = request.features
        else:
            features = await feature_service.get_customer_features(request.account_id)
        
        if not features:
            raise HTTPException(status_code=404, detail="Customer features not found")
        
        # Make prediction
        prediction_result = await churn_model.predict(features)
        
        return CustomerChurnResponse(
            account_id=request.account_id,
            churn_probability=prediction_result["probability"],
            churn_risk_category=prediction_result["risk_category"],
            risk_factors=prediction_result["risk_factors"],
            prediction_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error predicting churn for {request.account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/clv", response_model=CLVResponse)
async def predict_clv(request: CLVRequest):
    """Predict customer lifetime value"""
    try:
        if not clv_model:
            raise HTTPException(status_code=503, detail="CLV model not loaded")
        
        # Get features for the customer
        features = await feature_service.get_customer_features(request.account_id)
        
        if not features:
            raise HTTPException(status_code=404, detail="Customer features not found")
        
        # Make prediction
        prediction_result = await clv_model.predict(features, request.forecast_months)
        
        return CLVResponse(
            account_id=request.account_id,
            predicted_clv=prediction_result["clv"],
            confidence_interval=prediction_result["confidence_interval"],
            monthly_forecast=prediction_result["monthly_forecast"],
            forecast_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error predicting CLV for {request.account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/health", response_model=HealthScoreResponse)
async def predict_health_score(request: HealthScoreRequest):
    """Calculate customer health score"""
    try:
        if not health_model:
            raise HTTPException(status_code=503, detail="Health model not loaded")
        
        # Get features for the customer
        features = await feature_service.get_customer_features(request.account_id)
        
        if not features:
            raise HTTPException(status_code=404, detail="Customer features not found")
        
        # Calculate health score
        health_result = await health_model.calculate_health_score(features)
        
        return HealthScoreResponse(
            account_id=request.account_id,
            health_score=health_result["score"],
            health_category=health_result["category"],
            contributing_factors=health_result["factors"],
            recommendations=health_result["recommendations"],
            score_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error calculating health score for {request.account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def batch_predictions(request: BatchPredictionRequest):
    """Run batch predictions for multiple customers"""
    start_time = datetime.utcnow()
    predictions = []
    error_count = 0
    
    try:
        for account_id in request.account_ids:
            try:
                features = await feature_service.get_customer_features(account_id)
                
                if not features:
                    error_count += 1
                    continue
                
                if request.model_type == "churn" and churn_model:
                    result = await churn_model.predict(features)
                    predictions.append({
                        "account_id": account_id,
                        "model_type": "churn",
                        "prediction": result
                    })
                elif request.model_type == "clv" and clv_model:
                    result = await clv_model.predict(features, 12)
                    predictions.append({
                        "account_id": account_id,
                        "model_type": "clv",
                        "prediction": result
                    })
                elif request.model_type == "health" and health_model:
                    result = await health_model.calculate_health_score(features)
                    predictions.append({
                        "account_id": account_id,
                        "model_type": "health",
                        "prediction": result
                    })
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing {account_id}: {e}")
                error_count += 1
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return BatchPredictionResponse(
            predictions=predictions,
            processed_count=len(predictions),
            error_count=error_count,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in batch predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Feature serving endpoints
@app.get("/features/{account_id}")
async def get_customer_features(account_id: str):
    """Get real-time features for a customer"""
    try:
        features = await feature_service.get_customer_features(account_id)
        
        if not features:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            "account_id": account_id,
            "features": features,
            "feature_timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting features for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/features/refresh/{account_id}")
async def refresh_customer_features(account_id: str):
    """Force refresh of customer features"""
    try:
        await feature_service.refresh_customer_features(account_id)
        
        return {
            "account_id": account_id,
            "status": "refreshed",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing features for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
