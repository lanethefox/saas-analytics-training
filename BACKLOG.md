# Platform Backlog

This document tracks features and services that are available but not enabled by default in the core setup.

## 🚦 Service Status

### Core Services (Default)
These services are included in the standard `docker-compose.yml`:
- ✅ **PostgreSQL** - Database with pgvector extension
- ✅ **Redis** - Caching layer
- ✅ **dbt** - Data transformation framework
- ✅ **Apache Superset** - Business intelligence and dashboards
- ✅ **Jupyter Lab** - Interactive notebooks for data science

### Backlogged Services
These services are available in `docker-compose.full.yml` but disabled by default:

#### 🔄 Workflow Orchestration
- **Apache Airflow** - DAG-based workflow orchestration
  - Status: Fully configured but not in core setup
  - Reason: Adds complexity for learners; many use cases don't need orchestration
  - Enable with: `./setup.sh --full`

#### 🤖 Machine Learning Platform
- **MLflow** - ML experiment tracking and model registry
  - Status: Configured with MinIO backend
  - Reason: Advanced feature not needed for basic analytics learning
  - Enable with: `./setup.sh --full`
  
- **Feast** - Feature store (partially configured)
  - Status: Configuration started but incomplete
  - Reason: Complex setup, limited educational use cases

#### 📊 Monitoring & Observability
- **Grafana** - System and business metrics monitoring
  - Status: Basic configuration available
  - Reason: Focus on analytics, not operations
  - Enable with: `./setup.sh --full`

- **Prometheus** - Metrics collection
  - Status: Basic configuration available
  - Reason: Operational complexity not core to analytics training
  - Enable with: `./setup.sh --full`

## 📋 Feature Backlog

### High Priority (Next Release)
1. **Improved Jupyter Configuration**
   - Fix permission issues in container
   - Pre-install common data science libraries
   - Add example notebooks for each learning module

2. **Enhanced Data Generation**
   - Add more realistic data patterns
   - Include data quality issues for training
   - Support incremental data generation

3. **Superset Dashboard Templates**
   - Pre-configured dashboards for each domain
   - Interactive SQL tutorials
   - Guided analytics exercises

### Medium Priority
1. **dbt Documentation**
   - Auto-generate and serve dbt docs
   - Integration with Superset
   - Lineage visualization

2. **Data Quality Monitoring**
   - Great Expectations integration
   - Automated data quality checks
   - Quality dashboards in Superset

3. **Authentication & Security**
   - Unified authentication across services
   - Role-based access control
   - SSL/TLS configuration

### Low Priority
1. **Cloud Deployment Options**
   - Kubernetes manifests
   - Terraform configurations
   - Cloud-specific optimizations

2. **Advanced Analytics**
   - R integration in Jupyter
   - Spark integration
   - GPU support for ML

3. **Extended Integrations**
   - Kafka for streaming
   - Elasticsearch for search
   - Additional data sources

## 🛠️ Known Issues

### Setup & Configuration
1. **Jupyter Permission Issues**
   - Container may restart due to permission errors
   - Workaround: Set user in docker-compose.yml

2. **First-Run Failures**
   - Some services may fail on first run before data exists
   - Resolution: Run setup.sh again after data loads

3. **Memory Requirements**
   - Full stack requires 8GB+ RAM allocated to Docker
   - Core services work with 4GB

### Data & Schema
1. **Schema Evolution**
   - Some dbt models expect columns that may not exist
   - Working on unified schema approach

2. **Sample Data**
   - Current data generator creates synthetic patterns
   - Planning more realistic business scenarios

## 🚀 How to Enable Backlogged Features

### Quick Enable
```bash
# Run full stack
./setup.sh --full

# Or modify docker-compose.yml to include specific services
```

### Manual Enable
1. Copy service definition from `docker-compose.full.yml`
2. Add to your `docker-compose.yml`
3. Run `docker-compose up -d [service-name]`

### Testing Backlogged Features
```bash
# Test Airflow
docker-compose -f docker-compose.full.yml up -d airflow-webserver airflow-scheduler

# Test MLflow
docker-compose -f docker-compose.full.yml up -d mlflow minio

# Test Monitoring
docker-compose -f docker-compose.full.yml up -d grafana prometheus
```

## 📝 Contributing

To move a feature from backlog to core:
1. Ensure it adds clear educational value
2. Document setup and usage
3. Add to validation tests
4. Update tutorials to include feature
5. Test on fresh installation

## 📅 Release Planning

### v1.1 (Next Release)
- Fix Jupyter permissions
- Improve data generation
- Add more dashboard templates

### v1.2 (Future)
- dbt documentation server
- Basic data quality checks
- Unified authentication

### v2.0 (Long Term)
- Cloud deployment options
- Advanced analytics features
- Production-ready configurations