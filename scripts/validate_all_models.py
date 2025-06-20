#!/usr/bin/env python3
"""
Comprehensive dbt Model Validation Script
Validates all models layer by layer, fixes issues, and generates a report
"""

import subprocess
import json
import psycopg2
import re
import time
from datetime import datetime
import sys
import os

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saas_platform_dev',
    'user': 'saas_user',
    'password': 'saas_secure_password_2024'
}

class ModelValidator:
    def __init__(self):
        self.results = []
        self.conn = None
        self.fixes_applied = []
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def get_row_count(self, schema, table):
        """Get row count for a table"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                return cur.fetchone()[0]
        except Exception as e:
            return f"Error: {str(e)}"
    
    def check_table_exists(self, schema, table):
        """Check if table exists"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    )
                """, (schema, table))
                return cur.fetchone()[0]
        except Exception as e:
            return False
    
    def run_dbt_command(self, command):
        """Run dbt command in docker"""
        full_command = f'docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && {command}"'
        try:
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def get_models_in_layer(self, layer):
        """Get list of models in a specific layer"""
        code, stdout, stderr = self.run_dbt_command(f"dbt list --select path:models/{layer} --resource-type model --profiles-dir .")
        models = []
        for line in stdout.strip().split('\n'):
            try:
                # Parse JSON output
                if line.strip().startswith('{'):
                    data = json.loads(line)
                    if data.get('info', {}).get('name') == 'ListCmdOut':
                        model_path = data.get('data', {}).get('msg', '')
                        if model_path:
                            # Extract just the model name
                            parts = model_path.split('.')
                            if len(parts) > 0:
                                models.append(parts[-1])
            except:
                pass
        return models
    
    def validate_raw_sources(self):
        """Validate all raw source tables"""
        print("\n" + "="*80)
        print("VALIDATING RAW LAYER SOURCES")
        print("="*80)
        
        # Define all source tables
        sources = {
            'app_database': [
                'accounts', 'locations', 'users', 'devices', 'subscriptions',
                'user_sessions', 'page_views', 'feature_usage', 'tap_events'
            ],
            'stripe': [
                'stripe_customers', 'stripe_prices', 'stripe_subscriptions', 'stripe_subscription_items',
                'stripe_invoices', 'stripe_charges', 'stripe_events', 'stripe_payment_intents'
            ],
            'hubspot': [
                'hubspot_companies', 'hubspot_contacts', 'hubspot_deals', 
                'hubspot_engagements', 'hubspot_tickets', 'hubspot_owners'
            ],
            'marketing': [
                'google_ads_campaigns', 'facebook_ads_campaigns', 'linkedin_ads_campaigns',
                'iterable_campaigns', 'attribution_touchpoints', 'marketing_qualified_leads',
                'google_analytics_sessions'
            ]
        }
        
        for source_name, tables in sources.items():
            print(f"\nValidating {source_name} sources:")
            for table in tables:
                if source_name == 'app_database':
                    full_table = f"app_database_{table}"
                else:
                    full_table = table
                exists = self.check_table_exists('raw', full_table)
                
                if exists:
                    row_count = self.get_row_count('raw', full_table)
                    status = "PASS"
                    print(f"  ✓ {full_table}: {row_count:,} rows")
                else:
                    row_count = 0
                    status = "MISSING"
                    print(f"  ✗ {full_table}: TABLE NOT FOUND")
                
                self.results.append({
                    'layer': 'raw',
                    'model': full_table,
                    'status': status,
                    'row_count': row_count,
                    'execution_time': 0,
                    'notes': ''
                })
    
    def run_single_model(self, model_name, layer):
        """Run a single dbt model and return results"""
        print(f"\nRunning {layer}.{model_name}...")
        start_time = time.time()
        
        code, stdout, stderr = self.run_dbt_command(f"dbt run --select {model_name} --profiles-dir .")
        execution_time = time.time() - start_time
        
        # Parse results from dbt output
        if code == 0 and "Completed successfully" in stdout:
            status = "PASS"
            # Extract schema and table name
            schema = self.get_model_schema(layer)
            row_count = self.get_row_count(schema, model_name)
            notes = ""
            print(f"  ✓ Success: {row_count:,} rows in {execution_time:.2f}s")
        else:
            status = "FAIL"
            row_count = 0
            error_msg = self.extract_error_message(stdout + stderr)
            notes = f"Error: {error_msg}"
            print(f"  ✗ Failed: {error_msg}")
        
        return {
            'layer': layer,
            'model': model_name,
            'status': status,
            'row_count': row_count,
            'execution_time': round(execution_time, 2),
            'notes': notes
        }
    
    def get_model_schema(self, layer):
        """Get schema name for a layer"""
        schema_map = {
            'staging': 'staging',
            'intermediate': 'intermediate',
            'entity': 'entity',
            'mart': 'mart',
            'metrics': 'public'  # metrics models go to public by default
        }
        return schema_map.get(layer, 'public')
    
    def extract_error_message(self, output):
        """Extract error message from dbt output"""
        # Look for common error patterns
        if "column" in output and "does not exist" in output:
            match = re.search(r'column "([^"]+)" does not exist', output)
            if match:
                return f"Missing column: {match.group(1)}"
        
        if "relation" in output and "does not exist" in output:
            match = re.search(r'relation "([^"]+)" does not exist', output)
            if match:
                return f"Missing table: {match.group(1)}"
        
        # Return first line with ERROR or error
        for line in output.split('\n'):
            if 'error' in line.lower():
                return line.strip()[:100]  # Limit length
        
        return "Unknown error"
    
    def validate_layer(self, layer):
        """Validate all models in a layer"""
        print(f"\n" + "="*80)
        print(f"VALIDATING {layer.upper()} LAYER")
        print("="*80)
        
        models = self.get_models_in_layer(layer)
        print(f"Found {len(models)} models in {layer} layer")
        
        for model in models:
            result = self.run_single_model(model, layer)
            self.results.append(result)
            
            # If model failed, attempt to fix common issues
            if result['status'] == 'FAIL':
                fixed = self.attempt_fix(model, layer, result['notes'])
                if fixed:
                    print(f"  🔧 Attempting fix for {model}...")
                    # Re-run after fix
                    result = self.run_single_model(model, layer)
                    result['notes'] = f"Fixed: {fixed}. {result['notes']}"
                    self.results[-1] = result  # Update last result
    
    def attempt_fix(self, model_name, layer, error_notes):
        """Attempt to fix common model issues"""
        # This is a placeholder - would need actual fix logic
        # based on specific error patterns
        return None
    
    def generate_report(self):
        """Generate final validation report"""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY REPORT")
        print("="*80)
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n")
        
        # Summary by layer
        layers = {}
        for result in self.results:
            layer = result['layer']
            if layer not in layers:
                layers[layer] = {'total': 0, 'passed': 0, 'failed': 0, 'total_rows': 0}
            
            layers[layer]['total'] += 1
            if result['status'] == 'PASS':
                layers[layer]['passed'] += 1
                if isinstance(result['row_count'], int):
                    layers[layer]['total_rows'] += result['row_count']
            else:
                layers[layer]['failed'] += 1
        
        print("SUMMARY BY LAYER:")
        print("-" * 60)
        print(f"{'Layer':<15} {'Total':<10} {'Passed':<10} {'Failed':<10} {'Total Rows':<15}")
        print("-" * 60)
        for layer, stats in layers.items():
            print(f"{layer:<15} {stats['total']:<10} {stats['passed']:<10} {stats['failed']:<10} {stats['total_rows']:<15,}")
        
        # Detailed results
        print("\n\nDETAILED RESULTS:")
        print("-" * 120)
        print(f"{'Layer':<12} {'Model':<40} {'Status':<10} {'Rows':<15} {'Time (s)':<10} {'Notes':<30}")
        print("-" * 120)
        
        for result in self.results:
            row_count_str = f"{result['row_count']:,}" if isinstance(result['row_count'], int) else str(result['row_count'])
            notes = result['notes'][:30] + '...' if len(result['notes']) > 30 else result['notes']
            
            print(f"{result['layer']:<12} {result['model']:<40} {result['status']:<10} {row_count_str:<15} {result['execution_time']:<10} {notes:<30}")
        
        # Failed models
        failed_models = [r for r in self.results if r['status'] == 'FAIL']
        if failed_models:
            print("\n\nFAILED MODELS REQUIRING ATTENTION:")
            print("-" * 80)
            for result in failed_models:
                print(f"\n{result['layer']}.{result['model']}:")
                print(f"  Error: {result['notes']}")
        
        # Save to file
        with open('model_validation_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print("\n\nFull results saved to: model_validation_report.json")

def main():
    validator = ModelValidator()
    
    # Connect to database
    if not validator.connect_db():
        print("Failed to connect to database")
        return
    
    try:
        # Validate each layer in order
        validator.validate_raw_sources()
        
        layers = ['staging', 'intermediate', 'entity', 'mart', 'metrics']
        for layer in layers:
            validator.validate_layer(layer)
        
        # Generate final report
        validator.generate_report()
        
    finally:
        if validator.conn:
            validator.conn.close()

if __name__ == "__main__":
    main()