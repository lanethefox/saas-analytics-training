# Platform Documentation

Welcome to the technical documentation for the B2B SaaS Analytics Training Platform.

## 📚 Documentation Structure

### Getting Started
- [Setup Guide](SETUP.md) - Install and configure the platform
- [Quick Start](QUICK_START.md) - Get running in minutes
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

### Architecture & Data Model
- [Entity Data Model](core_entity_data_model.md) - Core entity-centric architecture
- [Data Model Documentation](data_model_documentation.md) - Detailed table documentation
- [Entity Relationships](entity_relationship_diagram.md) - Visual ERD and relationships
- [Entity Summary](entity_summary_table.md) - Quick reference for all entities
- [Schema Explanation](SCHEMA_EXPLANATION.md) - Database schema architecture

### Analytics & Metrics
- [Metrics Layer Guide](METRICS_LAYER_GUIDE.md) - Unified metrics layer
- [Business Analytics Guide](business_analytics_guide.md) - Analytics best practices
- [Entity Quick Start](ENTITY_QUICK_START.md) - Working with entity models

### Platform Services
- [Superset Setup Guide](SUPERSET_SETUP_GUIDE.md) - Business intelligence setup
- [Superset Manual Setup](SUPERSET_MANUAL_SETUP.md) - Step-by-step configuration
- [Superset Quick Reference](SUPERSET_QUICK_REFERENCE.md) - Common tasks
- [Airflow Setup](airflow_setup.md) - Orchestration configuration

### Cross-Domain Knowledge
- [Cross-Domain Interactions](CROSS_DOMAIN_INTERACTIONS_AND_BEST_PRACTICES.md) - How domains work together

## 🔍 Quick Links

**New to the platform?** Start with the [Setup Guide](SETUP.md)

**Want to understand the data?** Read the [Entity Data Model](core_entity_data_model.md)

**Looking for metrics?** Check the [Metrics Layer Guide](METRICS_LAYER_GUIDE.md)

**Need help?** See [Troubleshooting](TROUBLESHOOTING.md)

## 📊 Platform Overview

This platform simulates a complete B2B SaaS analytics environment for a bar/restaurant IoT management system called TapFlow Analytics.

### Tech Stack
- **Database**: PostgreSQL with raw → transformed architecture
- **Transformation**: dbt for data modeling
- **Orchestration**: Apache Airflow for scheduling
- **Visualization**: Apache Superset for dashboards
- **ML Platform**: MLflow, Feast, and custom models
- **Monitoring**: Grafana for system metrics

### Data Architecture
```
External Systems → Raw Schema → dbt Models → Entity Models → Analytics
                    (raw.*)      (staging)    (7 entities)   (dashboards)
```

See [Schema Explanation](SCHEMA_EXPLANATION.md) for detailed architecture.