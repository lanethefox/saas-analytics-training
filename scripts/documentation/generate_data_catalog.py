#!/usr/bin/env python3
"""
Generate comprehensive data catalog documentation from database schema.
This script introspects the PostgreSQL database and creates markdown documentation
for all tables, columns, relationships, and data quality metrics.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.database_config import db_helper

class DataCatalogGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            database='saas_platform_dev',
            user='saas_user',
            password='saas_secure_password_2024'
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.output_dir = Path('docs/data_catalog')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_all(self):
        """Generate complete data catalog documentation"""
        print("🚀 Starting Data Catalog Generation...")
        
        # Generate schema documentation
        self.generate_schema_docs('raw', 'Raw Layer - Source Data')
        self.generate_schema_docs('staging', 'Staging Layer - Cleaned Data')
        self.generate_schema_docs('intermediate', 'Intermediate Layer - Business Logic')
        self.generate_schema_docs('metrics', 'Metrics Layer - KPIs')
        
        # Generate ERD
        self.generate_erd()
        
        # Generate data quality report
        self.generate_data_quality_report()
        
        # Generate index page
        self.generate_index()
        
        print("✅ Data Catalog Generation Complete!")
        
    def generate_schema_docs(self, schema_name, schema_title):
        """Generate documentation for a specific schema"""
        print(f"📝 Documenting {schema_name} schema...")
        
        # Get all tables in schema
        self.cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema_name,))
        
        tables = self.cur.fetchall()
        if not tables:
            print(f"  No tables found in {schema_name} schema")
            return
            
        output_file = self.output_dir / f'{schema_name}_layer.md'
        
        with open(output_file, 'w') as f:
            f.write(f"# {schema_title}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Overview\n\n")
            f.write(f"This schema contains {len(tables)} tables.\n\n")
            
            # Table of contents
            f.write("## Tables\n\n")
            for table in tables:
                table_name = table['table_name']
                f.write(f"- [{table_name}](#{table_name.replace('_', '-')})\n")
            f.write("\n---\n\n")
            
            # Document each table
            for table in tables:
                table_name = table['table_name']
                self.document_table(f, schema_name, table_name)
                
    def document_table(self, file_handle, schema_name, table_name):
        """Document a single table"""
        f = file_handle
        
        # Table header
        f.write(f"## {table_name}\n\n")
        
        # Get row count and sample data
        self.cur.execute(f"SELECT COUNT(*) as count FROM {schema_name}.{table_name}")
        row_count = self.cur.fetchone()['count']
        f.write(f"**Row Count:** {row_count:,}\n\n")
        
        # Get table comment if exists
        self.cur.execute("""
            SELECT obj_description(c.oid) as comment
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relname = %s
        """, (schema_name, table_name))
        
        comment = self.cur.fetchone()
        if comment and comment['comment']:
            f.write(f"**Description:** {comment['comment']}\n\n")
        
        # Get columns
        self.cur.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                col_description(pgc.oid, cols.ordinal_position) as comment
            FROM information_schema.columns cols
            JOIN pg_class pgc ON pgc.relname = cols.table_name
            JOIN pg_namespace nsp ON nsp.oid = pgc.relnamespace 
                AND nsp.nspname = cols.table_schema
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, table_name))
        
        columns = self.cur.fetchall()
        
        # Column documentation
        f.write("### Columns\n\n")
        f.write("| Column | Type | Nullable | Default | Description |\n")
        f.write("|--------|------|----------|---------|-------------|\n")
        
        for col in columns:
            col_type = col['data_type']
            if col['character_maximum_length']:
                col_type += f"({col['character_maximum_length']})"
            
            nullable = "YES" if col['is_nullable'] == 'YES' else "NO"
            default = col['column_default'] or ''
            comment = col['comment'] or ''
            
            f.write(f"| {col['column_name']} | {col_type} | {nullable} | {default} | {comment} |\n")
        
        # Foreign keys
        self.cur.execute("""
            SELECT
                kcu.column_name,
                ccu.table_schema AS foreign_schema,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = %s
                AND tc.table_name = %s
        """, (schema_name, table_name))
        
        foreign_keys = self.cur.fetchall()
        
        if foreign_keys:
            f.write("\n### Foreign Keys\n\n")
            for fk in foreign_keys:
                f.write(f"- `{fk['column_name']}` → `{fk['foreign_schema']}.{fk['foreign_table']}.{fk['foreign_column']}`\n")
        
        # Indexes
        self.cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
            AND indexname NOT LIKE '%_pkey'
        """, (schema_name, table_name))
        
        indexes = self.cur.fetchall()
        
        if indexes:
            f.write("\n### Indexes\n\n")
            for idx in indexes:
                f.write(f"- `{idx['indexname']}`\n")
        
        # Sample queries
        f.write("\n### Sample Queries\n\n")
        f.write("```sql\n")
        f.write(f"-- Get all records\n")
        f.write(f"SELECT * FROM {schema_name}.{table_name} LIMIT 10;\n\n")
        
        # Add specific queries based on table
        if 'customer' in table_name or 'account' in table_name:
            f.write(f"-- Count by status\n")
            f.write(f"SELECT status, COUNT(*) \n")
            f.write(f"FROM {schema_name}.{table_name} \n")
            f.write(f"GROUP BY status;\n")
        
        f.write("```\n\n")
        
        # Data distribution
        if row_count > 0 and row_count < 1000000:  # Only for smaller tables
            self.add_data_distribution(f, schema_name, table_name)
        
        f.write("---\n\n")
        
    def add_data_distribution(self, f, schema_name, table_name):
        """Add data distribution statistics for key columns"""
        f.write("### Data Distribution\n\n")
        
        # Look for common column patterns
        common_columns = ['status', 'state', 'type', 'plan_name', 'device_type', 'role']
        
        for col_name in common_columns:
            self.cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = %s 
                AND table_name = %s 
                AND column_name = %s
            """, (schema_name, table_name, col_name))
            
            if self.cur.fetchone():
                self.cur.execute(f"""
                    SELECT {col_name}, COUNT(*) as count
                    FROM {schema_name}.{table_name}
                    WHERE {col_name} IS NOT NULL
                    GROUP BY {col_name}
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                distribution = self.cur.fetchall()
                if distribution:
                    f.write(f"**{col_name} distribution:**\n")
                    for row in distribution:
                        f.write(f"- {row[col_name]}: {row['count']:,}\n")
                    f.write("\n")
    
    def generate_erd(self):
        """Generate Entity Relationship Diagram"""
        print("📊 Generating ERD...")
        
        output_file = self.output_dir / 'entity_relationship_diagram.md'
        
        with open(output_file, 'w') as f:
            f.write("# Entity Relationship Diagram\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Create mermaid diagram
            f.write("```mermaid\nerDiagram\n")
            
            # Get all foreign key relationships
            self.cur.execute("""
                SELECT
                    tc.table_schema,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_schema AS foreign_schema,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema IN ('raw', 'staging')
                ORDER BY tc.table_schema, tc.table_name
            """)
            
            relationships = self.cur.fetchall()
            
            # Track entities
            entities = set()
            
            for rel in relationships:
                parent = f"{rel['foreign_schema']}__{rel['foreign_table']}"
                child = f"{rel['table_schema']}__{rel['table_name']}"
                entities.add(parent)
                entities.add(child)
                
                # Determine relationship type (simplified)
                if rel['column_name'].endswith('_id'):
                    f.write(f"    {parent} ||--o{{ {child} : has\n")
                else:
                    f.write(f"    {parent} ||--|| {child} : references\n")
            
            f.write("```\n\n")
            
            # Add relationship summary
            f.write("## Relationship Summary\n\n")
            f.write(f"- Total Entities: {len(entities)}\n")
            f.write(f"- Total Relationships: {len(relationships)}\n\n")
            
            # Group by schema
            f.write("### By Schema\n\n")
            for schema in ['raw', 'staging', 'intermediate', 'metrics']:
                schema_rels = [r for r in relationships if r['table_schema'] == schema]
                if schema_rels:
                    f.write(f"**{schema}**: {len(schema_rels)} relationships\n")
    
    def generate_data_quality_report(self):
        """Generate data quality metrics"""
        print("📈 Generating Data Quality Report...")
        
        output_file = self.output_dir / 'data_quality_report.md'
        
        with open(output_file, 'w') as f:
            f.write("# Data Quality Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall metrics
            f.write("## Overall Metrics\n\n")
            
            # Table counts by schema
            self.cur.execute("""
                SELECT table_schema, COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema IN ('raw', 'staging', 'intermediate', 'metrics')
                AND table_type = 'BASE TABLE'
                GROUP BY table_schema
                ORDER BY table_schema
            """)
            
            schema_counts = self.cur.fetchall()
            
            f.write("### Tables by Schema\n\n")
            for row in schema_counts:
                f.write(f"- **{row['table_schema']}**: {row['table_count']} tables\n")
            
            # Data volumes
            f.write("\n### Data Volumes\n\n")
            
            key_tables = [
                ('raw', 'app_database_accounts', 'Accounts'),
                ('raw', 'app_database_locations', 'Locations'),
                ('raw', 'app_database_devices', 'Devices'),
                ('raw', 'app_database_users', 'Users'),
                ('raw', 'app_database_subscriptions', 'Subscriptions')
            ]
            
            for schema, table, label in key_tables:
                self.cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table}")
                count = self.cur.fetchone()['count']
                f.write(f"- **{label}**: {count:,} records\n")
            
            # Referential integrity
            f.write("\n## Referential Integrity\n\n")
            
            integrity_checks = [
                ("Locations → Accounts", 
                 "SELECT COUNT(*) FROM raw.app_database_locations WHERE customer_id NOT IN (SELECT id FROM raw.app_database_accounts)"),
                ("Devices → Locations",
                 "SELECT COUNT(*) FROM raw.app_database_devices WHERE location_id NOT IN (SELECT id FROM raw.app_database_locations)"),
                ("Users → Accounts",
                 "SELECT COUNT(*) FROM raw.app_database_users WHERE customer_id NOT IN (SELECT id FROM raw.app_database_accounts)"),
            ]
            
            all_good = True
            for check_name, query in integrity_checks:
                self.cur.execute(query)
                violations = self.cur.fetchone()['count']
                status = "✅ PASS" if violations == 0 else f"❌ FAIL ({violations} violations)"
                f.write(f"- {check_name}: {status}\n")
                if violations > 0:
                    all_good = False
            
            f.write(f"\n**Overall Status**: {'✅ All relationships valid' if all_good else '❌ Some relationships need attention'}\n")
    
    def generate_index(self):
        """Generate index page for data catalog"""
        print("📚 Generating Index...")
        
        output_file = self.output_dir / 'index.md'
        
        with open(output_file, 'w') as f:
            f.write("# TapFlow Analytics Data Catalog\n\n")
            f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Overview\n\n")
            f.write("This data catalog provides comprehensive documentation of all tables, ")
            f.write("columns, relationships, and data quality metrics in the TapFlow Analytics platform.\n\n")
            
            f.write("## Quick Links\n\n")
            f.write("- [Raw Layer](raw_layer.md) - Source data from application\n")
            f.write("- [Staging Layer](staging_layer.md) - Cleaned and standardized data\n")
            f.write("- [Intermediate Layer](intermediate_layer.md) - Business logic applied\n")
            f.write("- [Metrics Layer](metrics_layer.md) - Key performance indicators\n")
            f.write("- [Entity Relationship Diagram](entity_relationship_diagram.md) - Visual data model\n")
            f.write("- [Data Quality Report](data_quality_report.md) - Current data health\n\n")
            
            f.write("## Key Statistics\n\n")
            
            # Get summary stats
            self.cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM information_schema.tables 
                     WHERE table_schema IN ('raw', 'staging', 'intermediate', 'metrics') 
                     AND table_type = 'BASE TABLE') as total_tables,
                    (SELECT COUNT(*) FROM information_schema.columns 
                     WHERE table_schema IN ('raw', 'staging', 'intermediate', 'metrics')) as total_columns,
                    (SELECT COUNT(*) FROM raw.app_database_accounts) as total_accounts,
                    (SELECT SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint 
                     FROM pg_tables 
                     WHERE schemaname IN ('raw', 'staging', 'intermediate', 'metrics')) as total_size
            """)
            
            stats = self.cur.fetchone()
            
            f.write(f"- **Total Tables**: {stats['total_tables']}\n")
            f.write(f"- **Total Columns**: {stats['total_columns']}\n")
            f.write(f"- **Active Accounts**: {stats['total_accounts']:,}\n")
            f.write(f"- **Database Size**: {stats['total_size'] / 1024 / 1024:.1f} MB\n\n")
            
            f.write("## Documentation Standards\n\n")
            f.write("This catalog is automatically generated from the database schema and is updated:\n")
            f.write("- On every schema change\n")
            f.write("- Daily at 2 AM UTC\n")
            f.write("- On-demand via `python scripts/documentation/generate_data_catalog.py`\n\n")
            
            f.write("For questions or corrections, please contact the Analytics Engineering team.\n")
    
    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    generator = DataCatalogGenerator()
    generator.generate_all()