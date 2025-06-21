# Release Notes - Simplified Setup

## Overview
This release dramatically simplifies the platform setup by focusing on core services and fixing critical compatibility issues.

## 🎯 Key Improvements

### 1. Core Services by Default
- **Before**: All services started by default (15+ containers)
- **After**: Only essential services (5 containers)
- **Result**: Faster startup, lower resource usage, easier to understand

### 2. Fixed Data Generation
- **Before**: Schema mismatch caused data generation to fail
- **After**: Enhanced schema aligns with data generator
- **Result**: Data loads successfully on first run

### 3. Reduced Requirements
- **Before**: 8GB RAM required
- **After**: 4GB RAM for core services
- **Result**: Works on more machines

### 4. Clearer Options
```bash
# Simple default
./setup.sh

# Full stack when needed
./setup.sh --full

# Custom data size
./setup.sh --size large
```

## 📦 What's Included (Default)
- ✅ PostgreSQL with pgvector
- ✅ Redis for caching
- ✅ dbt for transformations
- ✅ Apache Superset for BI
- ✅ Jupyter Lab for notebooks

## 🔄 What's Optional (--full)
- Apache Airflow (orchestration)
- MLflow (ML platform)
- Grafana & Prometheus (monitoring)
- MinIO (object storage)

## 🔧 Technical Changes
1. Enhanced schema (`database/01_main_schema.sql`) includes all expected columns
2. Separate compose files: `docker-compose.yml` (core) and `docker-compose.full.yml`
3. Fixed Jupyter permissions with explicit user setting
4. Automatic creation of `superset_db` database
5. Improved validation script that checks only running services

## 📋 Migration Guide
If upgrading from previous version:
1. Stop all services: `docker-compose down`
2. Pull latest changes: `git pull`
3. Run new setup: `./setup.sh`
4. For full stack: `./setup.sh --full`

## 🐛 Issues Fixed
- Schema mismatch preventing data generation
- Missing superset_db causing Superset to fail
- Jupyter container restart loop
- Validation script checking non-existent services
- Complex setup overwhelming new users

## 📚 Documentation Updates
- Simplified README focusing on core services
- Added BACKLOG.md for optional features
- Updated setup instructions
- Clearer service descriptions

## 🚀 Next Steps
See [BACKLOG.md](BACKLOG.md) for planned improvements and how to enable optional features.