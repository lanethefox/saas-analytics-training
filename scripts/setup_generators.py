#!/usr/bin/env python3

# Append HubSpot helper methods to HubSpot generator
with open('/Users/lane/Development/Active/data-platform/scripts/hubspot_generator.py', 'a') as f:
    with open('/Users/lane/Development/Active/data-platform/scripts/hubspot_helpers.py', 'r') as helper:
        f.write('\n\n')
        f.write(helper.read())

# Append Marketing helper methods to Marketing generator  
with open('/Users/lane/Development/Active/data-platform/scripts/marketing_generator.py', 'a') as f:
    with open('/Users/lane/Development/Active/data-platform/scripts/marketing_helpers.py', 'r') as helper:
        f.write('\n\n')
        f.write(helper.read())

# Append Device helper methods to Device generator
with open('/Users/lane/Development/Active/data-platform/scripts/device_generator.py', 'a') as f:
    with open('/Users/lane/Development/Active/data-platform/scripts/device_helpers.py', 'r') as helper:
        f.write('\n\n')
        f.write(helper.read())

print("✅ Helper methods combined with generators")
print("🚀 Synthetic data generator is ready to run!")
