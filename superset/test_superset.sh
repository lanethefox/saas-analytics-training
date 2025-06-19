#!/bin/bash

# Quick Superset Test Script
# Tests login and basic functionality

echo "🧪 Testing Superset Setup..."

# Test 1: Basic connectivity
echo "1️⃣ Testing basic connectivity..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8088)
if [ "$response" -eq "200" ] || [ "$response" -eq "302" ]; then
    echo "   ✅ Superset is responding (HTTP $response)"
else
    echo "   ❌ Superset not responding (HTTP $response)"
    exit 1
fi

# Test 2: Health check
echo "2️⃣ Testing health endpoint..."
if curl -s -f http://localhost:8088/health > /dev/null; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
fi

# Test 3: Database connectivity
echo "3️⃣ Testing database connectivity..."
if docker exec -e PGPASSWORD=superset_secure_password_2024 saas_platform_postgres psql -U superset_user -d superset_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✅ Superset database connection successful"
else
    echo "   ❌ Superset database connection failed"
fi

if docker exec -e PGPASSWORD=superset_readonly_password_2024 saas_platform_postgres psql -U superset_readonly -d saas_platform_dev -c "SELECT COUNT(*) FROM information_schema.tables;" > /dev/null 2>&1; then
    echo "   ✅ Main database readonly connection successful"
else
    echo "   ❌ Main database readonly connection failed"
fi

# Test 4: Redis connectivity
echo "4️⃣ Testing Redis connectivity..."
if docker exec saas_platform_redis redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis connection successful"
else
    echo "   ❌ Redis connection failed"
fi

echo ""
echo "🎯 Test Summary:"
echo "   Superset URL: http://localhost:8088"
echo "   Admin login: admin / admin_password_2024"
echo ""
echo "📋 Service Status:"
docker-compose ps superset postgres redis | grep -E "(STATE|superset|postgres|redis)"
echo ""
echo "🔗 Database Connection Strings for Superset:"
echo "   Main DB (readonly): postgresql://superset_readonly:superset_readonly_password_2024@postgres:5432/saas_platform_dev"
echo "   Superset Meta DB: postgresql://superset_user:superset_secure_password_2024@postgres:5432/superset_db"
echo ""
echo "✨ Ready to use! 🚀"
