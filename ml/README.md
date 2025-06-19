# Machine Learning Components for SaaS Data Platform

This directory contains the complete machine learning framework for customer analytics, predictive modeling, and business intelligence automation.

## ML Architecture

### 1. **Customer Analytics Models**
- **Churn Prediction**: XGBoost and LightGBM models for predicting customer churn risk
- **Customer Lifetime Value (CLV)**: Prophet-based forecasting for revenue prediction
- **Health Scoring**: Real-time customer health assessment using ensemble methods
- **Expansion Prediction**: Models to identify upsell and cross-sell opportunities

### 2. **Operational ML Models**
- **Device Failure Prediction**: IoT sensor data analysis for predictive maintenance
- **Anomaly Detection**: Real-time outlier detection for operational metrics
- **Demand Forecasting**: Usage pattern prediction for capacity planning
- **Performance Optimization**: Automated parameter tuning for device efficiency

### 3. **Marketing Intelligence**
- **Attribution Modeling**: Multi-touch attribution using Shapley values
- **Campaign Optimization**: Automated bid management and budget allocation
- **Lead Scoring**: Probabilistic scoring for sales qualification
- **Customer Segmentation**: Behavioral clustering and persona development

### 4. **Feature Engineering Pipeline**
- **Real-time Features**: Streaming feature computation from IoT events
- **Batch Features**: Daily/weekly/monthly aggregations for historical analysis
- **External Enrichment**: Weather, economic, and industry data integration
- **Feature Store**: Centralized feature management with versioning

## Directory Structure

```
ml/
├── api/                    # FastAPI model serving endpoints
├── models/                 # ML model implementations
├── features/               # Feature engineering pipelines
├── training/               # Model training scripts and pipelines
├── evaluation/             # Model evaluation and monitoring
├── utils/                  # Shared utilities and helpers
├── config/                 # Configuration files
├── data/                   # Data processing and ingestion
├── notebooks/              # Jupyter notebooks for exploration
└── tests/                  # Unit and integration tests
```

## Quick Start

### 1. **Train Churn Model**
```bash
python ml/training/train_churn_model.py --data-date 2024-01-01
```

### 2. **Serve Models via API**
```bash
uvicorn ml.api.main:app --host 0.0.0.0 --port 8000
```

### 3. **Run Feature Pipeline**
```bash
python ml/features/daily_feature_pipeline.py
```

### 4. **Model Monitoring**
```bash
python ml/evaluation/model_monitoring.py
```

## Model Performance Targets

- **Churn Prediction**: AUC > 0.85, Precision > 0.75
- **CLV Forecasting**: MAPE < 15%, R² > 0.80
- **Device Failure**: Recall > 0.90, False Positive Rate < 0.05
- **Campaign Attribution**: Attribution accuracy > 80%

## Integration Points

- **dbt Models**: Features derived from entity tables
- **MLflow**: Model tracking, versioning, and registry
- **Airflow**: Automated training and deployment pipelines
- **PostgreSQL**: Feature store and model metadata
- **Redis**: Real-time feature caching and model serving
- **Grafana**: Model performance monitoring and alerting

The ML framework is designed for production deployment with automated retraining, A/B testing capabilities, and comprehensive monitoring to ensure model performance and business impact.
