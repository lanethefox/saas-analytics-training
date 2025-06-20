#!/usr/bin/env python3
"""Test script to verify MostlyAI installation"""

try:
    import mostlyai
    print("✓ MostlyAI package imported successfully")
    print(f"✓ MostlyAI version: {mostlyai.__version__ if hasattr(mostlyai, '__version__') else 'Version info not available'}")
    print("✓ Installation test PASSED")
except ImportError as e:
    print(f"✗ Failed to import MostlyAI: {e}")
    print("✗ Installation test FAILED")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    print("✗ Installation test FAILED")
