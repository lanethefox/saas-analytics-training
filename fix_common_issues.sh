#!/bin/bash

echo "========================================="
echo "Fixing Common Test Setup Issues"
echo "========================================="

# Create missing directories
echo "Creating missing directories..."
mkdir -p airflow/logs
mkdir -p airflow/plugins
mkdir -p jupyter
mkdir -p superset/dashboards
mkdir -p grafana/provisioning
mkdir -p prometheus

# Remove directory that should be a file
if [ -d "airflow/airflow.cfg" ]; then
    echo "Removing airflow.cfg directory..."
    rm -rf airflow/airflow.cfg
fi

# Copy minimal airflow config if needed
if [ ! -f "airflow/airflow.cfg" ] && [ -f "airflow/airflow_minimal.cfg" ]; then
    echo "Copying minimal airflow config..."
    cp airflow/airflow_minimal.cfg airflow/airflow.cfg
fi

# Handle 01_schema.sql directory issue
if [ -d "database/01_schema.sql" ]; then
    echo "Found 01_schema.sql as directory, checking for actual schema file..."
    # Use the complete schema file instead
    if [ -f "database/00_complete_raw_schema_fixed.sql" ]; then
        echo "Using 00_complete_raw_schema_fixed.sql as main schema"
    fi
fi

# Create prometheus config if missing
if [ ! -f "prometheus/prometheus.yml" ]; then
    echo "Creating minimal prometheus config..."
    cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']
EOF
fi

# Create grafana provisioning structure
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/provisioning/datasources

# Set correct permissions
echo "Setting permissions..."
chmod -R 755 airflow/dags
chmod -R 755 dbt_project
chmod -R 755 jupyter
chmod -R 755 superset

echo "========================================="
echo "Common issues fixed!"
echo "========================================="
echo ""
echo "You can now run:"
echo "  ./test_minimal_setup.sh"
echo ""
echo "Or use the full test setup:"
echo "  docker-compose -f docker-compose.test.yml up -d"