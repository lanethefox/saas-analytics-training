# Ship It - Task List

## 1. File Organization
- [ ] Move all curriculum files to `/education` directory
- [ ] Consolidate scattered documentation into `/docs`
- [ ] Clean up root directory (move scripts to appropriate folders)
- [ ] Delete or archive development/testing files

## 2. Documentation Refactor
- [ ] Create single README.md with clear sections:
  - What this is
  - Quick start (docker-compose up)
  - Education modules overview
  - Architecture diagram
- [ ] Move detailed docs to `/docs` folder
- [ ] Create SETUP.md with prerequisites and install steps

## 3. Educational Package
- [ ] Create `/education/workday-simulations` with:
  - Day in the life scenarios for each role
  - Morning dashboard checks
  - Stakeholder requests to fulfill
  - End of day reporting
- [ ] Add `/education/quarterly-projects` with:
  - Q1: Pipeline optimization (Sales)
  - Q2: Churn reduction (CS)
  - Q3: Attribution model (Marketing)
  - Q4: Feature adoption (Product)
- [ ] Link each project to specific OKRs and dashboard components

## 4. Data Generation Scripts
- [ ] Create `scripts/reset_data.sh` - wipes and reloads clean data
- [ ] Create `scripts/generate_data.py` with size options:
  - `--small` (1K accounts)
  - `--medium` (10K accounts)  
  - `--large` (40K accounts)
- [ ] Make scripts work on any environment (remove hardcoded paths)

## 5. Easy Setup Script
```bash
#!/bin/bash
# setup.sh
echo "Setting up B2B SaaS Analytics Platform..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Please install Docker first"
    exit 1
fi

# Clone if needed
if [ ! -d ".git" ]; then
    git clone https://github.com/yourusername/data-platform .
fi

# Setup environment
cp .env.example .env

# Build and start
docker-compose build
docker-compose up -d

# Wait for services
echo "Waiting for services to start..."
sleep 30

# Load sample data
docker-compose exec postgres bash -c "cd /app && python scripts/generate_data.py --small"

echo "Done! Visit http://localhost:8088 for Superset (admin/admin)"
```

## 6. Docker & Environment
- [ ] Update docker-compose.yml to use consistent service names
- [ ] Create .env.example with all required variables
- [ ] Ensure all paths are relative/containerized
- [ ] Add health checks to all services
- [ ] Set resource limits for education use

## 7. Create .gitignore
```gitignore
# Environment
.env
.env.local

# Data
*.csv
*.parquet
/data/

# Logs
*.log
/logs/

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/
env/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/

# dbt
target/
dbt_packages/
logs/

# Docker
docker-compose.override.yml
```

## 8. GitHub Prep
- [ ] Create clean branch for education release
- [ ] Add LICENSE file (MIT or Apache 2.0)
- [ ] Write education-focused README
- [ ] Tag release as `v1.0-education`
- [ ] Push to GitHub:
```bash
git add .
git commit -m "Educational release v1.0"
git tag -a v1.0-education -m "First educational release"
git push origin main --tags
```

## 9. Quick Test Checklist
- [ ] Clone fresh repo
- [ ] Run setup.sh
- [ ] Verify all services start
- [ ] Run sample queries in Superset
- [ ] Test data reset script
- [ ] Confirm curriculum links work

## That's It!
Focus on making it work out-of-the-box. Everything else can be improved later based on user feedback.