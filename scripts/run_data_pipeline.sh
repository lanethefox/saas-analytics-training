#!/bin/bash
"""
🚀 SaaS Platform Data Generation & Loading Pipeline
==================================================

Two-tier approach:
0. XS scale: 100 customers (quick testing)
1. SMALL scale: 1,000 customers (testing)
2. ENTERPRISE scale: 40,000 customers (production)

Usage:
  ./run_data_pipeline.sh xs         # Generate & load XS dataset (3-5 min)
  ./run_data_pipeline.sh small      # Generate & load small dataset
  ./run_data_pipeline.sh enterprise # Generate & load enterprise dataset
  ./run_data_pipeline.sh all        # Run xs, then small, then enterprise
"""

set -e  # Exit on any error

SCALE=${1:-small}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DATA_DIR="$SCRIPT_DIR/../data/synthetic"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python dependencies
    if ! python3 -c "import psycopg2, faker, numpy, pandas" 2>/dev/null; then
        print_error "Missing Python dependencies. Please run:"
        echo "pip3 install psycopg2-binary faker numpy pandas"
        exit 1
    fi
    print_step "Python dependencies verified"
    
    # Check PostgreSQL connection
    if ! psql -d saas_platform_dev -c "SELECT 1;" &>/dev/null; then
        print_error "Cannot connect to PostgreSQL database 'saas_platform_dev'"
        echo "Please ensure PostgreSQL is running and database exists"
        exit 1
    fi
    print_step "PostgreSQL connection verified"
    
    # Check disk space (rough estimate)
    available_space=$(df -h "$DATA_DIR" 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//')
    if [[ "$SCALE" == "enterprise" ]] && [[ ${available_space%.*} -lt 100 ]]; then
        print_warning "Enterprise scale may require 100GB+ of disk space"
        echo "Available space: ${available_space}GB"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

run_xs_scale() {
    print_header "Running XS Scale Generation (100 customers)"
    
    print_step "Step 1: Generating synthetic data..."
    cd "$SCRIPT_DIR"
    time python3 generate_synthetic_data.py --scale xs --months 60
    
    print_step "Step 2: Creating database schema..."
    psql -d saas_platform_dev -f ../database/01_main_schema.sql
    
    print_step "Step 3: Loading data into PostgreSQL..."
    time python3 load_synthetic_data.py
    
    print_step "Step 4: Verifying data load..."
    psql -d saas_platform_dev -c "
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as rows
        FROM pg_stat_user_tables 
        WHERE schemaname = 'raw'
        ORDER BY n_tup_ins DESC;
    "
}

run_small_scale() {
    print_header "Running SMALL Scale Generation (1,000 customers)"
    
    print_step "Step 1: Generating synthetic data..."
    cd "$SCRIPT_DIR"
    time python3 generate_synthetic_data.py --scale small --months 60
    
    print_step "Step 2: Creating database schema..."
    psql -d saas_platform_dev -f ../database/01_main_schema.sql
    
    print_step "Step 3: Loading data into PostgreSQL..."
    time python3 load_synthetic_data.py
    
    print_step "Step 4: Verifying data load..."
    psql -d saas_platform_dev -c "
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as rows
        FROM pg_stat_user_tables 
        WHERE schemaname = 'raw'
        ORDER BY n_tup_ins DESC;
    "
}

run_enterprise_scale() {
    print_header "Running ENTERPRISE Scale Generation (40,000 customers)"
    
    print_warning "This will take 4-7 hours and generate 60TB+ of data"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_step "Enterprise scale generation cancelled"
        return
    fi
    
    print_step "Step 1: Generating synthetic data..."
    cd "$SCRIPT_DIR"
    time python3 generate_synthetic_data.py --scale enterprise --months 60
    
    print_step "Step 2: Creating database schema (if not exists)..."
    psql -d saas_platform_dev -f ../database/01_main_schema.sql
    
    print_step "Step 3: Loading data with optimized parallel pipeline..."
    time python3 load_synthetic_data_optimized.py
    
    print_step "Step 4: Creating performance indexes..."
    psql -d saas_platform_dev -c "
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tap_events_device_timestamp 
        ON raw.tap_events(device_id, timestamp);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tap_events_location_timestamp 
        ON raw.tap_events(location_id, timestamp);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_user_start 
        ON raw.user_sessions(user_id, session_start);
    "
    
    print_step "Step 5: Analyzing table statistics..."
    psql -d saas_platform_dev -c "ANALYZE;"
}

show_final_stats() {
    print_header "Final Database Statistics"
    
    psql -d saas_platform_dev -c "
        WITH table_stats AS (
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as rows,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_stat_user_tables 
            WHERE schemaname = 'raw'
        )
        SELECT 
            tablename,
            rows,
            size
        FROM table_stats
        ORDER BY rows DESC;
        
        SELECT 
            pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size
        FROM pg_stat_user_tables 
        WHERE schemaname = 'raw';
    "
}

main() {
    case $SCALE in
        "xs")
            check_prerequisites
            run_xs_scale
            show_final_stats
            print_step "XS scale generation completed successfully!"
            ;;
        "small")
            check_prerequisites
            run_small_scale
            show_final_stats
            print_step "Small scale generation completed successfully!"
            ;;
        "enterprise")
            check_prerequisites
            run_enterprise_scale
            show_final_stats
            print_step "Enterprise scale generation completed successfully!"
            ;;
        "all")
            check_prerequisites
            run_xs_scale
            echo -e "\n${YELLOW}XS scale complete. Press Enter to continue with Small scale...${NC}"
            read
            run_small_scale
            echo -e "\n${YELLOW}Small scale complete. Press Enter to continue with Enterprise scale...${NC}"
            read
            run_enterprise_scale
            show_final_stats
            print_step "All scales completed successfully!"
            ;;
        *)
            echo "Usage: $0 {xs|small|enterprise|all}"
            echo ""
            echo "Scales:"
            echo "  xs         - 100 customers, ~27M events (~14GB) [3-5 min]"
            echo "  small      - 1,000 customers, ~1.8B events (~911GB) [15-25 min]"
            echo "  enterprise - 40,000 customers, ~125B events (~62TB) [4-7 hours]"
            echo "  all        - Run xs, then small, then enterprise"
            exit 1
            ;;
    esac
}

main "$@"
