#!/bin/bash

echo "🔧 Fixing MLflow Database Issues..."

# Stop MLflow
echo "Stopping MLflow..."
docker-compose stop mlflow

# Clean alembic version
echo "Cleaning alembic version table..."
docker exec saas_platform_postgres sh -c "PGPASSWORD=saas_secure_password_2024 psql -U saas_user -d saas_platform_dev -c \"DELETE FROM alembic_version;\""

# Drop any existing MLflow tables (if any)
echo "Dropping any existing MLflow tables..."
docker exec saas_platform_postgres sh -c "PGPASSWORD=saas_secure_password_2024 psql -U saas_user -d saas_platform_dev -c \"DROP TABLE IF EXISTS experiments CASCADE;\""
docker exec saas_platform_postgres sh -c "PGPASSWORD=saas_secure_password_2024 psql -U saas_user -d saas_platform_dev -c \"DROP TABLE IF EXISTS runs CASCADE;\""
docker exec saas_platform_postgres sh -c "PGPASSWORD=saas_secure_password_2024 psql -U saas_user -d saas_platform_dev -c \"DROP TABLE IF EXISTS params CASCADE;\""
docker exec saas_platform_postgres sh -c "PGPASSWORD=saas_secure_password_2024 psql -U saas_user -d saas_platform_dev -c \"DROP TABLE IF EXISTS metrics CASCADE;\""
docker exec saas_platform_postgres sh -c "PGPASSWORD=saas_secure_password_2024 psql -U saas_user -d saas_platform_dev -c \"DROP TABLE IF EXISTS tags CASCADE;\""

# Remove and recreate volume
echo "Cleaning MLflow artifacts volume..."
docker volume rm data-platform_mlflow_artifacts 2>/dev/null || true
docker volume create data-platform_mlflow_artifacts

# Create S3 bucket in MinIO
echo "Ensuring S3 bucket exists in MinIO..."
docker exec saas_platform_minio mc alias set myminio http://localhost:9000 minio_admin minio_secure_password_2024 2>/dev/null || true
docker exec saas_platform_minio mc mb myminio/mlflow 2>/dev/null || true

# Restart MLflow
echo "Starting MLflow..."
docker-compose up -d mlflow

# Wait for MLflow to start
echo "Waiting for MLflow to initialize..."
sleep 10

# Check status
echo "Checking MLflow status..."
docker-compose ps mlflow
docker-compose logs --tail=20 mlflow

# Test MLflow
echo "Testing MLflow API..."
curl -s http://localhost:5001/api/2.0/mlflow/experiments/list | python3 -m json.tool || echo "MLflow might still be starting up..."

echo "✅ MLflow fix complete! Check http://localhost:5001"