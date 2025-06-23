#!/usr/bin/env python3
"""
Get row counts for all tables in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper

def get_all_tables():
    """Get list of all tables in the database"""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                table_schema,
                table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)
        return cursor.fetchall()

def get_row_count(schema, table):
    """Get exact row count for a table"""
    try:
        with db_helper.config.get_cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
            return cursor.fetchone()[0]
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("Getting row counts for all tables...")
    print("=" * 80)
    
    tables = get_all_tables()
    results = []
    
    for schema, table in tables:
        count = get_row_count(schema, table)
        results.append((schema, table, count))
        print(f"{schema}.{table}: {count:,}" if isinstance(count, int) else f"{schema}.{table}: {count}")
    
    print("=" * 80)
    print(f"Total tables: {len(results)}")
    
    # Group by schema
    print("\n\nBy Schema:")
    print("=" * 80)
    current_schema = None
    for schema, table, count in results:
        if schema != current_schema:
            print(f"\n{schema}:")
            current_schema = schema
        print(f"  {table}: {count:,}" if isinstance(count, int) else f"  {table}: {count}")

if __name__ == "__main__":
    main()