#!/bin/bash

echo "========================================="
echo "PostgreSQL Initialization Validator"
echo "========================================="

# Check database directory
echo -e "\nChecking database initialization files..."
ls -la database/*.sql | grep -E "\.sql$"

# Check if we have proper init files
echo -e "\nValidating SQL files..."
for file in database/*.sql; do
    if [ -f "$file" ]; then
        echo "  ✓ Found: $file"
        # Check first few lines
        echo "    First line: $(head -n 1 "$file" | cut -c1-60)..."
    fi
done

# Test PostgreSQL container alone
echo -e "\nTesting PostgreSQL container..."
docker run --rm -d \
    --name test_postgres \
    -e POSTGRES_DB=saas_platform_dev \
    -e POSTGRES_USER=saas_user \
    -e POSTGRES_PASSWORD=saas_secure_password_2024 \
    -p 25432:5432 \
    pgvector/pgvector:pg15

sleep 5

# Check if it's running
if docker ps | grep test_postgres > /dev/null; then
    echo "  ✓ PostgreSQL container started successfully"
    
    # Test connection
    docker exec test_postgres pg_isready -U saas_user -d saas_platform_dev
    
    # Stop test container
    docker stop test_postgres
else
    echo "  ✗ PostgreSQL container failed to start"
    docker logs test_postgres
fi

echo -e "\nValidation complete!"