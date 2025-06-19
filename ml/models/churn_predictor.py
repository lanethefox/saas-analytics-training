"""
Customer Churn Prediction Model
Advanced ensemble model using XGBoost and LightGBM for churn prediction
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
import optuna
import shap
import joblib
import logging

logger = logging.getLogger(__name__)

class ChurnPredictor:
    """
    Advanced churn prediction model using ensemble methods
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.version = None
        self.last_trained = None
        self.performance_metrics = None
        self.shap_explainer = None
        
    async def load_latest_model(self):
        """Load the latest trained model from MLflow"""
        try:
            client = mlflow.tracking.MlflowClient()
            latest_version = client.get_latest_versions("churn_prediction_model", stages=["Production"])
            
            if latest_version:
                model_version = latest_version[0].version
                model_uri = f"models:/churn_prediction_model/{model_version}"
                
                # Load model and artifacts
                self.model = mlflow.sklearn.load_model(model_uri)
                
                # Load additional artifacts
                run_id = latest_version[0].run_id
                artifacts_path = f"runs:/{run_id}"
                
                self.scaler = mlflow.artifacts.load_dict(f"{artifacts_path}/scaler.pkl")
                self.feature_names = mlflow.artifacts.load_dict(f"{artifacts_path}/feature_names.json")
                self.performance_metrics = mlflow.artifacts.load_dict(f"{artifacts_path}/metrics.json")
                
                self.version = model_version
                logger.info(f"Loaded churn model version {model_version}")
                
                # Initialize SHAP explainer
                self.shap_explainer = shap.Explainer(self.model)
                
            else:
                logger.warning("No production churn model found, training new model")
                await self.train_model()
                
        except Exception as e:
            logger.error(f"Error loading churn model: {e}")
            # Fallback to training a new model
            await self.train_model()
    
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make churn prediction for a customer
        
        Args:
            features: Dictionary of customer features
            
        Returns:
            Dictionary with prediction results
        """
        try:
            if not self.model:
                raise ValueError("Model not loaded")
            
            # Convert features to DataFrame
            feature_df = pd.DataFrame([features])
            
            # Ensure all required features are present
            for feature in self.feature_names:
                if feature not in feature_df.columns:
                    feature_df[feature] = 0  # Default value for missing features
            
            # Select and order features
            feature_df = feature_df[self.feature_names]
            
            # Scale features
            if self.scaler:
                feature_array = self.scaler.transform(feature_df)
            else:
                feature_array = feature_df.values
            
            # Make prediction
            churn_probability = self.model.predict_proba(feature_array)[0][1]
            
            # Determine risk category
            if churn_probability >= 0.8:
                risk_category = "critical_risk"
            elif churn_probability >= 0.6:
                risk_category = "high_risk"
            elif churn_probability >= 0.4:
                risk_category = "medium_risk"
            elif churn_probability >= 0.2:
                risk_category = "low_risk"
            else:
                risk_category = "minimal_risk"
            
            # Get SHAP explanations for risk factors
            risk_factors = []
            if self.shap_explainer:
                try:
                    shap_values = self.shap_explainer(feature_array)
                    feature_importance = dict(zip(self.feature_names, shap_values.values[0]))
                    
                    # Get top risk factors (positive SHAP values contributing to churn)
                    top_risk_factors = sorted(
                        [(k, v) for k, v in feature_importance.items() if v > 0],
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    
                    risk_factors = [
                        self._interpret_risk_factor(factor, value) 
                        for factor, value in top_risk_factors
                    ]
                    
                except Exception as e:
                    logger.warning(f"Error generating SHAP explanations: {e}")
                    risk_factors = ["Unable to generate detailed risk factors"]
            
            return {
                "probability": float(churn_probability),
                "risk_category": risk_category,
                "risk_factors": risk_factors,
                "model_version": self.version
            }
            
        except Exception as e:
            logger.error(f"Error making churn prediction: {e}")
            raise
    
    def _interpret_risk_factor(self, factor: str, shap_value: float) -> str:
        """Convert SHAP values to human-readable risk factors"""
        risk_factor_mapping = {
            "days_since_last_activity": "Extended period of inactivity",
            "device_events_30d": "Low device usage",
            "payment_failures_30d": "Recent payment issues",
            "support_tickets_30d": "High support ticket volume",
            "feature_usage_decline": "Decreased feature adoption",
            "billing_amount_change": "Billing disputes or downgrades",
            "user_engagement_score": "Low user engagement",
            "device_health_score": "Poor device performance",
            "subscription_age_days": "Early in subscription lifecycle",
            "mrr_change_30d": "Revenue contraction"
        }
        
        return risk_factor_mapping.get(factor, f"High {factor.replace('_', ' ')}")
    
    async def train_model(self, data: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """
        Train the churn prediction model
        
        Args:
            data: Training data (if None, will load from database)
            
        Returns:
            Dictionary with training metrics
        """
        try:
            # Start MLflow run
            with mlflow.start_run():
                logger.info("Starting churn model training")
                
                # Load training data if not provided
                if data is None:
                    data = await self._load_training_data()
                
                # Prepare features and target
                X, y = self._prepare_training_data(data)
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )
                
                # Scale features
                self.scaler = StandardScaler()
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)
                
                # Optimize hyperparameters
                best_params = await self._optimize_hyperparameters(X_train_scaled, y_train)
                
                # Train ensemble model
                self.model = self._create_ensemble_model(best_params)
                self.model.fit(X_train_scaled, y_train)
                
                # Evaluate model
                y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
                y_pred = self.model.predict(X_test_scaled)
                
                metrics = {
                    "auc": roc_auc_score(y_test, y_pred_proba),
                    "precision": precision_score(y_test, y_pred),
                    "recall": recall_score(y_test, y_pred),
                    "f1": f1_score(y_test, y_pred)
                }
                
                self.performance_metrics = metrics
                self.feature_names = list(X.columns)
                self.version = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.last_trained = datetime.now()
                
                # Log to MLflow
                mlflow.log_params(best_params)
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(
                    self.model, 
                    "model",
                    registered_model_name="churn_prediction_model"
                )
                
                # Log artifacts
                mlflow.log_artifact(joblib.dump(self.scaler, "scaler.pkl"), "scaler.pkl")
                mlflow.log_artifact(self.feature_names, "feature_names.json")
                mlflow.log_artifact(metrics, "metrics.json")
                
                logger.info(f"Churn model training completed. AUC: {metrics['auc']:.3f}")
                
                return metrics
                
        except Exception as e:
            logger.error(f"Error training churn model: {e}")
            raise
    
    def _create_ensemble_model(self, params: Dict[str, Any]) -> VotingClassifier:
        """Create ensemble model with optimized parameters"""
        
        # XGBoost model
        xgb_model = xgb.XGBClassifier(
            n_estimators=params.get("xgb_n_estimators", 200),
            max_depth=params.get("xgb_max_depth", 6),
            learning_rate=params.get("xgb_learning_rate", 0.1),
            subsample=params.get("xgb_subsample", 0.8),
            colsample_bytree=params.get("xgb_colsample_bytree", 0.8),
            random_state=42
        )
        
        # LightGBM model
        lgb_model = lgb.LGBMClassifier(
            n_estimators=params.get("lgb_n_estimators", 200),
            max_depth=params.get("lgb_max_depth", 6),
            learning_rate=params.get("lgb_learning_rate", 0.1),
            subsample=params.get("lgb_subsample", 0.8),
            colsample_bytree=params.get("lgb_colsample_bytree", 0.8),
            random_state=42,
            verbose=-1
        )
        
        # Create ensemble
        ensemble = VotingClassifier(
            estimators=[
                ("xgb", xgb_model),
                ("lgb", lgb_model)
            ],
            voting="soft"
        )
        
        return ensemble
    
    async def _optimize_hyperparameters(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Optimize hyperparameters using Optuna"""
        
        def objective(trial):
            params = {
                # XGBoost parameters
                "xgb_n_estimators": trial.suggest_int("xgb_n_estimators", 100, 300),
                "xgb_max_depth": trial.suggest_int("xgb_max_depth", 3, 10),
                "xgb_learning_rate": trial.suggest_float("xgb_learning_rate", 0.01, 0.3),
                "xgb_subsample": trial.suggest_float("xgb_subsample", 0.6, 1.0),
                "xgb_colsample_bytree": trial.suggest_float("xgb_colsample_bytree", 0.6, 1.0),
                
                # LightGBM parameters
                "lgb_n_estimators": trial.suggest_int("lgb_n_estimators", 100, 300),
                "lgb_max_depth": trial.suggest_int("lgb_max_depth", 3, 10),
                "lgb_learning_rate": trial.suggest_float("lgb_learning_rate", 0.01, 0.3),
                "lgb_subsample": trial.suggest_float("lgb_subsample", 0.6, 1.0),
                "lgb_colsample_bytree": trial.suggest_float("lgb_colsample_bytree", 0.6, 1.0),
            }
            
            model = self._create_ensemble_model(params)
            cv_scores = cross_val_score(model, X, y, cv=3, scoring="roc_auc")
            return cv_scores.mean()
        
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=50)
        
        return study.best_params
    
    async def _load_training_data(self) -> pd.DataFrame:
        """Load training data from the data warehouse"""
        # This would typically load from the entity tables created by dbt
        # For now, return a placeholder
        logger.info("Loading training data from data warehouse")
        # Implementation would connect to PostgreSQL and load from entity_customers
        # and related tables with historical data
        return pd.DataFrame()
    
    def _prepare_training_data(self, data: pd.DataFrame) -> tuple:
        """Prepare features and target for training"""
        # Define feature columns and target
        feature_columns = [
            "days_since_last_activity",
            "device_events_30d", 
            "user_engagement_score",
            "payment_success_rate",
            "support_tickets_30d",
            "feature_usage_count",
            "subscription_age_days",
            "mrr_change_30d",
            "device_health_score",
            "location_count"
        ]
        
        # For demonstration, create synthetic features
        np.random.seed(42)
        n_samples = 10000
        
        X = pd.DataFrame({
            "days_since_last_activity": np.random.exponential(5, n_samples),
            "device_events_30d": np.random.poisson(100, n_samples),
            "user_engagement_score": np.random.beta(2, 5, n_samples),
            "payment_success_rate": np.random.beta(8, 2, n_samples),
            "support_tickets_30d": np.random.poisson(2, n_samples),
            "feature_usage_count": np.random.poisson(10, n_samples),
            "subscription_age_days": np.random.exponential(180, n_samples),
            "mrr_change_30d": np.random.normal(0, 50, n_samples),
            "device_health_score": np.random.beta(3, 2, n_samples),
            "location_count": np.random.poisson(2, n_samples) + 1
        })
        
        # Create target with realistic churn patterns
        churn_score = (
            -0.1 * X["days_since_last_activity"] +
            0.01 * X["device_events_30d"] +
            2.0 * X["user_engagement_score"] +
            1.5 * X["payment_success_rate"] +
            -0.2 * X["support_tickets_30d"] +
            0.05 * X["feature_usage_count"] +
            -0.002 * X["subscription_age_days"] +
            -0.01 * X["mrr_change_30d"] +
            1.0 * X["device_health_score"] +
            0.1 * X["location_count"]
        )
        
        # Convert to binary target with some noise
        y = (churn_score + np.random.normal(0, 0.5, n_samples)) > np.percentile(churn_score, 80)
        
        return X, y.astype(int)
