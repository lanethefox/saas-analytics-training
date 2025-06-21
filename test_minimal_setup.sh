#!/bin/bash

echo "========================================="
echo "SaaS Data Platform - Minimal Test Setup"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"
if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Stop any existing containers
echo -e "\n${YELLOW}Stopping any existing test containers...${NC}"
docker-compose -f docker-compose.test.minimal.yml down -v 2>/dev/null || true

# Pull required images
echo -e "\n${YELLOW}Pulling required Docker images...${NC}"
docker pull pgvector/pgvector:pg15
docker pull redis:7-alpine

# Start services
echo -e "\n${YELLOW}Starting core services...${NC}"
docker-compose -f docker-compose.test.minimal.yml up -d postgres redis

# Wait for PostgreSQL to be ready
echo -e "\n${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec saas_test_postgres pg_isready -U saas_user -d saas_platform_dev >/dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "\n${RED}PostgreSQL failed to start in time${NC}"
    docker-compose -f docker-compose.test.minimal.yml logs postgres
    exit 1
fi

# Load test data
echo -e "\n${YELLOW}Loading test data...${NC}"
if [ -f "scripts/load_xs_data_smart.py" ]; then
    echo "Loading XS dataset..."
    python scripts/load_xs_data_smart.py
    echo -e "${GREEN}Test data loaded!${NC}"
else
    echo -e "${YELLOW}No test data loader found. Skipping data load.${NC}"
fi

# Start remaining services
echo -e "\n${YELLOW}Starting dbt, Superset, and Jupyter...${NC}"
docker-compose -f docker-compose.test.minimal.yml up -d dbt superset jupyter

# Wait a bit for services to initialize
sleep 10

# Check service status
echo -e "\n${YELLOW}Checking service status...${NC}"
docker-compose -f docker-compose.test.minimal.yml ps

# Display access information
echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Minimal test environment is ready!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nAccess points:"
echo -e "  PostgreSQL: localhost:15432"
echo -e "  Redis: localhost:16379"
echo -e "  Superset: http://localhost:18088"
echo -e "  Jupyter: http://localhost:18888 (token: saas_ml_token_2024)"
echo -e "\nDatabase credentials:"
echo -e "  Host: localhost"
echo -e "  Port: 15432"
echo -e "  Database: saas_platform_dev"
echo -e "  Username: saas_user"
echo -e "  Password: saas_secure_password_2024"
echo -e "\n${YELLOW}To stop the test environment:${NC}"
echo -e "  docker-compose -f docker-compose.test.minimal.yml down"
echo -e "\n${YELLOW}To view logs:${NC}"
echo -e "  docker-compose -f docker-compose.test.minimal.yml logs -f [service_name]"