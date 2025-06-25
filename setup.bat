@echo off
REM B2B SaaS Analytics Platform - Windows Setup Script
REM This script sets up the platform with Docker on Windows

echo.
echo ====================================================
echo B2B SaaS Analytics Platform - Windows Setup
echo ====================================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed.
    echo Please install Docker Desktop and ensure it's running.
    echo https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Parse command line arguments
set "SKIP_DATA=false"
set "COMPOSE_FILE=docker-compose.yml"

:parse_args
if "%~1"=="" goto :done_parsing
if /i "%~1"=="--skip-data" (
    set "SKIP_DATA=true"
    shift
    goto :parse_args
)
if /i "%~1"=="--full" (
    set "COMPOSE_FILE=docker-compose.full.yml"
    shift
    goto :parse_args
)
if /i "%~1"=="--help" (
    goto :show_help
)
shift
goto :parse_args
:done_parsing

echo Starting setup with:
echo - Using deterministic data generation
echo - Skip data generation: %SKIP_DATA%
echo - Compose file: %COMPOSE_FILE%
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo Done.
)

REM Stop any existing containers
echo Stopping any existing containers...
docker-compose -f %COMPOSE_FILE% down >nul 2>&1

REM Start services
echo.
echo Starting Docker services...
docker-compose -f %COMPOSE_FILE% up -d

REM Wait for PostgreSQL to be ready
echo.
echo Waiting for PostgreSQL to be ready...
:wait_postgres
timeout /t 2 /nobreak >nul
docker-compose exec -T postgres pg_isready -U saas_user >nul 2>&1
if errorlevel 1 (
    echo PostgreSQL not ready yet, waiting...
    goto :wait_postgres
)
echo PostgreSQL is ready!

REM Generate data if not skipped
if "%SKIP_DATA%"=="false" (
    echo.
    echo Generating deterministic data...
    
    REM Check if Python is available
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH.
        echo Please install Python 3.8+ from https://www.python.org/downloads/
        echo Or use --skip-data flag to skip data generation.
        pause
        exit /b 1
    )
    
    REM Install Python dependencies
    echo Installing Python dependencies...
    pip install -r requirements.txt >nul 2>&1
    
    REM Run deterministic data generation
    python scripts/generate_all_deterministic.py
    if errorlevel 1 (
        echo ERROR: Data generation failed!
        pause
        exit /b 1
    )
) else (
    echo.
    echo Skipping data generation as requested.
)

REM Run dbt transformations
echo.
echo Running dbt transformations...
docker-compose exec -T dbt-core bash -c "cd /opt/dbt_project && dbt deps && dbt run"
if errorlevel 1 (
    echo WARNING: dbt transformations failed!
    echo You may need to run them manually later.
)

REM Validate deployment
echo.
echo Validating deployment...
docker-compose ps

REM Show access information
echo.
echo ====================================================
echo Platform is ready!
echo ====================================================
echo.
echo Access points:
echo - Superset (BI): http://localhost:8088 (admin/admin)
echo - Jupyter Lab: http://localhost:8888
echo - PostgreSQL: localhost:5432 (saas_user/saas_secure_password_2024)
echo - Redis: localhost:6379
echo.
echo To view Jupyter token:
echo   docker logs saas_platform_jupyter
echo.
echo To stop all services:
echo   docker-compose -f %COMPOSE_FILE% down
echo.
echo To remove all data and start fresh:
echo   docker-compose -f %COMPOSE_FILE% down -v
echo.
pause
exit /b 0

:show_help
echo.
echo Usage: setup.bat [options]
echo.
echo Options:
echo   --skip-data         Skip data generation step
echo   --full              Use full stack with all services
echo   --help              Show this help message
echo.
echo Examples:
echo   setup.bat                    # Core services + small dataset
echo   setup.bat --size large       # Core services + large dataset
echo   setup.bat --full             # All services + small dataset
echo   setup.bat --skip-data        # Core services, no data
echo.
pause
exit /b 0