#!/usr/bin/env python3
"""Collect row counts for all DBT models across schemas."""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_config import DatabaseConfig

def get_tables_in_schema(cursor, schema_name):
    """Get all tables and views in a schema."""
    cursor.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = %s
        AND table_type IN ('BASE TABLE', 'VIEW')
        ORDER BY table_name
    """, (schema_name,))
    return cursor.fetchall()

def get_row_count(cursor, schema_name, table_name):
    """Get row count for a table."""
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {schema_name}.{table_name}')
        return cursor.fetchone()[0]
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    db_config = DatabaseConfig()
    
    # Schemas to check
    schemas = ['public', 'staging', 'intermediate', 'metrics']
    
    results = {}
    
    with db_config.get_connection() as conn:
        with conn.cursor() as cursor:
            for schema in schemas:
                print(f"\nChecking schema: {schema}")
                tables = get_tables_in_schema(cursor, schema)
                
                schema_results = []
                for table_name, table_type in tables:
                    count = get_row_count(cursor, schema, table_name)
                    schema_results.append({
                        'name': table_name,
                        'type': table_type,
                        'count': count
                    })
                    print(f"  {table_name} ({table_type}): {count:,}" if isinstance(count, int) else f"  {table_name}: {count}")
                
                results[schema] = schema_results
    
    # Generate markdown report
    markdown = f"""# Data Platform Row Counts Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary by Schema

"""
    
    for schema in schemas:
        if schema in results and results[schema]:
            total_tables = len(results[schema])
            tables_with_data = sum(1 for t in results[schema] if isinstance(t['count'], int) and t['count'] > 0)
            
            markdown += f"### {schema.upper()} Schema\n"
            markdown += f"- Total objects: {total_tables}\n"
            markdown += f"- Objects with data: {tables_with_data}\n\n"
    
    markdown += "\n## Detailed Row Counts\n\n"
    
    for schema in schemas:
        if schema in results and results[schema]:
            markdown += f"### {schema.upper()} Schema\n\n"
            markdown += "| Table/View | Type | Row Count |\n"
            markdown += "|------------|------|----------:|\n"
            
            for table in sorted(results[schema], key=lambda x: x['name']):
                count_str = f"{table['count']:,}" if isinstance(table['count'], int) else table['count']
                table_type = "Table" if table['type'] == 'BASE TABLE' else "View"
                markdown += f"| {table['name']} | {table_type} | {count_str} |\n"
            
            markdown += "\n"
    
    # Add metrics insights
    if 'metrics' in results and results['metrics']:
        markdown += "## Metrics Schema Insights\n\n"
        
        summary_views = [t for t in results['metrics'] if 'summary' in t['name']]
        historical_views = [t for t in results['metrics'] if 'historical' in t['name']]
        
        if summary_views:
            markdown += "### Summary Views (Aggregated KPIs)\n"
            for view in summary_views:
                count_str = f"{view['count']:,}" if isinstance(view['count'], int) else view['count']
                markdown += f"- **{view['name']}**: {count_str} rows"
                if isinstance(view['count'], int) and view['count'] == 1:
                    markdown += " ✓ (Single-row KPI summary)"
                markdown += "\n"
            markdown += "\n"
        
        if historical_views:
            markdown += "### Historical Views (Time Series)\n"
            for view in historical_views:
                count_str = f"{view['count']:,}" if isinstance(view['count'], int) else view['count']
                markdown += f"- **{view['name']}**: {count_str} rows\n"
            markdown += "\n"
    
    # Save to file
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'project_status_rows.md')
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print(f"\n✅ Report saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    main()