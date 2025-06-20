#!/usr/bin/env python3
"""Truncate user sessions table"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper

if __name__ == "__main__":
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("TRUNCATE TABLE raw.app_database_user_sessions CASCADE;")
        cursor.connection.commit()
        print("✓ Truncated app_database_user_sessions table")