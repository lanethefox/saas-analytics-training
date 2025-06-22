# Installation Guide

This guide will help you set up the B2B SaaS Analytics Platform on your machine.

## Prerequisites

### Required Software
- **Docker Desktop**: [Download here](https://www.docker.com/products/docker-desktop)
  - Mac: 8GB RAM allocated to Docker
  - Windows: WSL2 enabled, 8GB RAM allocated
  - Linux: Docker and docker-compose installed
- **Python 3.8+**: For running data generation scripts
- **Git**: For cloning the repository

### System Requirements
- 4GB RAM minimum for core services (8GB for full stack)
- 20GB free disk space
- Modern CPU (2+ cores)
- Stable internet connection for initial setup

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/data-platform
cd data-platform
```

### 2. Run the Setup Script

**Linux/macOS:**
```bash
# Make the script executable
chmod +x setup.sh

# Run the setup
./setup.sh
```

**Windows (Command Prompt):**
```batch
setup.bat
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

The setup script will:
- Check prerequisites
- Create necessary directories
- Copy environment configuration
- Build Docker containers
- Start all services
- Load sample data (1,000 accounts)

**Expected time**: 10-15 minutes on first run

### 3. Verify Installation
```bash
# Run the validation script
./validate_setup.sh
```

This will check:
- Docker services status
- Database connectivity
- Schema and table creation
- Service endpoints

### 4. Troubleshooting

If you encounter any issues during setup, see our comprehensive [Troubleshooting Guide](TROUBLESHOOTING.md) which covers:
- Data generation failures
- Database connection issues
- Python dependency problems
- Docker memory issues
- Port conflicts
- Quick fixes and resets

### 5. Access the Platform

| Service | URL | Credentials |
|---------|-----|-------------|
| **Apache Superset** | http://localhost:8088 | admin / admin_password_2024 |
| **Jupyter Lab** | http://localhost:8888 | Token: saas_ml_token_2024 |
| **PostgreSQL** | localhost:5432 | saas_user / saas_secure_password_2024 |
| **Grafana** | http://localhost:3000 | admin / grafana_admin_2024 |

## Manual Installation (Alternative)

If the setup script doesn't work, follow these manual steps:

### 1. Create Environment File
```bash
cp .env.example .env
```

### 2. Create Required Directories
```bash
mkdir -p data logs dbt_project/logs
```

### 3. Build and Start Services
```bash
# Build all containers
docker-compose build

# Start services in background
docker-compose up -d

# Wait for services to initialize
sleep 30
```

### 4. Initialize the Database
```bash
# The database schema is automatically created by Docker
# Just generate sample data:
python3 scripts/generate_educational_data.py --size small

# Or use the original generator:
python3 scripts/generate_data.py --size small
```

### 5. Run dbt Models
```bash
docker exec saas_platform_dbt bash -c "cd /opt/dbt_project && dbt run --profiles-dir ."
```

## Loading Different Data Sizes

The platform supports multiple data sizes for different use cases:

```bash
# Tiny dataset (100 accounts) - Quick demos
python3 scripts/generate_data.py --size tiny

# Small dataset (1,000 accounts) - Default, exercises
python3 scripts/generate_data.py --size small

# Medium dataset (10,000 accounts) - Projects
python3 scripts/generate_data.py --size medium

# Large dataset (40,000 accounts) - Full platform
python3 scripts/generate_data.py --size large
```

## Common Issues

### Docker Memory Error
**Problem**: "Cannot allocate memory" or services crashing
**Solution**: Increase Docker Desktop memory to 8GB minimum

### Port Already in Use
**Problem**: "bind: address already in use"
**Solution**: 
```bash
# Stop conflicting service or change port in docker-compose.yml
docker-compose down
# Edit docker-compose.yml to use different ports
docker-compose up -d
```

### Database Connection Failed
**Problem**: Cannot connect to PostgreSQL
**Solution**: 
```bash
# Check if postgres is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart the service
docker-compose restart postgres
```

### Superset Login Issues
**Problem**: Cannot log into Superset
**Solution**: 
```bash
# Reset Superset admin password
docker-compose exec superset superset fab reset-password --username admin
```

## Next Steps

1. **Run Automated Onboarding**: Verify your setup is complete
   ```bash
   python3 scripts/onboarding_automation.py --name "Your Name" --team "sales"
   ```
2. **Try Interactive SQL Tutorial**: Learn platform-specific queries
   ```bash
   # Open the tutorial at docs/onboarding/common/interactive-sql-tutorial.md
   # Copy queries to run in Jupyter Lab or psql
   ```
3. **Explore Dashboards**: Log into Superset and explore pre-built dashboards
4. **Review Metric Lineage**: Understand how metrics are calculated
   - See `/docs/onboarding/common/metric-lineage.md`
5. **Start Learning**: Follow the curriculum in `/education/curriculum_overview.md`
6. **Join Community**: Get help in our [Discord server](https://discord.gg/analytics-education)

## Uninstallation

To completely remove the platform:

```bash
# Stop and remove all containers
docker-compose down -v

# Remove the project directory
cd ..
rm -rf data-platform
```

## Need Help?

- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Search [GitHub Issues](https://github.com/yourusername/data-platform/issues)
- Ask in [Discord Community](https://discord.gg/analytics-education)
- Email: support@analytics-education.com

---

Remember: Learning analytics is a journey. Take it one step at a time, and don't hesitate to ask for help!