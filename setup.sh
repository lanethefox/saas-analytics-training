#!/bin/bash

# B2B SaaS Analytics Platform - Setup Script
# Core services by default, use --full for complete stack

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
SKIP_DATA_GEN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            COMPOSE_FILE="docker-compose.full.yml"
            shift
            ;;
        --skip-data)
            SKIP_DATA_GEN=true
            shift
            ;;
        --help)
            echo "Usage: ./setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --full          Use full stack including Airflow, MLflow, monitoring"
            echo "  --skip-data     Skip data generation"
            echo "  --help          Show this help message"
            echo ""
            echo "Note: Data generation now uses deterministic seed for consistency"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use ./setup.sh --help for usage information"
            exit 1
            ;;
    esac
done

# Print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠${NC} $1"
}

# Header
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          🎓 B2B SaaS Analytics Training Platform              ║"
if [[ "$COMPOSE_FILE" == "docker-compose.full.yml" ]]; then
    echo "║                   (Full Stack Setup)                          ║"
else
    echo "║                   (Core Services Only)                        ║"
fi
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi
print_success "Docker is running"

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    print_error "Docker Compose is not available!"
    exit 1
fi
print_success "Docker Compose is available"

# Check Python (for data generation)
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION is installed"
    
    # Install Python dependencies if needed
    print_status "Checking Python dependencies..."
    if ! python3 -c "import psycopg2" 2>/dev/null; then
        print_status "Installing psycopg2-binary..."
        pip3 install psycopg2-binary || {
            print_warning "Failed to install psycopg2-binary. Data generation may not work."
            SKIP_DATA_GEN=true
        }
    fi
else
    print_warning "Python 3 is not installed. Data generation will be skipped."
    SKIP_DATA_GEN=true
fi

# Ensure directories exist
print_status "Ensuring required directories exist..."
mkdir -p airflow/{dags,logs,plugins}
mkdir -p dbt_project/{logs,target}
mkdir -p grafana/provisioning/{dashboards,datasources}
mkdir -p jupyter/work
mkdir -p mlflow
mkdir -p prometheus
mkdir -p superset

# Schema files are now properly named and will be executed in order by Docker
# No need to copy or rename - Docker postgres init handles this automatically

# Set correct permissions
print_status "Setting permissions..."
chmod -R 755 airflow superset dbt_project || true

# Pull/Build images
print_status "Pulling Docker images..."
$DOCKER_COMPOSE -f $COMPOSE_FILE pull --quiet postgres redis || {
    print_warning "Failed to pull some images, will retry during startup"
}

# Start services
print_status "Starting services with $COMPOSE_FILE..."
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
MAX_TRIES=30
TRIES=0
while ! docker exec saas_platform_postgres pg_isready -U saas_user &> /dev/null; do
    TRIES=$((TRIES+1))
    if [ $TRIES -eq $MAX_TRIES ]; then
        print_error "PostgreSQL failed to start after $MAX_TRIES attempts"
        echo "Checking logs:"
        docker logs saas_platform_postgres --tail 20
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "PostgreSQL is ready"

# Extra wait for database initialization
sleep 5

# Run data generation if not skipped
if [[ "$SKIP_DATA_GEN" == false ]] && command -v python3 &> /dev/null; then
    print_status "Generating deterministic dataset..."
    
    # Use the deterministic data generation script
    if [[ -f "scripts/generate_all_deterministic.py" ]]; then
        python3 scripts/generate_all_deterministic.py || {
            print_warning "Data generation failed. Check logs for details."
        }
    else
        print_warning "Data generation script not found"
    fi
else
    print_warning "Skipping data generation"
fi

# Run dbt
print_status "Running dbt transformations..."
docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt deps && dbt seed && dbt run" || {
    print_warning "dbt transformations failed. This is normal on first run if no data exists yet."
}

# Initialize Superset
print_status "Initializing Apache Superset..."
docker exec saas_platform_superset superset db upgrade || print_warning "Superset db upgrade failed"
docker exec saas_platform_superset superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin_password_2024 2>/dev/null || print_warning "Admin user may already exist"
docker exec saas_platform_superset superset init || print_warning "Superset init failed"

# Import dashboards if available
if [[ -f "superset/dashboards/sales/import_sales_dashboard.sql" ]]; then
    print_status "Importing sample dashboards..."
    docker exec -i saas_platform_postgres psql -U saas_user -d superset_db < superset/dashboards/sales/import_sales_dashboard.sql 2>/dev/null || {
        print_warning "Dashboard import failed - this is normal on first run"
    }
fi

# Display summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    🎉 Setup Complete! 🎉                      "
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Access your services:"
echo "───────────────────────────────────────────────────────────────"
echo ""
echo "📈 ${GREEN}Superset${NC} (Business Intelligence)"
echo "   URL: http://localhost:8088"
echo "   Username: admin"
echo "   Password: admin_password_2024"
echo ""
echo "🔬 ${GREEN}Jupyter Lab${NC} (Data Science Notebooks)"
echo "   URL: http://localhost:8888"
echo "   Token: saas_ml_token_2024"
echo ""
echo "🗄️  ${GREEN}PostgreSQL${NC} (Database)"
echo "   Host: localhost:5432"
echo "   Database: saas_platform_dev"
echo "   Username: saas_user"
echo "   Password: saas_secure_password_2024"
echo ""

if [[ "$COMPOSE_FILE" == "docker-compose.full.yml" ]]; then
    echo "🔄 ${GREEN}Airflow${NC} (Workflow Orchestration)"
    echo "   URL: http://localhost:8080"
    echo "   Username: admin"
    echo "   Password: airflow_admin_2024"
    echo ""
    echo "🤖 ${GREEN}MLflow${NC} (ML Experiment Tracking)"
    echo "   URL: http://localhost:5001"
    echo ""
    echo "📊 ${GREEN}Grafana${NC} (System Monitoring)"
    echo "   URL: http://localhost:3000"
    echo "   Username: admin"
    echo "   Password: grafana_admin_2024"
    echo ""
fi

echo "───────────────────────────────────────────────────────────────"
echo ""
echo "📚 Next steps:"
echo "   1. Visit Superset to explore dashboards"
echo "   2. Check out the education materials in /edu"
echo "   3. Try the SQL exercises in Jupyter notebooks"
echo ""
echo "🛠️  Useful commands:"
echo "   View logs:        $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f [service]"
echo "   Stop services:    $DOCKER_COMPOSE -f $COMPOSE_FILE down"
echo "   Restart service:  $DOCKER_COMPOSE -f $COMPOSE_FILE restart [service]"
echo ""

# Run validation
if [[ -f "validate_setup.sh" ]]; then
    print_status "Running validation checks..."
    ./validate_setup.sh --quiet || {
        print_warning "Some validation checks failed. This may be normal on first setup."
    }
fi

echo "✨ Happy learning!"
echo ""