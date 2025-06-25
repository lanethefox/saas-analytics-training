#!/bin/bash
# Setup script for macOS/Linux
# Creates a complete local data platform with PostgreSQL, synthetic data, and dbt transformations

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
POSTGRES_VERSION="15"

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Parse command line arguments
CHECK_ONLY=false
SKIP_SERVICES=false
# Deterministic data generation - no scale needed

while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --skip-services)
            SKIP_SERVICES=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--check-only] [--skip-services]"
            exit 1
            ;;
    esac
done

echo "🚀 SaaS Data Platform Setup (macOS/Linux)"
echo "=========================================="
echo "Using deterministic data generation"
echo "Skip services: $SKIP_SERVICES"
echo "Check only: $CHECK_ONLY"
echo

# Step 1: Check prerequisites
print_step "Checking prerequisites..."

# Check for Python 3
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
print_success "Python $PYTHON_VERSION found"

# Check for PostgreSQL client
if ! command_exists psql; then
    print_warning "PostgreSQL client not found. Installing may be required for database operations."
fi

# Check for dbt
if ! command_exists dbt; then
    print_warning "dbt not found. Will be installed in virtual environment."
fi

if $CHECK_ONLY; then
    print_success "Prerequisites check completed"
    exit 0
fi

# Step 2: Set up Python virtual environment
print_step "Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Created virtual environment"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Activated virtual environment"

# Step 3: Install Python dependencies
print_step "Installing Python dependencies..."

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python dependencies installed"

# Step 4: Initialize database
print_step "Initializing PostgreSQL database..."

cd "$SCRIPT_DIR"
python3 scripts/init_database.py

if [ $? -ne 0 ]; then
    print_error "Database initialization failed"
    exit 1
fi
print_success "Database initialized"

# Step 5: Deploy database schema
print_step "Deploying database schema..."

cd "$SCRIPT_DIR/database"
if [ -f "01_main_schema.sql" ]; then
    PGPASSWORD=saas_secure_password_2024 psql -h localhost -U saas_user -d saas_platform_dev -f 01_main_schema.sql > /dev/null 2>&1
    print_success "Database schema deployed"
else
    print_error "Schema file not found: database/01_main_schema.sql"
    exit 1
fi

# Step 6: Wipe existing data
print_step "Wiping existing data..."

cd "$SCRIPT_DIR"
python3 scripts/wipe_data.py
print_success "Data wiped"

# Step 7: Generate deterministic data
print_step "Generating deterministic data..."

python3 scripts/generate_all_deterministic.py

if [ $? -eq 0 ]; then
    print_success "Data generation completed"
else
    print_warning "Some generators failed, but continuing with available data"
fi

# Step 8: Load data into PostgreSQL
print_step "Loading data into PostgreSQL..."

python3 scripts/load_synthetic_data.py

if [ $? -ne 0 ]; then
    print_error "Data loading failed"
    exit 1
fi
print_success "Data loaded successfully"

# Step 9: Run dbt transformations
print_step "Running dbt transformations..."

cd "$SCRIPT_DIR/dbt_project"

# Install dbt dependencies
dbt deps > /dev/null 2>&1

# Run dbt
dbt run

if [ $? -ne 0 ]; then
    print_error "dbt transformations failed"
    exit 1
fi
print_success "dbt transformations completed"

# Step 10: Validate setup
print_step "Validating setup..."

cd "$SCRIPT_DIR"
if [ -f "scripts/validate_setup.py" ]; then
    python3 scripts/validate_setup.py
    if [ $? -eq 0 ]; then
        print_success "Setup validation passed"
    else
        print_warning "Setup validation had warnings"
    fi
else
    print_warning "Validation script not found, skipping validation"
fi

# Print summary
echo
echo "🎉 Setup completed successfully!"
echo "================================"
echo
echo "Database connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: saas_platform_dev"
echo "  User: saas_user"
echo "  Password: saas_secure_password_2024"
echo
echo "Next steps:"
echo "  1. Connect to PostgreSQL: psql -h localhost -U saas_user -d saas_platform_dev"
echo "  2. View dbt docs: cd dbt_project && dbt docs generate && dbt docs serve"
echo "  3. Run dbt tests: cd dbt_project && dbt test"
echo
echo "To reset and start over, run: ./setup_local_osx.sh"

# Deactivate virtual environment
deactivate