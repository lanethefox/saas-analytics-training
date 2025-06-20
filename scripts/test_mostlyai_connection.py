#!/usr/bin/env python3
"""Test script to verify MostlyAI API connection"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.mostlyai_config import config

def test_mostlyai_connection():
    """Test the MostlyAI API connection"""
    print("=" * 60)
    print("MostlyAI Connection Test")
    print("=" * 60)
    
    # Check if API key is configured
    if not config.api_key or config.api_key == 'your-mostlyai-api-key-here':
        print("\n⚠️  WARNING: MostlyAI API key not configured!")
        print("\nTo configure MostlyAI:")
        print("1. Sign up for a MostlyAI account at https://mostly.ai")
        print("2. Get your API key from the MostlyAI dashboard")
        print("3. Update the MOSTLYAI_API_KEY in your .env file")
        print("\nCurrent configuration:")
        print(f"  MOSTLYAI_BASE_URL: {config.base_url}")
        print(f"  MOSTLYAI_API_KEY: {'Not set' if not config.api_key else 'Set but placeholder'}")
        return False
    
    # Test the connection
    print(f"\nTesting connection to: {config.base_url}")
    print(f"API Key configured: {'*' * 10}{config.api_key[-10:]}")
    
    success = config.test_connection()
    
    if success:
        print("\n✅ MostlyAI API connection test PASSED!")
    else:
        print("\n❌ MostlyAI API connection test FAILED!")
        print("\nPlease check:")
        print("- Your API key is valid")
        print("- You have internet connectivity")
        print("- The MostlyAI service is available")
    
    return success

if __name__ == "__main__":
    test_mostlyai_connection()
