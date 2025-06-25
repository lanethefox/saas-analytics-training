#!/bin/bash

# Reset Data Script - Wipes and reloads clean data

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔄 Data Reset Script"
echo "===================="
echo ""

# Default values
CLEAR="true"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-clear)
            CLEAR="false"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-clear]"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}⚠️  This will delete all existing data!${NC}"
echo "Using deterministic data generation"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Check if running in Docker or locally
if [ -f /.dockerenv ]; then
    # Running inside Docker
    echo "🐳 Running in Docker environment"
    DB_HOST="postgres"
else
    # Running locally
    echo "💻 Running in local environment"
    DB_HOST="localhost"
fi

# Run deterministic data generation
echo ""
echo "🏗️  Generating deterministic data..."

if command -v python3 &> /dev/null; then
    python3 scripts/generate_all_deterministic.py
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Run dbt models if available
if command -v docker &> /dev/null && docker ps | grep -q saas_platform_dbt; then
    echo ""
    echo "🔧 Running dbt transformations..."
    docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt run --profiles-dir ." || {
        echo -e "${YELLOW}⚠️  dbt run had issues (this may be normal on first run)${NC}"
    }
fi

echo ""
echo -e "${GREEN}✅ Data reset complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Visit http://localhost:8088 to see updated dashboards"
echo "2. Run queries in Jupyter Lab at http://localhost:8888"
echo "3. Check data quality with: docker-compose exec postgres psql -U saas_user -d saas_platform_dev"