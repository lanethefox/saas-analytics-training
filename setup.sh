#!/bin/bash

# B2B SaaS Analytics Platform - Educational Setup Script
# This script sets up the complete analytics platform for educational use

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
echo "=================================================="
echo "🎓 B2B SaaS Analytics Platform - Educational Setup"
echo "=================================================="
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

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Check available memory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DOCKER_MEMORY=$(docker system info --format '{{.MemTotal}}' 2>/dev/null || echo "0")
    DOCKER_MEMORY_GB=$((DOCKER_MEMORY / 1073741824))
else
    # Linux/WSL
    DOCKER_MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
fi

if [ "$DOCKER_MEMORY_GB" -lt 8 ]; then
    print_warning "Less than 8GB RAM detected. Using lightweight mode."
    export LIGHTWEIGHT_MODE=true
fi

print_success "All prerequisites met!"

# Create necessary directories
print_status "Creating project directories..."
mkdir -p data logs dbt_project/logs
print_success "Directories created"

# Setup environment
print_status "Setting up environment..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Environment file created"
    else
        print_error ".env.example not found! Creating basic .env file..."
        cat > .env << 'EOF'
# Database Configuration
POSTGRES_DB=saas_platform_dev
POSTGRES_USER=saas_user
POSTGRES_PASSWORD=saas_secure_password_2024
DB_HOST=postgres
DB_PORT=5432

# Superset Configuration
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin_password_2024
SUPERSET_SECRET_KEY=your_secret_key_here_change_in_production

# Jupyter Configuration
JUPYTER_TOKEN=saas_ml_token_2024

# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=grafana_admin_2024

# Airflow Configuration
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin_password_2024
AIRFLOW_SECRET_KEY=your_airflow_secret_key_here
EOF
        print_success "Basic environment file created"
    fi
else
    print_success "Environment file already exists"
fi

# Pull Docker images
print_status "Pulling Docker images (this may take a few minutes)..."
docker-compose pull

# Build containers
print_status "Building containers..."
docker-compose build --quiet

# Start services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to initialize..."
sleep 30

# Check service health
print_status "Checking service health..."
POSTGRES_HEALTHY=$(docker-compose ps postgres | grep -c "Up" || true)
SUPERSET_HEALTHY=$(docker-compose ps superset | grep -c "Up" || true)

if [ "$POSTGRES_HEALTHY" -eq 0 ]; then
    print_error "PostgreSQL failed to start!"
    docker-compose logs postgres
    exit 1
fi

if [ "$SUPERSET_HEALTHY" -eq 0 ]; then
    print_warning "Superset may still be initializing..."
fi

print_success "Core services are running"

# Load sample data
print_status "Loading sample data..."
if command -v python3 &> /dev/null; then
    # Try to run data generation script
    if [ -f "scripts/generate_data.py" ]; then
        python3 scripts/generate_data.py --size small || {
            print_warning "Data generation script failed. Will create minimal test data..."
            # Create minimal test data using SQL
            docker-compose exec -T postgres psql -U saas_user -d saas_platform_dev << 'EOF'
-- Create minimal test data
INSERT INTO raw.app_database_accounts (id, name, created_at, industry, employee_count, annual_revenue)
VALUES 
('test-001', 'Test Company 1', NOW(), 'Technology', 50, 5000000),
('test-002', 'Test Company 2', NOW(), 'Healthcare', 100, 10000000),
('test-003', 'Test Company 3', NOW(), 'Retail', 200, 20000000);
EOF
        }
    else
        print_warning "Data generation script not found. Platform will start with empty database."
    fi
else
    print_warning "Python not available. Platform will start with empty database."
fi

# Run dbt models
print_status "Running dbt transformations..."
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt run --profiles-dir ." || {
    print_warning "dbt run failed. You may need to run it manually later."
}

# Final checks
print_status "Performing final checks..."
echo ""

# Display service URLs
echo "=================================================="
echo "🎉 Setup Complete! Your platform is ready."
echo "=================================================="
echo ""
echo "📊 Access your services at:"
echo ""
echo "  Apache Superset (BI):    http://localhost:8088"
echo "  Username: admin"
echo "  Password: admin_password_2024"
echo ""
echo "  Jupyter Lab (notebooks): http://localhost:8888"
echo "  Token: saas_ml_token_2024"
echo ""
echo "  PostgreSQL (database):   localhost:5432"
echo "  Username: saas_user"
echo "  Password: saas_secure_password_2024"
echo ""
echo "  Grafana (monitoring):    http://localhost:3000"
echo "  Username: admin"
echo "  Password: grafana_admin_2024"
echo ""
echo "=================================================="
echo ""
echo "📚 Next steps:"
echo "1. Open Superset and explore the dashboards"
echo "2. Check out the curriculum in /education"
echo "3. Try the example queries in Jupyter Lab"
echo ""
echo "Need help? Check SETUP.md or join our Discord!"
echo ""

# Create a validation script for users to run later
cat > validate_setup.sh << 'EOF'
#!/bin/bash
# Quick validation script
echo "🔍 Validating platform setup..."

# Check if services are running
docker-compose ps

# Check database
echo ""
echo "📊 Checking database..."
docker-compose exec postgres psql -U saas_user -d saas_platform_dev -c "SELECT COUNT(*) as accounts FROM raw.app_database_accounts;" 2>/dev/null || echo "Database check failed"

# Check Superset
echo ""
echo "📈 Checking Superset..."
curl -s -o /dev/null -w "Superset HTTP status: %{http_code}\n" http://localhost:8088/health || echo "Superset check failed"

echo ""
echo "✅ Validation complete!"
EOF

chmod +x validate_setup.sh

print_success "Setup script complete!"
print_success "Run ./validate_setup.sh to check platform health anytime"