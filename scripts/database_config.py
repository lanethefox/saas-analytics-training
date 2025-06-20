#!/usr/bin/env python3
"""
Database connection module for synthetic data generation.

This module handles:
- PostgreSQL connection setup
- Raw schema verification  
- Helper functions for bulk data insertion
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from environs import Env
from contextlib import contextmanager

# Initialize environment variable reader
env = Env()
env.read_env()

class DatabaseConfig:
    """Configuration for PostgreSQL database connection"""
    
    def __init__(self):
        # Load database credentials from environment
        self.db_name = env.str('POSTGRES_DB', default='saas_platform_dev')
        self.db_user = env.str('POSTGRES_USER', default='saas_user')
        self.db_password = env.str('POSTGRES_PASSWORD', default='saas_secure_password_2024')
        self.db_host = env.str('POSTGRES_HOST', default='localhost')  # Changed from 'postgres' for local dev
        self.db_port = env.int('POSTGRES_PORT', default=5432)
        
        # Build connection string
        self.connection_string = (
            f"postgresql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=False):
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()

db_config = DatabaseConfig()

class DatabaseHelper:
    """Helper functions for database operations"""
    
    def __init__(self, config=None):
        self.config = config or db_config
    
    def verify_raw_schema_exists(self):
        """Verify that the raw schema exists in the database"""
        with self.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'raw'
            """)
            result = cursor.fetchone()
            return result is not None
    
    def create_raw_schema_if_not_exists(self):
        """Create raw schema if it doesn't exist"""
        with self.config.get_cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS raw")
            print("✓ Raw schema created/verified")
    
    def get_table_list(self, schema='raw'):
        """Get list of tables in a schema"""
        with self.config.get_cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """, (schema,))
            return [row[0] for row in cursor.fetchall()]
    
    def bulk_insert(self, table_name, data, schema='raw', page_size=1000):
        """Bulk insert data into a table using COPY for performance"""
        if not data:
            return 0
        
        full_table_name = f"{schema}.{table_name}"
        columns = list(data[0].keys())
        
        inserted = 0
        with self.config.get_cursor() as cursor:
            # Process in batches
            for i in range(0, len(data), page_size):
                batch = data[i:i + page_size]
                
                # Prepare values
                values = []
                for row in batch:
                    values.append(tuple(row.get(col) for col in columns))
                
                # Generate INSERT statement
                placeholders = ','.join(['%s'] * len(columns))
                insert_query = f"""
                    INSERT INTO {full_table_name} ({','.join(columns)})
                    VALUES ({placeholders})
                """
                
                # Execute batch insert
                execute_batch(cursor, insert_query, values)
                inserted += len(batch)
                
                if inserted % 10000 == 0:
                    print(f"  Inserted {inserted:,} records into {full_table_name}")
        
        print(f"✓ Total inserted: {inserted:,} records into {full_table_name}")
        return inserted
    
    def truncate_table(self, table_name, schema='raw'):
        """Truncate a table (remove all data)"""
        with self.config.get_cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {schema}.{table_name} CASCADE")
            print(f"✓ Truncated {schema}.{table_name}")
    
    def get_row_count(self, table_name, schema='raw'):
        """Get the number of rows in a table"""
        with self.config.get_cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            return cursor.fetchone()[0]
    
    def test_connection(self):
        """Test the database connection"""
        try:
            with self.config.get_cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"✓ Connected to PostgreSQL")
                print(f"  Version: {version}")
                print(f"  Database: {self.config.db_name}")
                print(f"  Host: {self.config.db_host}:{self.config.db_port}")
                return True
        except Exception as e:
            print(f"✗ Failed to connect to PostgreSQL: {e}")
            return False

# Create singleton instance
db_helper = DatabaseHelper()

if __name__ == "__main__":
    # Test the database connection when run directly
    print("Testing database connection...")
    db_helper.test_connection()
    
    if db_helper.verify_raw_schema_exists():
        print("✓ Raw schema exists")
        tables = db_helper.get_table_list()
        print(f"✓ Found {len(tables)} tables in raw schema")
        if tables:
            print("  Tables:", ", ".join(tables[:5]), "..." if len(tables) > 5 else "")
    else:
        print("✗ Raw schema does not exist")
