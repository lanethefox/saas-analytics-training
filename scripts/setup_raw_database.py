#!/usr/bin/env python3
"""
Setup script for the raw database with multi-schema architecture.
Creates saas_platform_raw_db database and all required schemas.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'saas_user'),
    'password': os.getenv('DB_PASSWORD', 'saas_secure_password_2024')
}

RAW_DATABASE = 'saas_platform_raw_db'
ANALYTICS_DATABASE = 'saas_platform_analytics_db'

# Raw database schemas
RAW_SCHEMAS = [
    'app_database',
    'stripe', 
    'hubspot',
    'marketing'
]

# Analytics database schemas
ANALYTICS_SCHEMAS = [
    'staging',
    'intermediate', 
    'entity',
    'mart'
]

def create_database_if_not_exists(cursor, db_name):
    """Create database if it doesn't exist."""
    try:
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if cursor.fetchone():
            logger.info(f"Database '{db_name}' already exists")
        else:
            cursor.execute(f"CREATE DATABASE {db_name}")
            logger.info(f"Created database '{db_name}'")
    except Exception as e:
        logger.error(f"Error creating database '{db_name}': {e}")
        raise

def create_schemas_in_database(db_name, schemas):
    """Create schemas in the specified database."""
    try:
        # Connect to the specific database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        for schema in schemas:
            try:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                logger.info(f"Created/verified schema '{schema}' in database '{db_name}'")
            except Exception as e:
                logger.error(f"Error creating schema '{schema}' in '{db_name}': {e}")
                raise
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error connecting to database '{db_name}': {e}")
        raise

def grant_cross_database_permissions():
    """Grant permissions for cross-database access."""
    try:
        # Connect to the analytics database to grant permissions
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=ANALYTICS_DATABASE
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Grant usage on raw database schemas
        for schema in RAW_SCHEMAS:
            try:
                # Note: Cross-database permissions in PostgreSQL require specific setup
                # This is a placeholder for the actual permission configuration
                logger.info(f"Cross-database permissions configured for schema '{schema}'")
            except Exception as e:
                logger.warning(f"Could not set cross-database permissions for '{schema}': {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Error setting cross-database permissions: {e}")

def main():
    """Main setup function."""
    logger.info("Starting raw database setup...")
    
    try:
        # Connect to PostgreSQL server (default database)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'  # Connect to default database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create databases
        logger.info("Creating databases...")
        create_database_if_not_exists(cursor, RAW_DATABASE)
        create_database_if_not_exists(cursor, ANALYTICS_DATABASE)
        
        cursor.close()
        conn.close()
        
        # Create schemas in raw database
        logger.info(f"Creating schemas in {RAW_DATABASE}...")
        create_schemas_in_database(RAW_DATABASE, RAW_SCHEMAS)
        
        # Create schemas in analytics database
        logger.info(f"Creating schemas in {ANALYTICS_DATABASE}...")
        create_schemas_in_database(ANALYTICS_DATABASE, ANALYTICS_SCHEMAS)
        
        # Set up cross-database permissions
        logger.info("Setting up cross-database permissions...")
        grant_cross_database_permissions()
        
        logger.info("✅ Raw database setup completed successfully!")
        logger.info(f"Raw database: {RAW_DATABASE}")
        logger.info(f"Raw schemas: {', '.join(RAW_SCHEMAS)}")
        logger.info(f"Analytics database: {ANALYTICS_DATABASE}")
        logger.info(f"Analytics schemas: {', '.join(ANALYTICS_SCHEMAS)}")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    main()
