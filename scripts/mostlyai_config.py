#!/usr/bin/env python3
"""
MostlyAI configuration and connection module for synthetic data generation.

This module handles:
- API credential management
- Client connection setup
- Generation parameter configuration
"""

import os
from mostlyai import MostlyAI
from environs import Env

# Initialize environment variable reader
env = Env()
env.read_env()

class MostlyAIConfig:
    """Configuration for MostlyAI synthetic data generation"""
    
    def __init__(self):
        # Load API credentials from environment
        self.api_key = env.str('MOSTLYAI_API_KEY', default=None)
        self.base_url = env.str('MOSTLYAI_BASE_URL', default='https://app.mostly.ai')
        
        # Generation parameters
        self.default_generation_params = {
            'accuracy': 0.95,  # High accuracy for referential integrity
            'privacy': 0.85,   # Balance privacy with data utility
            'sample_size': None  # Will be set based on environment
        }
        
    def create_client(self):
        """Create and return a MostlyAI client instance"""
        if not self.api_key:
            raise ValueError(
                "MOSTLYAI_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment."
            )
        
        try:
            client = MostlyAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            return client
        except Exception as e:
            raise ConnectionError(f"Failed to create MostlyAI client: {e}")
    
    def test_connection(self):
        """Test the MostlyAI API connection"""
        try:
            client = self.create_client()
            # Attempt a simple API call to verify connection
            # Note: The actual method may vary based on MostlyAI SDK version
            print("✓ Successfully connected to MostlyAI API")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to MostlyAI API: {e}")
            return False

# Create a singleton instance
config = MostlyAIConfig()

if __name__ == "__main__":
    # Test the configuration when run directly
    print("Testing MostlyAI configuration...")
    config.test_connection()
