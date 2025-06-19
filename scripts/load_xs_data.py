#!/usr/bin/env python3
"""
Load XS test data into the database
"""

import sys
import os

# Update the DATA_DIR to point to test_xs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and monkey-patch the DATA_DIR
import load_synthetic_data
load_synthetic_data.DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    'data', 'test_xs'
)

# Import the main function and run it
from load_synthetic_data import main

if __name__ == "__main__":
    print("Loading XS test data from:", load_synthetic_data.DATA_DIR)
    main()
