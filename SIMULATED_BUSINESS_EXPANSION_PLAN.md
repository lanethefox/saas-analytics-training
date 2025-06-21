# Simulated Business Expansion Plan: TapFlow Analytics Platform

## Executive Summary

Transform the B2B SaaS Analytics Training Platform into a fully simulated business environment featuring:
- Complete business operations simulation with dynamic data generation
- Functional product website with real-time analytics
- Modern data stack (Airbyte → Iceberg → ClickHouse)
- Production-grade MLOps pipeline
- End-to-end data flows mirroring real SaaS operations

**Vision**: Create the most realistic data platform simulation for learning modern data engineering, analytics, and ML operations.

## 1. Business Documentation & Data Mapping

### Company Profile: TapFlow Analytics

**Mission**: Revolutionize bar and restaurant operations through IoT-powered beverage analytics.

**Product Description**:
TapFlow provides smart tap systems that track pours, monitor inventory, detect maintenance needs, and deliver real-time analytics to bar owners and managers.

### Core Product Features

1. **Device Monitoring**
   - Real-time pour tracking
   - Temperature monitoring
   - Maintenance predictions
   - Offline detection

2. **Inventory Management**
   - Automated depletion tracking
   - Reorder suggestions
   - Waste analysis
   - Cost optimization

3. **Sales Analytics**
   - Revenue by product/time/location
   - Bartender performance
   - Peak hour analysis
   - Pricing optimization

4. **Customer Insights**
   - Popular drinks by demographic
   - Seasonal trends
   - Event impact analysis
   - Loyalty program integration

### Business Functions

#### Sales & Marketing
- **Processes**: Lead gen → Qualification → Demo → Negotiation → Close → Expansion
- **Systems**: Salesforce, HubSpot, Google Ads, LinkedIn
- **Metrics**: Pipeline velocity, CAC, win rate, ACV

#### Customer Success
- **Processes**: Onboarding → Training → Adoption → QBRs → Renewal
- **Systems**: Gainsight, Zendesk, Intercom
- **Metrics**: NPS, health score, churn rate, NRR

#### Product & Engineering
- **Processes**: Discovery → Design → Development → QA → Release
- **Systems**: Jira, GitHub, CircleCI, LaunchDarkly
- **Metrics**: Velocity, quality, adoption, performance

#### Finance & Operations
- **Processes**: Billing → Collections → Reporting → Forecasting
- **Systems**: Stripe, NetSuite, Tableau
- **Metrics**: MRR, burn rate, runway, unit economics

### Complete Data Map

```mermaid
graph LR
    subgraph "Data Sources"
        IOT[IoT Devices]
        WEB[Website/App]
        CRM[Salesforce]
        SUP[Zendesk]
        FIN[Stripe]
        MKT[Marketing Tools]
    end
    
    subgraph "Ingestion"
        AB[Airbyte]
        RT[Real-time Stream]
    end
    
    subgraph "Storage"
        PG[PostgreSQL]
        ICE[Iceberg Lake]
        CH[ClickHouse]
    end
    
    subgraph "Processing"
        DBT[dbt Models]
        FEAT[Feast Features]
        ML[ML Models]
    end
    
    subgraph "Serving"
        DASH[Dashboards]
        API[APIs]
        ALERT[Alerts]
    end
    
    IOT --> RT --> CH
    WEB --> AB --> ICE
    CRM --> AB --> ICE
    SUP --> AB --> ICE
    FIN --> AB --> PG
    MKT --> AB --> ICE
    
    ICE --> DBT --> PG
    PG --> FEAT --> ML
    ML --> API
    PG --> DASH
    CH --> DASH
    ML --> ALERT
```

## 2. Dynamic Data Generation with Airflow

### Daily Batch Jobs Architecture

```python
# airflow/dags/master_simulation_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'tapflow',
    'depends_on_past': True,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

dag = DAG(
    'tapflow_daily_simulation',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
)

# Tasks structure:
# 1. State Management (read previous day's state)
# 2. Customer Lifecycle (new signups, churns, expansions)
# 3. Device Telemetry (24 hours of pour events)
# 4. User Activity (logins, feature usage)
# 5. Support Tickets (based on device issues)
# 6. Financial Events (charges, refunds)
# 7. Marketing Activity (campaigns, responses)
# 8. State Persistence (save end-of-day state)
```

### Dynamic Simulation Features

1. **Stateful Generation**
   - Maintain customer lifecycle stages
   - Track device health degradation
   - Accumulate historical patterns
   - Simulate seasonal variations

2. **Event Correlations**
   - Device failures → Support tickets
   - Low usage → Churn risk
   - Marketing campaigns → New signups
   - Feature adoption → Expansion

3. **Realistic Volumes**
   - 100-200 new customers/day
   - 1M+ device events/day
   - 10K+ user actions/day
   - Follows business hour patterns

### Implementation Components

```
scripts/simulation/
├── state_management/
│   ├── daily_state.py      # Read/write daily state
│   ├── customer_state.py   # Customer lifecycle tracking
│   └── device_state.py     # Device health tracking
├── generators/
│   ├── customer_lifecycle.py
│   ├── device_telemetry.py
│   ├── user_activity.py
│   ├── support_tickets.py
│   ├── financial_events.py
│   └── marketing_activity.py
└── orchestration/
    ├── dag_factory.py
    └── task_dependencies.py
```

## 3. React Product Website with PostHog

### Website Architecture

```
tapflow-website/
├── src/
│   ├── pages/
│   │   ├── Home.jsx           # Landing page
│   │   ├── Pricing.jsx        # Pricing tiers
│   │   ├── Features.jsx       # Product features
│   │   ├── Demo.jsx           # Demo request form
│   │   ├── Login.jsx          # Customer portal
│   │   └── Docs.jsx           # Documentation
│   ├── components/
│   │   ├── Analytics.jsx      # PostHog wrapper
│   │   ├── Navigation.jsx
│   │   └── Forms.jsx
│   └── utils/
│       └── posthog.js         # PostHog client
├── public/
└── package.json
```

### PostHog Implementation

```javascript
// src/utils/posthog.js
import posthog from 'posthog-js'

export const initPostHog = () => {
  posthog.init('your-project-api-key', {
    api_host: 'http://localhost:8001',
    autocapture: true,
    capture_pageview: true,
    capture_pageleave: true,
    session_recording: {
      enabled: true,
      sample_rate: 0.1
    }
  })
}

// Track custom events
export const trackEvent = (eventName, properties) => {
  posthog.capture(eventName, {
    ...properties,
    timestamp: new Date().toISOString()
  })
}
```

### Event Taxonomy

```yaml
Page Views:
  - home_viewed
  - pricing_viewed
  - features_viewed
  - demo_viewed

User Actions:
  - demo_requested
  - pricing_calculator_used
  - feature_video_played
  - documentation_searched
  
Conversion Events:
  - signup_started
  - signup_completed
  - trial_activated
  - plan_upgraded
```

### PostHog Deployment

```yaml
# docker-compose.posthog.yml
version: '3.8'

services:
  posthog:
    image: posthog/posthog:latest
    depends_on:
      - posthog-postgres
      - posthog-redis
      - clickhouse
    environment:
      DATABASE_URL: postgres://posthog:password@posthog-postgres:5432/posthog
      REDIS_URL: redis://posthog-redis:6379/
      CLICKHOUSE_HOST: clickhouse
      SECRET_KEY: ${POSTHOG_SECRET_KEY}
    ports:
      - "8001:8000"

  clickhouse:
    image: clickhouse/clickhouse-server:latest
    volumes:
      - ./clickhouse/config.xml:/etc/clickhouse-server/config.xml
      - clickhouse-data:/var/lib/clickhouse
    ports:
      - "8123:8123"
      - "9000:9000"

  posthog-postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: posthog
      POSTGRES_USER: posthog
      POSTGRES_PASSWORD: password
    volumes:
      - posthog-postgres-data:/var/lib/postgresql/data

  posthog-redis:
    image: redis:7-alpine
    volumes:
      - posthog-redis-data:/data

volumes:
  clickhouse-data:
  posthog-postgres-data:
  posthog-redis-data:
```

## 4. Airbyte Data Ingestion

### Connector Configuration

```yaml
# airbyte/sources/
sources:
  - name: tapflow_postgres
    type: postgres
    config:
      host: postgres
      database: saas_platform_dev
      username: saas_user
      schemas: [raw, app_events]
      replication: CDC
      
  - name: posthog_events  
    type: posthog
    config:
      api_key: ${POSTHOG_API_KEY}
      project_id: ${POSTHOG_PROJECT_ID}
      start_date: 2024-01-01
      
  - name: stripe_api
    type: stripe
    config:
      api_key: ${STRIPE_TEST_KEY}
      start_date: 2024-01-01
      
  - name: salesforce_api
    type: salesforce
    config:
      client_id: ${SF_CLIENT_ID}
      client_secret: ${SF_CLIENT_SECRET}
      refresh_token: ${SF_REFRESH_TOKEN}

destinations:
  - name: iceberg_lake
    type: s3 # Will be converted to Iceberg
    config:
      bucket: tapflow-lake
      path_pattern: ${NAMESPACE}/${STREAM_NAME}/year=${YEAR}/month=${MONTH}/
      format: parquet
```

### Airbyte Deployment

```yaml
# docker-compose.airbyte.yml
version: '3.8'

services:
  airbyte-webapp:
    image: airbyte/webapp:latest
    container_name: airbyte-webapp
    ports:
      - "8002:80"
    environment:
      - AIRBYTE_VERSION=${VERSION}
      - API_URL=${API_URL:-http://airbyte-server:8001}

  airbyte-server:
    image: airbyte/server:latest
    container_name: airbyte-server
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CONFIG_ROOT=/data
      - TRACKING_STRATEGY=segment
      - WORKER_ENVIRONMENT=docker

  airbyte-worker:
    image: airbyte/worker:latest
    container_name: airbyte-worker
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CONFIG_ROOT=/data
      - WORKER_ENVIRONMENT=docker

  airbyte-db:
    image: postgres:13
    container_name: airbyte-db
    environment:
      - POSTGRES_DB=airbyte
      - POSTGRES_USER=airbyte
      - POSTGRES_PASSWORD=airbyte
```

### Data Flow Orchestration

```python
# airflow/dags/airbyte_sync_dag.py

from airflow_airbyte.operators import AirbyteTriggerSyncOperator

# Sync all sources every hour
postgres_sync = AirbyteTriggerSyncOperator(
    task_id='sync_postgres',
    airbyte_conn_id='airbyte_default',
    connection_id='{{var.value.postgres_connection_id}}',
    asynchronous=False,
)

posthog_sync = AirbyteTriggerSyncOperator(
    task_id='sync_posthog',
    airbyte_conn_id='airbyte_default', 
    connection_id='{{var.value.posthog_connection_id}}',
    asynchronous=False,
)
```

## 5. Apache Iceberg Data Lake

### Iceberg Architecture

```
data-lake/
├── catalog/           # Iceberg catalog (Hive/Glue/Nessie)
├── warehouse/         # Actual data files
│   ├── raw/          # Raw ingested data
│   ├── staging/      # Cleaned data
│   ├── intermediate/ # Business logic applied
│   └── entity/       # Entity-centric models
└── metadata/         # Iceberg metadata
```

### Migration Strategy

```python
# scripts/migrate_to_iceberg.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder \
    .appName("PostgresToIceberg") \
    .config("spark.sql.catalog.tapflow", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.tapflow.type", "hadoop") \
    .config("spark.sql.catalog.tapflow.warehouse", "s3://tapflow-lake/warehouse") \
    .getOrCreate()

# Migrate each layer
def migrate_table(schema, table):
    # Read from PostgreSQL
    df = spark.read \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://localhost:5432/saas_platform_dev") \
        .option("dbtable", f"{schema}.{table}") \
        .option("user", "saas_user") \
        .option("password", "saas_secure_password_2024") \
        .load()
    
    # Write to Iceberg with partitioning
    df.writeTo(f"tapflow.{schema}.{table}") \
        .partitionedBy(days("created_at")) \
        .tableProperty("format-version", "2") \
        .tableProperty("write.metadata.delete-after-commit.enabled", "true") \
        .tableProperty("write.metadata.previous-versions-max", "100") \
        .create()

# Migrate all tables
for schema in ['raw', 'staging', 'intermediate', 'entity']:
    tables = get_tables_for_schema(schema)
    for table in tables:
        migrate_table(schema, table)
```

### Iceberg Benefits Implementation

1. **Time Travel**
   ```sql
   -- Query data as of yesterday
   SELECT * FROM tapflow.entity.entity_customers
   TIMESTAMP AS OF '2024-01-20 00:00:00'
   ```

2. **Schema Evolution**
   ```sql
   -- Add column without rewriting data
   ALTER TABLE tapflow.entity.entity_customers
   ADD COLUMN ai_health_score DOUBLE
   ```

3. **Partition Evolution**
   ```sql
   -- Change partitioning strategy
   ALTER TABLE tapflow.raw.device_events
   ADD PARTITION FIELD hour(event_timestamp)
   ```

### Query Engines

```yaml
# trino/config.properties
coordinator=true
node-scheduler.include-coordinator=true
http-server.http.port=8080
query.max-memory=5GB
query.max-memory-per-node=1GB

# Iceberg connector
connector.name=iceberg
hive.metastore.uri=thrift://hive-metastore:9083
iceberg.catalog.type=hive
```

## 6. ClickHouse + MLOps Stack

### ClickHouse for Real-time Analytics

```sql
-- Create real-time event tables
CREATE TABLE events.device_telemetry (
    event_id UUID,
    device_id String,
    location_id String, 
    event_type String,
    event_data String,
    event_time DateTime64(3),
    ingestion_time DateTime64(3) DEFAULT now64(3)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (device_id, event_time);

-- Materialized view for real-time aggregations
CREATE MATERIALIZED VIEW events.device_metrics_5min
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMMDD(window_start)
ORDER BY (device_id, window_start)
AS SELECT
    device_id,
    toStartOfFiveMinute(event_time) AS window_start,
    count() as event_count,
    avg(JSONExtractFloat(event_data, 'volume')) as avg_pour_volume,
    max(JSONExtractFloat(event_data, 'temperature')) as max_temperature
FROM events.device_telemetry
GROUP BY device_id, window_start;
```

### MLOps Pipeline

#### 1. Feast Feature Store

```python
# feast/feature_definitions.py

from feast import Entity, Feature, FeatureView, FileSource
from feast.types import Float32, Int64, String
from datetime import timedelta

# Define entities
customer = Entity(name="customer", value_type=String)
device = Entity(name="device", value_type=String)

# Define feature views
customer_features = FeatureView(
    name="customer_features",
    entities=["customer"],
    ttl=timedelta(days=1),
    features=[
        Feature(name="days_active", dtype=Int64),
        Feature(name="total_revenue", dtype=Float32),
        Feature(name="device_count", dtype=Int64),
        Feature(name="support_tickets_30d", dtype=Int64),
        Feature(name="usage_trend_7d", dtype=Float32),
        Feature(name="payment_reliability", dtype=Float32),
    ],
    online=True,
    source=FileSource(
        path="s3://tapflow-lake/features/customer_features.parquet",
        event_timestamp_column="event_timestamp"
    ),
)

device_features = FeatureView(
    name="device_features",
    entities=["device"],
    ttl=timedelta(hours=1),
    features=[
        Feature(name="pour_count_24h", dtype=Int64),
        Feature(name="avg_pour_size", dtype=Float32),
        Feature(name="uptime_percentage", dtype=Float32),
        Feature(name="temperature_variance", dtype=Float32),
        Feature(name="maintenance_score", dtype=Float32),
    ],
    online=True,
    source=FileSource(
        path="s3://tapflow-lake/features/device_features.parquet",
        event_timestamp_column="event_timestamp"
    ),
)
```

#### 2. MLflow Model Training

```python
# ml/models/churn_prediction.py

import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import feast

# Initialize Feast
store = feast.FeatureStore(repo_path="feast/")

# Get training data
entity_df = pd.DataFrame({
    "customer": customer_ids,
    "event_timestamp": timestamps
})

training_data = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "customer_features:days_active",
        "customer_features:total_revenue",
        "customer_features:device_count",
        "customer_features:support_tickets_30d",
        "customer_features:usage_trend_7d",
        "customer_features:payment_reliability"
    ]
).to_df()

# Train model
with mlflow.start_run():
    X_train, X_test, y_train, y_test = train_test_split(
        training_data.drop(['customer', 'event_timestamp', 'churned'], axis=1),
        training_data['churned'],
        test_size=0.2
    )
    
    model = RandomForestClassifier(n_estimators=100, max_depth=10)
    model.fit(X_train, y_train)
    
    # Log model
    mlflow.sklearn.log_model(
        model, 
        "churn_model",
        registered_model_name="tapflow_churn_prediction"
    )
    
    # Log metrics
    mlflow.log_metric("accuracy", model.score(X_test, y_test))
    mlflow.log_metric("precision", precision_score(y_test, model.predict(X_test)))
```

#### 3. Evidently Model Monitoring

```python
# ml/monitoring/drift_detection.py

from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset

# Create drift report
def check_model_drift(reference_data, current_data):
    column_mapping = ColumnMapping(
        prediction='prediction',
        numerical_features=['days_active', 'total_revenue', 'device_count'],
        categorical_features=['customer_tier'],
        target='churned'
    )
    
    report = Report(metrics=[
        DataDriftPreset(),
        TargetDriftPreset(),
    ])
    
    report.run(
        reference_data=reference_data,
        current_data=current_data,
        column_mapping=column_mapping
    )
    
    # Save report
    report.save_html("reports/drift_report.html")
    
    # Check if retraining needed
    if report.as_dict()["metrics"][0]["result"]["dataset_drift"]:
        trigger_retraining()
```

#### 4. Seldon Model Serving

```yaml
# seldon/churn-model-deployment.yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: churn-prediction
spec:
  predictors:
  - name: default
    replicas: 2
    graph:
      name: churn-model
      implementation: MLFLOW_SERVER
      modelUri: s3://tapflow-models/churn_model
      envSecretRefName: mlflow-secret
    componentSpecs:
    - spec:
        containers:
        - name: churn-model
          resources:
            requests:
              memory: 1Gi
              cpu: 0.5
```

### Integration with Analytics

```python
# integrations/ml_dashboard_integration.py

def update_customer_predictions():
    """Update customer predictions in real-time"""
    
    # Get features from Feast
    customer_features = store.get_online_features(
        features=[...],
        entity_rows=[{"customer": customer_id} for customer_id in active_customers]
    ).to_df()
    
    # Get predictions from Seldon
    predictions = requests.post(
        "http://seldon-gateway/seldon/default/churn-prediction/api/v1.0/predictions",
        json={"data": {"ndarray": customer_features.values.tolist()}}
    ).json()
    
    # Update dashboard database
    for customer_id, pred in zip(active_customers, predictions["data"]["ndarray"]):
        update_query = """
            UPDATE entity.entity_customers 
            SET ml_churn_probability = %s,
                ml_prediction_timestamp = NOW()
            WHERE customer_id = %s
        """
        cursor.execute(update_query, (pred[1], customer_id))
```

## Implementation Timeline

### Phase 0: Analytics Engineering Module (Weeks -2 to 0)
- Week -2: Create Analytics Engineering curriculum materials
- Week -1: Build example entity models and test scenarios
- Week 0: Integrate with existing education platform

### Phase 1: Foundation (Weeks 1-4)
- Week 1: Business documentation and data mapping
- Week 2: Enhanced data generators with state management
- Week 3: Airflow DAG implementation
- Week 4: Testing and validation

### Phase 2: Product Layer (Weeks 5-8)
- Week 5: React website development
- Week 6: PostHog integration and instrumentation
- Week 7: Connect website to data pipeline
- Week 8: Testing and optimization

### Phase 3: Modern Stack (Weeks 9-12)
- Week 9: Airbyte deployment and configuration
- Week 10: Iceberg migration and setup
- Week 11: ClickHouse implementation
- Week 12: Integration testing

### Phase 4: ML Platform (Weeks 13-16)
- Week 13: Feast feature store setup
- Week 14: MLflow and model training
- Week 15: Evidently monitoring
- Week 16: Seldon deployment and integration

## Success Metrics

### Technical Metrics
- Data freshness: <5 minute latency
- System uptime: 99.9%
- Query performance: <1 second for dashboards
- ML inference: <100ms response time
- Storage efficiency: 10:1 compression ratio

### Business Metrics
- 100K+ events/minute processed
- 50+ pre-built ML features
- 5+ production ML models
- Complete customer 360° view
- Real-time anomaly detection

### Educational Outcomes
- Learn 15+ modern data tools
- Build production-grade pipelines
- Implement MLOps best practices
- Create portfolio projects
- Industry-ready skills

## Resource Requirements

### Infrastructure
- 32GB RAM minimum (64GB recommended)
- 500GB SSD storage
- 8+ CPU cores
- Docker with 20GB+ allocated

### Software Stack
```yaml
Core Platform:
  - PostgreSQL 14+
  - Apache Airflow 2.5+
  - dbt 1.5+
  - Apache Superset 2.0+

Modern Stack:
  - Airbyte 0.50+
  - Apache Iceberg 1.3+
  - Trino 420+
  - ClickHouse 23.8+
  - MinIO (S3 compatible)

ML Platform:
  - Feast 0.34+
  - MLflow 2.8+
  - Evidently 0.4+
  - Seldon Core 1.15+

Development:
  - React 18+
  - PostHog 1.45+
  - Python 3.10+
  - Node.js 18+
```

## Next Steps

1. **Validate Architecture**: Review with stakeholders
2. **Create Development Branch**: `feature/simulated-business`
3. **Set Up Infrastructure**: Expand Docker Compose
4. **Build Foundation**: Start with Phase 1
5. **Iterate and Test**: Continuous validation

This comprehensive plan transforms the educational platform into a living, breathing simulated business that teaches the entire modern data stack through hands-on experience.