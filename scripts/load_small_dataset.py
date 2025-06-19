#!/usr/bin/env python3
"""
Load Small dataset (1000 customers) into PostgreSQL
"""

import os
import sys

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the generators to ensure all required data exists
from device_generator import DeviceDataGenerator
from hubspot_generator import HubSpotDataGenerator
from marketing_generator import MarketingDataGenerator

# Import the standard loader
from load_synthetic_data import DataLoader

def main():
    """Load the small dataset"""
    print("🚀 Loading Small Dataset (1000 customers)")
    print("=" * 50)
    
    # Create and run the standard loader
    loader = DataLoader()
    
    try:
        # Run the complete loading process
        loader.run()
        
        print("\n✅ Small dataset loading complete!")
        print("   - 1000 customers loaded")
        print("   - ~4400 locations")
        print("   - ~22000 devices")
        print("   - Complete marketing and billing data")
        
    except Exception as e:
        print(f"\n❌ Error during loading: {e}")
        raise

if __name__ == "__main__":
    main()
