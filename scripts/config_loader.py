"""
Configuration loader for data generation scripts.
Provides centralized access to data_generation_config.yaml parameters.
"""

import yaml
import os
from typing import Dict, Any
import random
import numpy as np

class DataGenerationConfig:
    """Centralized configuration management for data generation."""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'data_generation_config.yaml')
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Set random seeds for reproducibility
        self.set_random_seeds()
        
    def set_random_seeds(self):
        """Set random seeds for all random number generators."""
        seed = self.config['random_seed']
        random.seed(seed)
        np.random.seed(seed)
        
    def get_account_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get account distribution configuration."""
        return self.config['accounts']['distribution']
    
    def get_total_accounts(self) -> int:
        """Get total number of accounts to generate."""
        return self.config['accounts']['total']
    
    def get_industries(self) -> Dict[str, float]:
        """Get industry distribution."""
        return self.config['industries']
    
    def get_geographic_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get geographic distribution configuration."""
        return self.config['geographic_distribution']
    
    def get_device_config(self) -> Dict[str, Any]:
        """Get device configuration."""
        return self.config['devices']
    
    def get_subscription_tiers(self) -> Dict[str, Dict[str, Any]]:
        """Get subscription tier configuration."""
        return self.config['subscription_tiers']
    
    def get_id_ranges(self) -> Dict[str, list]:
        """Get ID ranges for each entity type."""
        return self.config['id_ranges']
    
    def get_time_ranges(self) -> Dict[str, Any]:
        """Get time range configuration."""
        return self.config['time_ranges']
    
    def get_user_roles(self) -> Dict[str, Dict[str, Any]]:
        """Get user role configuration."""
        return self.config['user_roles']
    
    def get_event_config(self) -> Dict[str, Any]:
        """Get event generation configuration."""
        return self.config['events']
    
    def get_growth_patterns(self) -> Dict[str, Any]:
        """Get growth pattern configuration."""
        return self.config['growth_patterns']
    
    def get_maintenance_config(self) -> Dict[str, Any]:
        """Get maintenance configuration."""
        return self.config['maintenance']


class IDAllocator:
    """Manages ID allocation for entities to ensure uniqueness and proper ranges."""
    
    def __init__(self, config: DataGenerationConfig):
        self.config = config
        self.id_ranges = config.get_id_ranges()
        self.current_ids = {entity: ranges[0] for entity, ranges in self.id_ranges.items()}
        
    def get_next_id(self, entity_type: str) -> int:
        """Get the next available ID for an entity type."""
        if entity_type not in self.current_ids:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        current_id = self.current_ids[entity_type]
        max_id = self.id_ranges[entity_type][1]
        
        if current_id > max_id:
            raise ValueError(f"ID range exhausted for {entity_type}. Current: {current_id}, Max: {max_id}")
        
        self.current_ids[entity_type] = current_id + 1
        return current_id
    
    def reset(self, entity_type: str = None):
        """Reset ID counter for an entity type or all types."""
        if entity_type:
            self.current_ids[entity_type] = self.id_ranges[entity_type][0]
        else:
            self.current_ids = {entity: ranges[0] for entity, ranges in self.id_ranges.items()}


def load_config(config_path: str = None) -> DataGenerationConfig:
    """Convenience function to load configuration."""
    return DataGenerationConfig(config_path)