# B2B SaaS Analytics Platform - PowerShell Setup Script
# This script sets up the platform with Docker on Windows using PowerShell

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "B2B SaaS Analytics Platform - PowerShell Setup" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker version | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running or not installed." -ForegroundColor Red
    Write-Host "Please install Docker Desktop and ensure it's running." -ForegroundColor Yellow
    Write-Host "https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Parse command line arguments
param(
    [switch]$SkipData = $false,
    [switch]$Full = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host ""
    Write-Host "Usage: .\setup.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  -SkipData          Skip data generation step"
    Write-Host "  -Full              Use full stack with all services"
    Write-Host "  -Help              Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\setup.ps1                    # Core services + small dataset"
    Write-Host "  .\setup.ps1                    # Core services + deterministic data"
    Write-Host "  .\setup.ps1 -Full              # All services + small dataset"
    Write-Host "  .\setup.ps1 -SkipData          # Core services, no data"
    Write-Host ""
    exit 0
}

$ComposeFile = if ($Full) { "docker-compose.full.yml" } else { "docker-compose.yml" }

Write-Host "Starting setup with:" -ForegroundColor Green
Write-Host "- Using deterministic data generation"
Write-Host "- Skip data generation: $SkipData"
Write-Host "- Compose file: $ComposeFile"
Write-Host ""

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Done." -ForegroundColor Green
}

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose -f $ComposeFile down 2>$null

# Start services
Write-Host ""
Write-Host "Starting Docker services..." -ForegroundColor Yellow
docker-compose -f $ComposeFile up -d

# Wait for PostgreSQL to be ready
Write-Host ""
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$postgresReady = $false
$attempts = 0
$maxAttempts = 30

while (-not $postgresReady -and $attempts -lt $maxAttempts) {
    Start-Sleep -Seconds 2
    try {
        docker-compose exec -T postgres pg_isready -U saas_user 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $postgresReady = $true
        }
    } catch {
        # Continue waiting
    }
    
    if (-not $postgresReady) {
        Write-Host "PostgreSQL not ready yet, waiting... ($attempts/$maxAttempts)" -ForegroundColor Yellow
        $attempts++
    }
}

if ($postgresReady) {
    Write-Host "PostgreSQL is ready!" -ForegroundColor Green
} else {
    Write-Host "ERROR: PostgreSQL failed to start within timeout!" -ForegroundColor Red
    exit 1
}

# Generate data if not skipped
if (-not $SkipData) {
    Write-Host ""
    Write-Host "Generating deterministic data..." -ForegroundColor Yellow
    
    # Check if Python is available
    try {
        python --version | Out-Null
    } catch {
        Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "Or use -SkipData flag to skip data generation." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Install Python dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt 2>$null | Out-Null
    
    # Run deterministic data generation
    python scripts/generate_all_deterministic.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Data generation failed!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "Skipping data generation as requested." -ForegroundColor Yellow
}

# Run dbt transformations
Write-Host ""
Write-Host "Running dbt transformations..." -ForegroundColor Yellow
docker-compose exec -T dbt-core bash -c "cd /opt/dbt_project && dbt deps && dbt run"
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: dbt transformations failed!" -ForegroundColor Yellow
    Write-Host "You may need to run them manually later." -ForegroundColor Yellow
}

# Validate deployment
Write-Host ""
Write-Host "Validating deployment..." -ForegroundColor Yellow
docker-compose ps

# Show access information
Write-Host ""
Write-Host "====================================================" -ForegroundColor Green
Write-Host "Platform is ready!" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access points:" -ForegroundColor Cyan
Write-Host "- Superset (BI): http://localhost:8088 (admin/admin)"
Write-Host "- Jupyter Lab: http://localhost:8888"
Write-Host "- PostgreSQL: localhost:5432 (saas_user/saas_secure_password_2024)"
Write-Host "- Redis: localhost:6379"
Write-Host ""
Write-Host "To view Jupyter token:" -ForegroundColor Yellow
Write-Host "  docker logs saas_platform_jupyter"
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "  docker-compose -f $ComposeFile down"
Write-Host ""
Write-Host "To remove all data and start fresh:" -ForegroundColor Yellow
Write-Host "  docker-compose -f $ComposeFile down -v"
Write-Host ""
Read-Host "Press Enter to continue"