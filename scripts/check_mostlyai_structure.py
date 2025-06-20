#!/usr/bin/env python3
"""Check MostlyAI module structure"""

import mostlyai
import inspect
import sys

print("MostlyAI module location:", mostlyai.__file__ if hasattr(mostlyai, '__file__') else 'No file attribute')
print("\nAvailable attributes in mostlyai module:")
for attr in dir(mostlyai):
    if not attr.startswith('_'):
        obj = getattr(mostlyai, attr)
        print(f"  {attr}: {type(obj).__name__}")
        
print("\nTrying to find the client class...")
# Check common patterns
patterns = ['Client', 'MostlyAI', 'MostlyAIClient', 'API', 'client']
for pattern in patterns:
    if hasattr(mostlyai, pattern):
        print(f"Found: mostlyai.{pattern}")
