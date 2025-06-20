#!/usr/bin/env python3
"""
Create backup of all generated data.

This script:
- Exports all database tables to CSV files
- Creates a compressed archive of all data files
- Includes all JSON mapping files
- Generates a backup manifest
"""

import json
import csv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import tarfile
import shutil
from scripts.database_config import db_helper

# Tables to backup
TABLES_TO_BACKUP = [
    # Core entities
    'app_database_accounts',
    'app_database_locations',
    'app_database_users',
    'app_database_devices',
    'app_database_subscriptions',
    
    # Stripe billing
    'stripe_customers',
    'stripe_prices',
    'stripe_subscriptions',
    'stripe_subscription_items',
    'stripe_invoices',
    'stripe_charges',
    'stripe_events',
    
    # HubSpot CRM
    'hubspot_companies',
    'hubspot_contacts',
    'hubspot_deals',
    'hubspot_engagements',
    'hubspot_tickets',
    
    # Marketing
    'google_ads_campaigns',
    'facebook_ads_campaigns',
    'linkedin_ads_campaigns',
    'iterable_campaigns',
    'attribution_touchpoints',
    'marketing_qualified_leads',
    'google_analytics_sessions',
    
    # App activity
    'app_database_user_sessions',
    'app_database_page_views',
    'app_database_feature_usage',
    'app_database_tap_events'
]

def export_table_to_csv(table_name, output_dir):
    """Export a database table to CSV file."""
    csv_file = os.path.join(output_dir, f"{table_name}.csv")
    
    with db_helper.config.get_cursor() as cursor:
        # Get column names
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # Export data
        cursor.execute(f"SELECT * FROM raw.{table_name} ORDER BY {columns[0]}")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)  # Header
            
            row_count = 0
            for row in cursor:
                # Convert any JSON/JSONB fields to strings
                processed_row = []
                for i, value in enumerate(row):
                    if isinstance(value, (dict, list)):
                        processed_row.append(json.dumps(value))
                    else:
                        processed_row.append(value)
                writer.writerow(processed_row)
                row_count += 1
        
        return row_count

def create_backup_manifest(backup_dir, table_stats, json_files):
    """Create a manifest file with backup metadata."""
    manifest = {
        'backup_date': datetime.now().isoformat(),
        'database': 'saas_platform_dev',
        'schema': 'raw',
        'tables_backed_up': len(table_stats),
        'total_records': sum(table_stats.values()),
        'table_statistics': table_stats,
        'json_mapping_files': json_files,
        'backup_format': 'CSV + JSON',
        'compression': 'tar.gz'
    }
    
    manifest_file = os.path.join(backup_dir, 'backup_manifest.json')
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def main():
    print("=== Creating Data Backup ===")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Create backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'data_backup_{timestamp}'
    csv_dir = os.path.join(backup_dir, 'csv_exports')
    json_dir = os.path.join(backup_dir, 'json_mappings')
    
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    
    print(f"\nCreating backup in: {backup_dir}")
    
    # Export database tables
    print("\nExporting database tables to CSV...")
    table_stats = {}
    
    for table in TABLES_TO_BACKUP:
        try:
            print(f"  Exporting {table}...", end=' ')
            row_count = export_table_to_csv(table, csv_dir)
            table_stats[table] = row_count
            print(f"✓ {row_count:,} records")
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            table_stats[table] = 0
    
    # Copy JSON mapping files
    print("\nCopying JSON mapping files...")
    json_files = []
    data_dir = 'data'
    
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                src = os.path.join(data_dir, filename)
                dst = os.path.join(json_dir, filename)
                shutil.copy2(src, dst)
                json_files.append(filename)
                print(f"  ✓ {filename}")
    
    # Copy important documentation
    print("\nCopying documentation...")
    docs_to_copy = [
        'DATAGEN_TODO.md',
        'DATAGEN_PROGRESS.md',
        'FINAL_DATA_SUMMARY_REPORT.md',
        'CLAUDE.md'
    ]
    
    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy2(doc, backup_dir)
            print(f"  ✓ {doc}")
    
    # Create manifest
    print("\nCreating backup manifest...")
    manifest = create_backup_manifest(backup_dir, table_stats, json_files)
    
    # Create compressed archive
    archive_name = f'{backup_dir}.tar.gz'
    print(f"\nCreating compressed archive: {archive_name}")
    
    with tarfile.open(archive_name, 'w:gz') as tar:
        tar.add(backup_dir, arcname=os.path.basename(backup_dir))
    
    # Calculate sizes
    backup_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                     for dirpath, dirnames, filenames in os.walk(backup_dir)
                     for filename in filenames)
    
    archive_size = os.path.getsize(archive_name)
    compression_ratio = (1 - archive_size / backup_size) * 100
    
    # Summary
    print("\n" + "="*60)
    print("BACKUP SUMMARY")
    print("="*60)
    print(f"Total Tables Backed Up: {len([v for v in table_stats.values() if v > 0])}")
    print(f"Total Records Exported: {sum(table_stats.values()):,}")
    print(f"JSON Mapping Files: {len(json_files)}")
    print(f"Documentation Files: {len([d for d in docs_to_copy if os.path.exists(d)])}")
    print(f"Uncompressed Size: {backup_size / 1024 / 1024:.1f} MB")
    print(f"Archive Size: {archive_size / 1024 / 1024:.1f} MB")
    print(f"Compression Ratio: {compression_ratio:.1f}%")
    print(f"\n✓ Backup completed: {archive_name}")
    
    # Cleanup temporary directory
    print("\nCleaning up temporary files...")
    shutil.rmtree(backup_dir)
    
    print("\n✓ Task 40 complete!")

if __name__ == "__main__":
    main()