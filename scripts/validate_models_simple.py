#!/usr/bin/env python3
"""
Simple model validation - validate raw sources and staging models
"""

import subprocess
import psycopg2
import json
import time

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def validate_raw_tables():
    """Check all raw tables"""
    print("="*80)
    print("RAW LAYER VALIDATION")
    print("="*80)
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get all tables in raw schema
    cur.execute("""
        SELECT table_name, 
               pg_size_pretty(pg_total_relation_size('"raw".'||table_name)) as size
        FROM information_schema.tables 
        WHERE table_schema = 'raw' 
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    
    results = []
    for table_name, size in tables:
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM raw.{table_name}")
        row_count = cur.fetchone()[0]
        
        print(f"✓ raw.{table_name}: {row_count:,} rows ({size})")
        results.append({
            'schema': 'raw',
            'table': table_name,
            'rows': row_count,
            'size': size
        })
    
    cur.close()
    conn.close()
    
    print(f"\nTotal raw tables: {len(tables)}")
    print(f"Total raw rows: {sum(r['rows'] for r in results):,}")
    
    return results

def get_staging_models():
    """Get list of staging models from dbt"""
    cmd = 'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt ls -s path:models/staging --resource-type model --profiles-dir . 2>/dev/null | grep -v \'{\'\"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    models = []
    for line in result.stdout.strip().split('\n'):
        if line and '.' in line:
            # Extract model name from full path
            model_name = line.split('.')[-1]
            models.append(model_name)
    
    return models

def run_staging_model(model_name):
    """Run a single staging model"""
    print(f"\nRunning staging.{model_name}...")
    
    start_time = time.time()
    cmd = f'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt run -s {model_name} --profiles-dir . 2>&1"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    exec_time = time.time() - start_time
    
    # Check if successful
    if "Completed successfully" in result.stdout:
        # Get row count
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT COUNT(*) FROM staging.{model_name}")
            row_count = cur.fetchone()[0]
            status = "PASS"
            error = ""
        except Exception as e:
            row_count = 0
            status = "ERROR"
            error = str(e)
        cur.close()
        conn.close()
        
        print(f"  ✓ Success: {row_count:,} rows in {exec_time:.2f}s")
    else:
        status = "FAIL"
        row_count = 0
        # Extract error
        error = "Unknown error"
        for line in result.stdout.split('\n'):
            if "error" in line.lower() and "column" in line:
                error = line.strip()
                break
        print(f"  ✗ Failed: {error}")
    
    return {
        'model': model_name,
        'status': status,
        'rows': row_count,
        'time': round(exec_time, 2),
        'error': error
    }

def main():
    # Validate raw tables
    raw_results = validate_raw_tables()
    
    # Get staging models
    print("\n" + "="*80)
    print("STAGING LAYER VALIDATION")
    print("="*80)
    
    staging_models = get_staging_models()
    print(f"Found {len(staging_models)} staging models")
    
    staging_results = []
    failed_models = []
    
    for model in staging_models[:10]:  # Test first 10 models
        result = run_staging_model(model)
        staging_results.append(result)
        if result['status'] != 'PASS':
            failed_models.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    print(f"\nRaw tables: {len(raw_results)} tables, {sum(r['rows'] for r in raw_results):,} total rows")
    print(f"Staging models tested: {len(staging_results)}")
    print(f"  - Passed: {sum(1 for r in staging_results if r['status'] == 'PASS')}")
    print(f"  - Failed: {len(failed_models)}")
    
    if failed_models:
        print("\nFailed models:")
        for model in failed_models:
            print(f"  - {model['model']}: {model['error']}")
    
    # Save results
    with open('validation_results.json', 'w') as f:
        json.dump({
            'raw': raw_results,
            'staging': staging_results,
            'summary': {
                'raw_tables': len(raw_results),
                'raw_rows': sum(r['rows'] for r in raw_results),
                'staging_tested': len(staging_results),
                'staging_passed': sum(1 for r in staging_results if r['status'] == 'PASS'),
                'staging_failed': len(failed_models)
            }
        }, f, indent=2)
    
    print("\nResults saved to validation_results.json")

if __name__ == "__main__":
    main()