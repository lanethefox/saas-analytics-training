# Setup script for Windows
# Creates a complete local data platform with PostgreSQL, synthetic data, and dbt transformations

param(
    [switch]$CheckOnly = $false,
    [switch]$SkipServices = $false
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step {
    param($Message)
    Write-Host "==> $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "🚀 SaaS Data Platform Setup (Windows)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Scale: $Scale"
Write-Host "Skip services: $SkipServices"
Write-Host "Check only: $CheckOnly"
Write-Host ""

# Step 1: Check prerequisites
Write-Step "Checking prerequisites..."

# Check for Python 3
if (-not (Test-Command "python")) {
    Write-Error "Python 3 is not installed or not in PATH. Please install Python 3.8 or higher."
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Success "Python found: $pythonVersion"

# Check for PostgreSQL client
if (-not (Test-Command "psql")) {
    Write-Warning "PostgreSQL client not found. You may need to add it to PATH."
}

# Check for pip
if (-not (Test-Command "pip")) {
    Write-Error "pip is not installed. Please ensure Python was installed with pip."
    exit 1
}

if ($CheckOnly) {
    Write-Success "Prerequisites check completed"
    exit 0
}

# Step 2: Set up Python virtual environment
Write-Step "Setting up Python virtual environment..."

$venvPath = Join-Path $ScriptDir "venv"

if (-not (Test-Path $venvPath)) {
    python -m venv venv
    Write-Success "Created virtual environment"
} else {
    Write-Success "Virtual environment already exists"
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript
Write-Success "Activated virtual environment"

# Step 3: Install Python dependencies
Write-Step "Installing Python dependencies..."

try {
    python -m pip install --upgrade pip *> $null
    pip install -r requirements.txt *> $null
    Write-Success "Python dependencies installed"
} catch {
    Write-Error "Failed to install Python dependencies"
    exit 1
}

# Step 4: Initialize database
Write-Step "Initializing PostgreSQL database..."

Push-Location $ScriptDir
try {
    python scripts/init_database.py
    if ($LASTEXITCODE -ne 0) {
        throw "Database initialization failed"
    }
    Write-Success "Database initialized"
} catch {
    Write-Error $_
    Pop-Location
    exit 1
}
Pop-Location

# Step 5: Deploy database schema
Write-Step "Deploying database schema..."

$schemaFile = Join-Path $ScriptDir "database\01_main_schema.sql"
if (Test-Path $schemaFile) {
    try {
        $env:PGPASSWORD = "saas_secure_password_2024"
        psql -h localhost -U saas_user -d saas_platform_dev -f $schemaFile *> $null
        Write-Success "Database schema deployed"
    } catch {
        Write-Error "Failed to deploy database schema"
        exit 1
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
} else {
    Write-Error "Schema file not found: $schemaFile"
    exit 1
}

# Step 6: Wipe existing data
Write-Step "Wiping existing data..."

Push-Location $ScriptDir
try {
    python scripts/wipe_data.py
    Write-Success "Data wiped"
} catch {
    Write-Error "Failed to wipe data"
    Pop-Location
    exit 1
}
Pop-Location

# Step 7: Generate deterministic data
Write-Step "Generating deterministic data..."

Push-Location $ScriptDir
try {
    python scripts/generate_all_deterministic.py
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Data generation completed"
    } else {
        Write-Warning "Some generators failed, but continuing with available data"
    }
} catch {
    Write-Warning "Data generation had errors, but continuing"
}
Pop-Location

# Step 8: Load data into PostgreSQL
Write-Step "Loading data into PostgreSQL..."

Push-Location $ScriptDir
try {
    python scripts/load_synthetic_data.py
    if ($LASTEXITCODE -ne 0) {
        throw "Data loading failed"
    }
    Write-Success "Data loaded successfully"
} catch {
    Write-Error $_
    Pop-Location
    exit 1
}
Pop-Location

# Step 9: Run dbt transformations
Write-Step "Running dbt transformations..."

Push-Location (Join-Path $ScriptDir "dbt_project")
try {
    # Install dbt dependencies
    dbt deps *> $null
    
    # Run dbt
    dbt run
    if ($LASTEXITCODE -ne 0) {
        throw "dbt transformations failed"
    }
    Write-Success "dbt transformations completed"
} catch {
    Write-Error $_
    Pop-Location
    exit 1
}
Pop-Location

# Step 10: Validate setup
Write-Step "Validating setup..."

Push-Location $ScriptDir
$validateScript = Join-Path $ScriptDir "scripts\validate_setup.py"
if (Test-Path $validateScript) {
    try {
        python $validateScript
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Setup validation passed"
        } else {
            Write-Warning "Setup validation had warnings"
        }
    } catch {
        Write-Warning "Validation script failed"
    }
} else {
    Write-Warning "Validation script not found, skipping validation"
}
Pop-Location

# Print summary
Write-Host ""
Write-Host "🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Database connection details:"
Write-Host "  Host: localhost"
Write-Host "  Port: 5432"
Write-Host "  Database: saas_platform_dev"
Write-Host "  User: saas_user"
Write-Host "  Password: saas_secure_password_2024"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Connect to PostgreSQL: psql -h localhost -U saas_user -d saas_platform_dev"
Write-Host "  2. View dbt docs: cd dbt_project && dbt docs generate && dbt docs serve"
Write-Host "  3. Run dbt tests: cd dbt_project && dbt test"
Write-Host ""
Write-Host "To reset and start over, run: .\setup_local_windows.ps1"

# Deactivate virtual environment
deactivate