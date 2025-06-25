#!/usr/bin/env python3
"""Check data issues"""

import psycopg2

# Database connection
conn = psycopg2.connect(
    host='localhost',
    database='saas_platform_dev',
    user='saas_user',
    password='saas_secure_password_2024',
    port=5432
)
cur = conn.cursor()

print("Checking account status...")
cur.execute("SELECT status, COUNT(*) FROM raw.app_database_accounts GROUP BY status")
for row in cur.fetchall():
    print(f"  Status '{row[0]}': {row[1]} accounts")

print("\nChecking subscription amounts...")
cur.execute("""
    SELECT 
        plan_name, 
        monthly_price, 
        COUNT(*) as count,
        SUM(monthly_price) as total
    FROM raw.app_database_subscriptions 
    WHERE status = 'active'
    GROUP BY plan_name, monthly_price
    ORDER BY monthly_price DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[2]} subs @ ${row[1]:,.2f} = ${row[3]:,.2f}")

print("\nChecking device status...")
cur.execute("SELECT status, COUNT(*) FROM raw.app_database_devices GROUP BY status ORDER BY COUNT(*) DESC")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} devices")

print("\nChecking user columns...")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'raw' AND table_name = 'app_database_users'")
cols = [row[0] for row in cur.fetchall()]
print(f"  Available columns: {', '.join(cols)}")

print("\nChecking sample account data...")
cur.execute("SELECT id, name, status, created_date FROM raw.app_database_accounts LIMIT 5")
for row in cur.fetchall():
    print(f"  ID: {row[0]}, Name: {row[1]}, Status: {row[2]}, Created: {row[3]}")

cur.close()
conn.close()