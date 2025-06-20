#!/usr/bin/env python3
"""
Comprehensive dbt model validation with automatic fixes
"""

import subprocess
import psycopg2
import json
import time
import re
import os
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

class ModelValidator:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.results = []
        self.fixes_applied = []
        
    def get_models_by_layer(self, layer):
        """Get all models in a layer"""
        cmd = f'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt ls -s {layer} --resource-type model --output json --profiles-dir ."'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        models = []
        for line in result.stdout.strip().split('\n'):
            if '"ListCmdOut"' in line and '"msg"' in line:
                try:
                    data = json.loads(line)
                    model_path = data['data']['msg']
                    model_name = model_path.split('.')[-1]
                    models.append(model_name)
                except:
                    pass
        
        return models
    
    def get_row_count(self, schema, table):
        """Get row count for a table"""
        try:
            cur = self.conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
            count = cur.fetchone()[0]
            cur.close()
            return count
        except:
            return None
    
    def validate_raw_layer(self):
        """Validate all raw tables"""
        print("\n" + "="*100)
        print("RAW LAYER VALIDATION")
        print("="*100)
        
        cur = self.conn.cursor()
        cur.execute("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size('"raw".'||table_name)) as size
            FROM information_schema.tables 
            WHERE table_schema = 'raw' 
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        total_rows = 0
        
        print(f"{'Table':<40} {'Rows':<15} {'Size':<15} {'Status'}")
        print("-"*85)
        
        for table_name, size in tables:
            row_count = self.get_row_count('raw', table_name)
            status = "PASS" if row_count is not None else "FAIL"
            total_rows += row_count or 0
            
            print(f"raw.{table_name:<35} {row_count:<15,} {size:<15} {status}")
            
            self.results.append({
                'layer': 'raw',
                'model': table_name,
                'status': status,
                'rows': row_count or 0,
                'time': 0,
                'error': ''
            })
        
        cur.close()
        print(f"\nTotal: {len(tables)} tables, {total_rows:,} rows")
        
    def run_model(self, model_name, layer):
        """Run a single model and capture results"""
        start_time = time.time()
        
        cmd = f'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt run -s {model_name} --profiles-dir . 2>&1"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        exec_time = time.time() - start_time
        
        # Determine schema
        schema_map = {
            'staging': 'staging',
            'intermediate': 'intermediate', 
            'entity': 'entity',
            'mart': 'mart',
            'metrics': 'public'
        }
        schema = schema_map.get(layer, 'public')
        
        if "Completed successfully" in result.stdout:
            row_count = self.get_row_count(schema, model_name) or 0
            return {
                'status': 'PASS',
                'rows': row_count,
                'time': round(exec_time, 2),
                'error': ''
            }
        else:
            # Extract error
            error = self.extract_error(result.stdout)
            return {
                'status': 'FAIL',
                'rows': 0,
                'time': round(exec_time, 2),
                'error': error
            }
    
    def extract_error(self, output):
        """Extract meaningful error from dbt output"""
        # Look for column errors
        match = re.search(r'column "([^"]+)" does not exist', output)
        if match:
            return f"Missing column: {match.group(1)}"
        
        # Look for table errors
        match = re.search(r'relation "([^"]+)" does not exist', output)
        if match:
            return f"Missing table: {match.group(1)}"
        
        # Look for other errors
        for line in output.split('\n'):
            if 'ERROR' in line or 'Error' in line:
                return line.strip()[:100]
        
        return "Unknown error"
    
    def fix_column_error(self, model_path, missing_column):
        """Attempt to fix missing column error"""
        # Read model file
        with open(model_path, 'r') as f:
            content = f.read()
        
        # Common column name fixes
        fixes = {
            'collection_method': 'NULL as collection_method',
            'valid_from': 'created_at as valid_from',
            'valid_to': 'NULL::timestamp as valid_to',
        }
        
        if missing_column in fixes:
            # Add the column with a default value
            new_content = content.replace(
                'from', 
                f',\n        {fixes[missing_column]}\nfrom'
            )
            
            with open(model_path, 'w') as f:
                f.write(new_content)
            
            return True
        
        return False
    
    def validate_layer(self, layer):
        """Validate all models in a layer"""
        print(f"\n" + "="*100)
        print(f"{layer.upper()} LAYER VALIDATION")
        print("="*100)
        
        models = self.get_models_by_layer(layer)
        print(f"Found {len(models)} models\n")
        
        print(f"{'Model':<40} {'Status':<10} {'Rows':<15} {'Time(s)':<10} {'Error'}")
        print("-"*95)
        
        for model in models:
            result = self.run_model(model, layer)
            
            status_icon = "✓" if result['status'] == 'PASS' else "✗"
            print(f"{status_icon} {model:<38} {result['status']:<10} {result['rows']:<15,} {result['time']:<10} {result['error'][:40]}")
            
            self.results.append({
                'layer': layer,
                'model': model,
                'status': result['status'],
                'rows': result['rows'],
                'time': result['time'],
                'error': result['error']
            })
            
            # If failed due to missing column, try to fix
            if result['status'] == 'FAIL' and 'Missing column' in result['error']:
                missing_col = result['error'].split(': ')[1]
                model_path = f"dbt_project/models/{layer}/{model}.sql"
                
                # For now, just log the error
                self.fixes_applied.append({
                    'model': model,
                    'error': result['error'],
                    'fix': f"Need to add column: {missing_col}"
                })
        
        # Summary for layer
        passed = sum(1 for r in self.results if r['layer'] == layer and r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['layer'] == layer and r['status'] == 'FAIL')
        total_rows = sum(r['rows'] for r in self.results if r['layer'] == layer)
        
        print(f"\nLayer Summary: {passed} passed, {failed} failed, {total_rows:,} total rows")
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*100)
        print("FINAL VALIDATION REPORT")
        print("="*100)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Summary by layer
        layers = {}
        for r in self.results:
            layer = r['layer']
            if layer not in layers:
                layers[layer] = {'total': 0, 'passed': 0, 'failed': 0, 'rows': 0}
            
            layers[layer]['total'] += 1
            if r['status'] == 'PASS':
                layers[layer]['passed'] += 1
                layers[layer]['rows'] += r['rows']
            else:
                layers[layer]['failed'] += 1
        
        print("SUMMARY BY LAYER:")
        print(f"{'Layer':<15} {'Total':<10} {'Passed':<10} {'Failed':<10} {'Total Rows'}")
        print("-"*60)
        
        for layer, stats in layers.items():
            print(f"{layer:<15} {stats['total']:<10} {stats['passed']:<10} {stats['failed']:<10} {stats['rows']:,}")
        
        # Failed models
        failed = [r for r in self.results if r['status'] == 'FAIL']
        if failed:
            print("\n\nFAILED MODELS:")
            print("-"*80)
            for r in failed:
                print(f"{r['layer']}.{r['model']}: {r['error']}")
        
        # Save detailed results
        with open('validation_report.json', 'w') as f:
            json.dump({
                'summary': layers,
                'results': self.results,
                'fixes_needed': self.fixes_applied
            }, f, indent=2)
        
        print(f"\n\nDetailed report saved to: validation_report.json")
        print(f"Total models validated: {len(self.results)}")
        print(f"Total passed: {sum(1 for r in self.results if r['status'] == 'PASS')}")
        print(f"Total failed: {sum(1 for r in self.results if r['status'] == 'FAIL')}")

def main():
    validator = ModelValidator()
    
    try:
        # Validate raw layer
        validator.validate_raw_layer()
        
        # Validate each dbt layer
        layers = ['staging', 'intermediate', 'entity', 'mart', 'metrics']
        for layer in layers:
            validator.validate_layer(layer)
        
        # Generate report
        validator.generate_report()
        
    finally:
        validator.conn.close()

if __name__ == "__main__":
    main()