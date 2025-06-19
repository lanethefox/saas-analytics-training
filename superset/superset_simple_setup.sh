#!/bin/bash

# Superset Quick Setup Script
# Usage: ./superset_simple_setup.sh [--no-auth]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Setting up Superset for Data Platform Project..."
echo "Project root: $PROJECT_ROOT"

# Check if --no-auth flag is provided
NO_AUTH=false
if [[ "$1" == "--no-auth" ]]; then
    NO_AUTH=true
    echo "⚠️  Using NO-AUTH configuration for easier development"
fi

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Start required services
echo "🔧 Starting required services (PostgreSQL, Redis)..."
cd "$PROJECT_ROOT"

# Start core services first
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
wait_for_service "PostgreSQL" localhost 5432
wait_for_service "Redis" localhost 6379

# Copy appropriate config file
if [ "$NO_AUTH" = true ]; then
    echo "📝 Using no-auth configuration..."
    cp superset/superset_config_no_auth.py superset/superset_config.py
else
    echo "📝 Using standard authentication configuration..."
    # Keep existing superset_config.py
fi

# Start superset
echo "🚀 Starting Superset..."
docker-compose up -d superset

# Wait for superset to be ready
echo "⏳ Waiting for Superset to initialize (this may take a few minutes)..."
sleep 10

# Check superset health
attempt=1
max_attempts=20
while [ $attempt -le $max_attempts ]; do
    if curl -s -f http://localhost:8088/health > /dev/null 2>&1; then
        echo "✅ Superset is ready!"
        break
    fi
    echo "   Attempt $attempt/$max_attempts: Superset not ready yet..."
    sleep 5
    ((attempt++))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Superset failed to start properly"
    echo "📋 Checking Superset logs:"
    docker logs saas_platform_superset --tail 20
    exit 1
fi

echo ""
echo "🎉 Superset setup complete!"
echo ""
echo "📊 Access Superset at: http://localhost:8088"

if [ "$NO_AUTH" = true ]; then
    echo "🔓 Authentication disabled - direct access available"
    echo "⚠️  Note: This is for development only!"
else
    echo "🔐 Login credentials:"
    echo "   Username: admin"
    echo "   Password: admin_password_2024"
fi

echo ""
echo "📚 Next steps:"
echo "   1. Access Superset at http://localhost:8088"
echo "   2. Add database connections:"
echo "      - Main database: postgresql://superset_readonly:superset_readonly_password_2024@postgres:5432/saas_platform_dev"
echo "   3. Import sample dashboards and datasets"
echo ""
echo "🔧 Quick commands:"
echo "   View logs: docker logs saas_platform_superset"
echo "   Restart:   docker-compose restart superset"
echo "   Stop:      docker-compose stop superset"
echo ""

# Check if we can connect to the main database
echo "🔍 Testing database connectivity..."
if docker exec saas_platform_postgres psql -U saas_user -d saas_platform_dev -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Main database connection successful"
else
    echo "⚠️  Main database connection failed - check PostgreSQL setup"
fi

echo "✨ Setup complete! Happy analyzing! 📈"
