#!/usr/bin/env python3
"""
Check the structure of all campaign tables in the raw schema.
"""

from database_config import db_helper

def check_campaign_tables():
    """Check structure of all campaign tables"""
    
    campaign_tables = [
        'google_ads_campaigns',
        'facebook_ads_campaigns', 
        'linkedin_ads_campaigns',
        'iterable_campaigns'
    ]
    
    print("Checking campaign table structures...\n")
    
    for table in campaign_tables:
        print(f"\n{'='*60}")
        print(f"Table: raw.{table}")
        print('='*60)
        
        with db_helper.config.get_cursor() as cursor:
            # Get column information
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'raw' 
                  AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            
            if not columns:
                print(f"✗ Table not found: raw.{table}")
                continue
            
            print(f"\nColumns ({len(columns)} total):")
            print(f"{'Column Name':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
            print("-" * 80)
            
            for col in columns:
                col_name = col[0]
                data_type = col[1]
                if col[2]:  # character_maximum_length
                    data_type += f"({col[2]})"
                nullable = "YES" if col[3] == "YES" else "NO"
                default = col[4] if col[4] else ""
                
                print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default:<20}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM raw.{table}")
            row_count = cursor.fetchone()[0]
            print(f"\nRow count: {row_count:,}")
            
            # Get sample data if table has rows
            if row_count > 0:
                print("\nSample data (first row):")
                cursor.execute(f"SELECT * FROM raw.{table} LIMIT 1")
                sample = cursor.fetchone()
                for i, col in enumerate(columns):
                    print(f"  {col[0]}: {sample[i]}")

if __name__ == "__main__":
    check_campaign_tables()