#!/bin/bash

# B2B SaaS Analytics Platform - Improved Setup Script
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
        print_success "Environment file created from .env.example"
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

# Install Python dependencies if needed
print_status "Checking Python dependencies..."
if ! python3 -c "import psycopg2" 2>/dev/null; then
    print_status "Installing psycopg2-binary..."
    pip3 install psycopg2-binary || {
        print_warning "Failed to install psycopg2-binary. Data generation may not work."
    }
fi

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose down 2>/dev/null || true

# Remove old volumes if doing fresh install
if [ "$1" == "--fresh" ]; then
    print_warning "Removing old data volumes for fresh install..."
    docker-compose down -v 2>/dev/null || true
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

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker-compose exec -T postgres pg_isready -U saas_user -d saas_platform_dev &>/dev/null; then
        print_success "PostgreSQL is ready!"
        break
    fi
    echo -n "."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    print_error "PostgreSQL failed to start in time!"
    docker-compose logs postgres
    exit 1
fi

# Wait a bit more to ensure all schemas are created
print_status "Waiting for database initialization..."
sleep 10

# Verify raw schema exists
print_status "Verifying database schema..."
docker-compose exec -T postgres psql -U saas_user -d saas_platform_dev -c "\dn" | grep -q "raw" || {
    print_error "Raw schema not found! Creating it manually..."
    docker-compose exec -T postgres psql -U saas_user -d saas_platform_dev -c "CREATE SCHEMA IF NOT EXISTS raw;"
}

# Load sample data
print_status "Loading sample data..."
if [ -f "scripts/generate_data.py" ]; then
    print_status "Running data generation script..."
    python3 scripts/generate_data.py --size small || {
        print_warning "Data generation failed. Trying alternative methods..."
        
        # Try generate_all_data.py as fallback
        if [ -f "scripts/generate_all_data.py" ]; then
            print_status "Trying generate_all_data.py..."
            cd scripts && python3 generate_all_data.py && cd .. || {
                print_warning "Alternative data generation also failed."
            }
        fi
        
        # As last resort, create minimal data
        print_status "Creating minimal test data..."
        docker-compose exec -T postgres psql -U saas_user -d saas_platform_dev << 'EOF'
-- Ensure raw schema exists
CREATE SCHEMA IF NOT EXISTS raw;

-- Create minimal accounts if table exists
INSERT INTO raw.app_database_accounts (id, name, created_at, industry, employee_count, annual_revenue)
SELECT 
    'test-' || generate_series::text,
    'Test Company ' || generate_series,
    NOW() - (random() * interval '365 days'),
    CASE (random() * 4)::int 
        WHEN 0 THEN 'Technology'
        WHEN 1 THEN 'Healthcare'
        WHEN 2 THEN 'Retail'
        ELSE 'Manufacturing'
    END,
    (random() * 1000 + 10)::int,
    (random() * 50000000 + 1000000)::bigint
FROM generate_series(1, 10)
ON CONFLICT (id) DO NOTHING;
EOF
    }
else
    print_warning "Data generation script not found. Platform will start with empty database."
fi

# Wait for other services
print_status "Waiting for all services to initialize..."
sleep 20

# Run dbt models
print_status "Running dbt transformations..."
if docker-compose ps dbt | grep -q "Up"; then
    docker-compose exec -T dbt bash -c "cd /opt/dbt_project && dbt deps --profiles-dir . 2>/dev/null || true" || true
    docker-compose exec -T dbt bash -c "cd /opt/dbt_project && dbt run --profiles-dir ." || {
        print_warning "dbt run failed. This is expected if no data was loaded."
        print_warning "You can run dbt manually later with: docker-compose exec dbt bash -c 'cd /opt/dbt_project && dbt run --profiles-dir .'"
    }
else
    print_warning "dbt container not running. Skipping transformations."
fi

# Check service health
print_status "Checking service health..."
docker-compose ps

# Create validation script
cat > validate_setup.sh << 'EOF'
#!/bin/bash
# Platform validation script

echo "🔍 Validating platform setup..."
echo ""

# Check services
echo "📦 Docker Services:"
docker-compose ps --format "table {{.Service}}\t{{.State}}\t{{.Ports}}"
echo ""

# Check database
echo "💾 Database Check:"
docker-compose exec -T postgres psql -U saas_user -d saas_platform_dev -c "
SELECT 'Schemas' as check_type, count(*) as count 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
UNION ALL
SELECT 'Tables', count(*) 
FROM information_schema.tables 
WHERE table_schema = 'raw'
UNION ALL
SELECT 'Accounts', count(*) 
FROM raw.app_database_accounts
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'raw' 
    AND table_name = 'app_database_accounts'
);" 2>/dev/null || echo "Database check failed"
echo ""

# Check service endpoints
echo "🌐 Service Endpoints:"
echo -n "Superset (http://localhost:8088): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/health || echo "Failed"
echo ""
echo -n "Jupyter (http://localhost:8888): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8888 || echo "Failed"
echo ""

echo ""
echo "✅ Validation complete!"
EOF

chmod +x validate_setup.sh

# Display final message
echo ""
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
echo "  Database: saas_platform_dev"
echo ""

if docker-compose ps | grep -q "grafana.*Up"; then
    echo "  Grafana (monitoring):    http://localhost:3000"
    echo "  Username: admin"
    echo "  Password: grafana_admin_2024"
    echo ""
fi

if docker-compose ps | grep -q "airflow.*Up"; then
    echo "  Airflow (orchestration): http://localhost:8080"
    echo "  Username: admin"
    echo "  Password: admin_password_2024"
    echo ""
fi

echo "=================================================="
echo ""
echo "📚 Next steps:"
echo "1. Run ./validate_setup.sh to check platform health"
echo "2. Open Superset and explore the dashboards"
echo "3. Check out the curriculum in education/"
echo "4. Try the SQL tutorial in Jupyter Lab"
echo ""

if [ -f "scripts/generate_data.py" ]; then
    echo "💡 To load more data, run:"
    echo "   python3 scripts/generate_data.py --size medium"
    echo ""
fi

echo "Need help? Check SETUP.md for detailed instructions!"
echo ""

# Run validation
print_status "Running initial validation..."
./validate_setup.sh