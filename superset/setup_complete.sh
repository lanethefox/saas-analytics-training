#!/bin/bash

# Superset Setup and Configuration Script
# This script configures Superset with the SaaS platform database and creates initial datasets

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

# Configuration variables
SUPERSET_URL="http://localhost:8088"
SUPERSET_USERNAME="admin"
SUPERSET_PASSWORD="admin_password_2024"
DATABASE_NAME="SaaS Platform Analytics"
MAX_ATTEMPTS=30

print_header "🚀 Apache Superset Setup and Configuration"

# Function to wait for Superset to be ready
wait_for_superset() {
    print_info "Waiting for Superset to be ready..."
    local attempt=1
    
    while [ $attempt -le $MAX_ATTEMPTS ]; do
        if curl -s -f "$SUPERSET_URL/health" > /dev/null 2>&1; then
            print_success "Superset is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$MAX_ATTEMPTS - Superset not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    print_error "Superset failed to start within expected time"
    return 1
}

# Function to check if database connection exists
check_database_connection() {
    print_info "Checking for existing database connection..."
    
    # This is a simple check - in production you'd use the API
    # For now, we'll assume we need to run the setup script
    return 1
}

# Function to run Python setup script
run_python_setup() {
    print_info "Running Python setup script to configure Superset..."
    
    if [ -f "superset/setup_superset.py" ]; then
        if python3 superset/setup_superset.py; then
            print_success "Python setup script completed successfully"
            return 0
        else
            print_warning "Python setup script had issues, continuing with manual setup"
            return 1
        fi
    else
        print_warning "Python setup script not found, proceeding with manual configuration"
        return 1
    fi
}

# Function to create admin user manually
create_admin_user() {
    print_info "Creating Superset admin user..."
    
    docker exec -i saas_platform_superset superset fab create-admin \
        --username "$SUPERSET_USERNAME" \
        --firstname "Admin" \
        --lastname "User" \
        --email "admin@example.com" \
        --password "$SUPERSET_PASSWORD" 2>/dev/null || {
        print_warning "Admin user may already exist"
    }
}

# Function to initialize Superset
initialize_superset() {
    print_info "Initializing Superset database and permissions..."
    
    docker exec -i saas_platform_superset superset db upgrade
    docker exec -i saas_platform_superset superset init
    
    print_success "Superset initialization completed"
}

# Main execution
main() {
    # Wait for Superset to be ready
    if ! wait_for_superset; then
        print_error "Cannot proceed with setup - Superset is not responding"
        exit 1
    fi
    
    # Initialize Superset
    initialize_superset
    
    # Create admin user
    create_admin_user
    
    # Try Python setup script first
    if ! run_python_setup; then
        print_warning "Python setup failed, manual configuration required"
        print_info "You can manually configure Superset by:"
        print_info "1. Visiting $SUPERSET_URL"
        print_info "2. Logging in with username: $SUPERSET_USERNAME, password: $SUPERSET_PASSWORD"
        print_info "3. Adding database connection to: postgresql://superset_readonly:superset_readonly_password_2024@postgres:5432/saas_platform_dev"
        print_info "4. Creating datasets for entity tables"
    fi
    
    print_header "✅ Superset Setup Complete!"
    
    echo "🎯 Next Steps:"
    echo "=============="
    echo "1. Access Superset: $SUPERSET_URL"
    echo "2. Username: $SUPERSET_USERNAME"
    echo "3. Password: $SUPERSET_PASSWORD"
    echo ""
    echo "📊 Available Entity Tables:"
    echo "=========================="
    echo "• entity_customers - Customer analytics and health scoring"
    echo "• entity_customers_daily - Daily customer snapshots"
    echo "• entity_devices - IoT device monitoring and performance"
    echo "• entity_devices_hourly - Hourly device metrics"
    echo "• entity_users - User engagement and behavior"
    echo "• entity_users_weekly - Weekly user activity"
    echo "• entity_subscriptions - Subscription revenue and lifecycle"
    echo "• entity_subscriptions_monthly - Monthly subscription metrics"
    echo "• entity_campaigns - Marketing campaign performance"
    echo "• entity_campaigns_daily - Daily campaign optimization"
    echo "• entity_locations - Location operations and health"
    echo "• entity_locations_weekly - Weekly location performance"
    echo "• entity_features - Product feature adoption"
    echo "• entity_features_monthly - Monthly feature metrics"
    echo ""
    echo "🔗 Database Connection Details:"
    echo "=============================="
    echo "Host: postgres"
    echo "Port: 5432"
    echo "Database: saas_platform_dev"
    echo "Username: superset_readonly"
    echo "Password: superset_readonly_password_2024"
    echo ""
    echo "📖 For detailed documentation, see: superset/README.md"
    
    print_success "Superset is ready for use!"
}

# Error handling
trap 'print_error "Setup interrupted or failed"' ERR

# Run main function
main "$@"
