#!/usr/bin/env python3
"""Test revenue daily metrics query."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_config import DatabaseConfig

def main():
    db_config = DatabaseConfig()
    
    with db_config.get_connection() as conn:
        with conn.cursor() as cursor:
            # Test the basic daily metrics query
            cursor.execute("""
                SELECT 
                    snapshot_date as metric_date,
                    COUNT(DISTINCT account_id) as total_customers,
                    COUNT(DISTINCT CASE WHEN customer_status = 'active' THEN account_id END) as active_customers,
                    SUM(CASE WHEN customer_status = 'active' THEN monthly_recurring_revenue ELSE 0 END) as total_mrr
                FROM intermediate.fct_customer_history
                WHERE snapshot_date >= CURRENT_DATE - interval '7 days'
                GROUP BY 1
                ORDER BY 1 DESC
            """)
            
            print('Daily revenue metrics (last 7 days):')
            print('-' * 80)
            print(f'{"Date":<12} {"Total":<10} {"Active":<10} {"MRR":<15}')
            print('-' * 80)
            for row in cursor.fetchall():
                mrr_str = f'${row[3]:,.0f}' if row[3] else '$0'
                print(f'{str(row[0]):<12} {row[1]:<10} {row[2]:<10} {mrr_str:<15}')

if __name__ == "__main__":
    main()