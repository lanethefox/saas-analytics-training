#!/usr/bin/env python3
"""Check the summary views to ensure they provide aggregated KPIs."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_config import DatabaseConfig

def execute_query(sql):
    """Execute a query and return results."""
    db_config = DatabaseConfig()
    with db_config.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

def main():
    print("Checking summary views...\n")
    
    # Check revenue summary
    print("=== METRICS_REVENUE_SUMMARY ===")
    result = execute_query("SELECT COUNT(*) as row_count FROM metrics.metrics_revenue_summary")
    print(f"Row count: {result[0][0]}")
    
    if result[0][0] == 1:
        print("✓ Correctly showing single-row aggregated KPIs")
        
        # Show sample data
        result = execute_query("""
            SELECT 
                metric_date,
                total_customers,
                active_customers,
                total_mrr,
                avg_mrr,
                median_mrr,
                avg_health_score
            FROM metrics.metrics_revenue_summary
        """)
        
        row = result[0]
        print(f"\nSample KPIs:")
        print(f"  Metric Date: {row[0]}")
        print(f"  Total Customers: {row[1]:,}")
        print(f"  Active Customers: {row[2]:,}")
        print(f"  Total MRR: ${row[3]:,.0f}")
        print(f"  Average MRR: ${row[4]:,.2f}")
        print(f"  Median MRR: ${row[5]:,.2f}")
        print(f"  Avg Health Score: {row[6]:.1f}")
    else:
        print(f"✗ Expected 1 row but found {result[0][0]}")
    
    print("\n=== METRICS_OPERATIONS_SUMMARY ===")
    result = execute_query("SELECT COUNT(*) as row_count FROM metrics.metrics_operations_summary")
    print(f"Row count: {result[0][0]}")
    
    if result[0][0] == 1:
        print("✓ Correctly showing single-row aggregated KPIs")
        
        # Show sample data
        result = execute_query("""
            SELECT 
                metric_date,
                total_devices,
                online_devices,
                total_locations,
                active_locations,
                total_users,
                active_users
            FROM metrics.metrics_operations_summary
        """)
        
        row = result[0]
        print(f"\nSample KPIs:")
        print(f"  Metric Date: {row[0]}")
        print(f"  Total Devices: {row[1]:,}")
        print(f"  Online Devices: {row[2]:,}")
        print(f"  Total Locations: {row[3]:,}")
        print(f"  Active Locations: {row[4]:,}")
        print(f"  Total Users: {row[5]:,}")
        print(f"  Active Users: {row[6]:,}")
    else:
        print(f"✗ Expected 1 row but found {result[0][0]}")
    
    # Check the original metrics_revenue view for comparison
    print("\n=== METRICS_REVENUE (Original) ===")
    result = execute_query("SELECT COUNT(*) as row_count FROM metrics.metrics_revenue")
    print(f"Row count: {result[0][0]:,}")
    print("This is the customer-level detail view with one row per customer")
    
    # Check distinct dates
    result = execute_query("SELECT COUNT(DISTINCT metric_date) FROM metrics.metrics_revenue")
    print(f"Distinct metric dates: {result[0][0]}")
    
    result = execute_query("SELECT DISTINCT metric_date FROM metrics.metrics_revenue LIMIT 5")
    print("Sample dates:", [row[0] for row in result])

if __name__ == "__main__":
    main()