# Apache Superset Guide

## 🚀 Quick Start

### Access Superset
- **URL**: http://localhost:8088
- **Username**: `admin`
- **Password**: `admin_password_2024`

### Database Connection
To add the main analytics database connection in Superset:
```
postgresql://superset_readonly:superset_readonly_password_2024@postgres:5432/saas_platform_dev
```

## 📋 Essential Commands

### Container Management
```bash
# Start Superset
docker-compose up -d superset

# Restart Superset  
docker restart saas_platform_superset

# View Superset logs
docker logs -f saas_platform_superset

# Access Superset shell
docker exec -it saas_platform_superset bash
```

### Setup & Testing
```bash
# Run automated setup
python superset/setup_superset.py

# Test database connection
./superset/connection_helper.sh

# Full system test
./superset/test_superset.sh
```

## 🎯 Key Features

### Available Data
- **Entity Tables**: All 7 core entity tables (customers, devices, users, etc.)
- **History Tables**: Complete change tracking for temporal analysis
- **Grain Tables**: Pre-aggregated data for fast reporting
- **Mart Models**: Business-ready analytical models

### Core Capabilities
- **SQL Lab**: Interactive SQL editor for data exploration
- **Chart Builder**: 40+ visualization types
- **Dashboard Designer**: Drag-and-drop dashboard creation
- **Data Exploration**: Self-service analytics interface

### Performance Features
- **Redis Caching**: Fast query results
- **Async Queries**: Long-running queries in background
- **Optimized Tables**: Strategic grain tables for speed

## 🔧 Troubleshooting

### Common Issues

**Can't connect to database:**
```bash
# Check database is running
docker ps | grep postgres

# Test connection
docker exec -it saas_platform_postgres psql -U superset_readonly -d saas_platform_dev -c "SELECT 1;"
```

**Performance issues:**
```bash
# Clear cache
docker exec -it saas_platform_redis redis-cli FLUSHDB

# Restart Superset
docker restart saas_platform_superset
```

**Login problems:**
```bash
# Reset admin password
docker exec -it saas_platform_superset superset fab reset-password --username admin
```

## 📊 Pre-Built Dashboards

### Executive Dashboard
- MRR/ARR tracking
- Customer health overview
- Churn risk analysis
- Growth metrics

### Marketing Dashboard
- Campaign performance
- Channel attribution
- CAC/LTV analysis
- Conversion funnels

### Operations Dashboard
- Device uptime monitoring
- Location performance
- Real-time alerts
- Capacity planning

## 🛠️ Advanced Configuration

### Adding New Users
```bash
docker exec -it saas_platform_superset superset fab create-user \
    --username newuser \
    --firstname First \
    --lastname Last \
    --email user@example.com \
    --role Admin
```

### Importing Dashboards
1. Go to Settings → Import Dashboards
2. Upload dashboard JSON files
3. Map database connections
4. Save and refresh

### Performance Tuning
- Use grain tables for time-series data
- Enable SQL Lab result caching
- Set appropriate cache timeouts
- Use database query optimization

## 📚 Learning Resources

### Key Concepts
- **Entity-Centric Modeling**: How our data is organized
- **Three-Table Pattern**: Atomic/History/Grain architecture
- **Self-Service Analytics**: Empowering business users
- **Performance Optimization**: Query and caching strategies

### Best Practices
- Start with grain tables for faster queries
- Use filters to limit data before aggregating
- Cache frequently-used dashboards
- Document your metrics and calculations

## ✅ Health Check

Run this to verify everything is working:
```bash
# Check all services
docker ps | grep -E "(superset|postgres|redis)"

# Test database connection
./superset/test_superset.sh

# Access web UI
curl -s http://localhost:8088/health | grep "OK"
```

## 🎉 You're Ready!

With Superset running, you can:
1. Explore the entity tables in SQL Lab
2. Create custom visualizations
3. Build dashboards for different teams
4. Share insights across the organization

Need help? Check the logs:
```bash
docker logs saas_platform_superset
```