#!/usr/bin/env python3
"""
Check existing Stripe prices in the database
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper

# Check existing prices
with db_helper.config.get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT * FROM raw.stripe_prices
        ORDER BY nickname, unit_amount
    """)
    prices = cursor.fetchall()
    
    print(f"Found {len(prices)} Stripe prices:")
    for price in prices:
        amount_display = f"${price['unit_amount'] / 100:,.2f}"
        interval = price['recurring_interval']
        print(f"  {price['nickname']}: {amount_display}/{interval} - {price['id']}")
