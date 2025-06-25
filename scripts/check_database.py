#!/usr/bin/env python3
"""
Check database connectivity for the SaaS data platform.
"""

import sys
from database_config import db_helper

def main():
    """Check database connection."""
    print("Checking database connection...")
    
    if db_helper.test_connection():
        print("\n✅ Database connection successful!")
        return 0
    else:
        print("\n❌ Database connection failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())