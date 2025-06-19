#!/usr/bin/env python3
"""
Apache Superset Setup and Configuration
This script automates the setup of Superset dashboards and data sources for the SaaS platform.
"""

import requests
import json
import time
import sys
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupersetManager:
    """Manages Superset API interactions for dashboard and chart creation."""
    
    def __init__(self, base_url: str = "http://localhost:8088", 
                 username: str = "admin", password: str = "admin_password_2024"):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        self.access_token = None
        
    def authenticate(self) -> bool:
        """Authenticate with Superset and get access token."""
        try:
            # Get CSRF token
            login_url = f"{self.base_url}/login/"
            response = self.session.get(login_url)
            response.raise_for_status()
            
            # Extract CSRF token from response
            if 'csrf_token' in response.text:
                import re
                csrf_match = re.search(r'csrf_token.*?value="([^"]+)"', response.text)
                if csrf_match:
                    self.csrf_token = csrf_match.group(1)
            
            # Login via API
            auth_url = f"{self.base_url}/api/v1/security/login"
            login_data = {
                "username": self.username,
                "password": self.password,
                "provider": "db",
                "refresh": True
            }
            
            headers = {"Content-Type": "application/json"}
            if self.csrf_token:
                headers["X-CSRFToken"] = self.csrf_token
                
            response = self.session.post(auth_url, json=login_data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get("access_token")
            
            if self.access_token:
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                logger.info("Successfully authenticated with Superset")
                return True
            else:
                logger.error("Failed to get access token")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def wait_for_superset(self, max_attempts: int = 30) -> bool:
        """Wait for Superset to be ready."""
        logger.info("Waiting for Superset to be ready...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    logger.info("Superset is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            logger.info(f"Attempt {attempt + 1}/{max_attempts} - Superset not ready yet...")
            time.sleep(10)
        
        logger.error("Superset failed to start within expected time")
        return False
    
    def create_database_connection(self) -> Optional[int]:
        """Create database connection to the main SaaS platform database."""
        try:
            database_config = {
                "database_name": "SaaS Platform Analytics",
                "sqlalchemy_uri": "postgresql://superset_readonly:superset_readonly_password_2024@postgres:5432/saas_platform_dev",
                "expose_in_sqllab": True,
                "allow_ctas": False,
                "allow_cvas": False,
                "allow_dml": False,
                "cache_timeout": None,
                "extra": json.dumps({
                    "allows_virtual_table_explore": True,
                    "cancel_query_on_windows_unload": True,
                    "metadata_cache_timeout": {},
                    "schemas_allowed_for_file_upload": []
                })
            }
            
            url = f"{self.base_url}/api/v1/database/"
            response = self.session.post(url, json=database_config)
            response.raise_for_status()
            
            result = response.json()
            database_id = result.get("id")
            logger.info(f"Created database connection with ID: {database_id}")
            return database_id
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    def get_databases(self) -> List[Dict]:
        """Get list of existing databases."""
        try:
            url = f"{self.base_url}/api/v1/database/"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            return result.get("result", [])
            
        except Exception as e:
            logger.error(f"Failed to get databases: {e}")
            return []
    
    def sync_database_tables(self, database_id: int) -> bool:
        """Sync tables for a database to refresh metadata."""
        try:
            url = f"{self.base_url}/api/v1/database/{database_id}/schemas"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Get available schemas
            schemas = response.json().get("result", [])
            
            # Refresh tables for each schema
            for schema in schemas:
                table_url = f"{self.base_url}/api/v1/database/{database_id}/tables"
                params = {"schema": schema}
                response = self.session.get(table_url, params=params)
                response.raise_for_status()
            
            logger.info(f"Synced tables for database {database_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync database tables: {e}")
            return False
    
    def create_dataset(self, database_id: int, table_name: str, schema: str = "public") -> Optional[int]:
        """Create a dataset from a database table."""
        try:
            dataset_config = {
                "database": database_id,
                "schema": schema,
                "table_name": table_name,
                "owners": [1]  # Admin user
            }
            
            url = f"{self.base_url}/api/v1/dataset/"
            response = self.session.post(url, json=dataset_config)
            response.raise_for_status()
            
            result = response.json()
            dataset_id = result.get("id")
            logger.info(f"Created dataset '{table_name}' with ID: {dataset_id}")
            return dataset_id
            
        except Exception as e:
            logger.error(f"Failed to create dataset {table_name}: {e}")
            return None
    
    def get_datasets(self) -> List[Dict]:
        """Get list of existing datasets."""
        try:
            url = f"{self.base_url}/api/v1/dataset/"
            response = self.session.get(url)
            response.raise_for_status()
            
            result = response.json()
            return result.get("result", [])
            
        except Exception as e:
            logger.error(f"Failed to get datasets: {e}")
            return []

def setup_core_datasets(superset: SupersetManager, database_id: int) -> Dict[str, int]:
    """Create datasets for core entity tables."""
    datasets = {}
    
    # Core entity tables to create datasets for
    entity_tables = [
        "entity_customers",
        "entity_customers_daily", 
        "entity_customers_history",
        "entity_locations",
        "entity_locations_weekly",
        "entity_users",
        "entity_users_weekly",
        "entity_subscriptions",
        "entity_subscriptions_monthly",
        "entity_devices",
        "entity_devices_hourly",
        "entity_campaigns",
        "entity_campaigns_daily",
        "entity_features",
        "entity_features_monthly"
    ]
    
    logger.info("Creating datasets for entity tables...")
    
    for table_name in entity_tables:
        dataset_id = superset.create_dataset(database_id, table_name)
        if dataset_id:
            datasets[table_name] = dataset_id
            time.sleep(1)  # Rate limiting
    
    return datasets

def setup_superset():
    """Main setup function for Superset configuration."""
    superset = SupersetManager()
    
    # Wait for Superset to be ready
    if not superset.wait_for_superset():
        logger.error("Superset is not responding. Please check the service status.")
        return False
    
    # Authenticate
    if not superset.authenticate():
        logger.error("Failed to authenticate with Superset")
        return False
    
    # Check for existing database connection
    databases = superset.get_databases()
    saas_db = None
    
    for db in databases:
        if "saas_platform_dev" in db.get("sqlalchemy_uri", ""):
            saas_db = db
            break
    
    # Create database connection if it doesn't exist
    if not saas_db:
        database_id = superset.create_database_connection()
        if not database_id:
            logger.error("Failed to create database connection")
            return False
    else:
        database_id = saas_db["id"]
        logger.info(f"Using existing database connection ID: {database_id}")
    
    # Sync database tables
    if not superset.sync_database_tables(database_id):
        logger.error("Failed to sync database tables")
        return False
    
    # Create core datasets
    datasets = setup_core_datasets(superset, database_id)
    if not datasets:
        logger.error("Failed to create any datasets")
        return False
    
    logger.info(f"Successfully created {len(datasets)} datasets")
    logger.info("Superset setup completed successfully!")
    
    logger.info("\n" + "="*60)
    logger.info("SUPERSET SETUP COMPLETE")
    logger.info("="*60)
    logger.info(f"Superset URL: http://localhost:8088")
    logger.info(f"Username: admin")
    logger.info(f"Password: admin_password_2024")
    logger.info("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = setup_superset()
        if success:
            logger.info("Superset setup completed successfully!")
            sys.exit(0)
        else:
            logger.error("Superset setup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during setup: {e}")
        sys.exit(1)
