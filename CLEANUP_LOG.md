# Cleanup Log

## Summary
Removed old artifacts and unnecessary files to streamline the repository.

## Files Removed

### Backup Files (4 files)
- `dbt_project/profiles.yml.bak`
- `dbt_project/models/entity/schema/schema.yml.backup`
- `dbt_project/models/entity/entity_models.yml.backup`
- `dbt_project/dbt_project.yml.backup`

### Python Cache (8 directories)
- All `__pycache__` directories
- All `.pyc` files

### Test Files (5 files)
- `test_setup.log`
- `airflow/dags/test_basic.py`
- `airflow/dags/test_simple_pipeline.py`
- `ml/test_api.py`
- `superset/test_superset.sh`

### Old Log Files
- `logs/` directory with pipeline logs
- `airflow/dags/logs/` directory
- `dbt_project/logs/dbt.log.1`
- `dbt_project/logs/dbt.log.2`

### Old Configuration Files (8 files)
- `airflow/dags/saas_daily_etl_pipeline.py.complex`
- `airflow/dags/saas_platform_etl.py.simple`
- `airflow/airflow_minimal.cfg`
- `dbt_project/profiles_simple.yml`
- `dbt_project/profiles_minimal.yml`
- `scripts/validate_models_simple.py`
- `scripts/validate_data_simple.py`
- `superset/superset_simple_setup.sh`

### Empty Directories Removed
- `database/01_schema.sql` (was incorrectly a directory)
- `feast/`
- `data/test_validation/`
- `dbt_project/models/entity/schema/`

### Documentation Artifacts (3 files)
- `CLEANUP_SUMMARY.md`
- `dbt_project/tests/TEST_COVERAGE_SUMMARY.md`
- `dbt_project/tests/TEST_COVERAGE_REPORT.md`

### Old Schema Files (1 file)
- `database/00_complete_raw_schema.sql` (superseded by 01_main_schema.sql)

## Directories Preserved
These empty directories were kept as they may be needed by services:
- `airflow/logs/` - Airflow needs this
- `airflow/plugins/` - For custom Airflow plugins
- `grafana/provisioning/` - Grafana configuration
- `jupyter/` - Jupyter workspace

## Impact
- Repository is cleaner and more focused
- No test artifacts or temporary files
- Single source of truth for configurations
- Reduced confusion from multiple config options

Total files removed: ~35 files and 8 directories