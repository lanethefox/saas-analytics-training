# Data Generation Runbook

## Overview

This runbook provides step-by-step instructions for generating deterministic data for the TapFlow Analytics platform. The new data generation system ensures:

- **Deterministic output**: Same data every run with fixed seed
- **Valid relationships**: All foreign keys reference existing records
- **Proper ID allocation**: Sequential IDs within defined ranges
- **Business realism**: Data follows configured business rules

## Prerequisites

1. PostgreSQL database running (via Docker or local)
2. Python environment with dependencies installed
3. Database initialized with schema

## Quick Start

### Option 1: Generate All Data (Recommended)

```bash
cd scripts/
python generate_all_deterministic.py
```

This will:
1. Truncate all existing data (with confirmation)
2. Generate all entities in the correct order
3. Validate data integrity
4. Display summary statistics

### Option 2: Generate Individual Entities

If you need to regenerate specific entities:

```bash
cd scripts/

# Always start with accounts (root entity)
python generate_accounts.py

# Then locations (depends on accounts)
python generate_locations.py

# Then devices (depends on locations)
python generate_devices.py

# Then users (depends on accounts)
python generate_users.py

# Finally subscriptions (depends on accounts and devices)
python generate_subscriptions.py
```

## Data Generation Order

The hierarchical generation order MUST be followed:

```
1. Accounts (150 records)
   ↓
2. Locations (~800 records)
   ↓
3. Devices (~25,000 records)
   ↓
4. Users (~5,000 records)
   ↓
5. Subscriptions (~180 records)
```

## Configuration

All parameters are defined in `scripts/data_generation_config.yaml`:

### Key Settings

- **Random seed**: 42 (ensures reproducibility)
- **Business name**: TapFlow Analytics
- **Time range**: 2020-01-01 to 2025-06-25

### Entity Distributions

#### Accounts (150 total)
- Small (70%): 105 accounts
- Medium (20%): 30 accounts  
- Large (8%): 12 accounts
- Enterprise (2%): 3 accounts

#### Locations per Account
- Small: 1-2 locations
- Medium: 3-10 locations
- Large: 10-50 locations
- Enterprise: 50-100 locations

#### Devices per Location
- Small: 5-10 devices
- Medium: 10-20 devices
- Large: 20-50 devices
- Enterprise: 30-100 devices

#### Users per Account
- Small: 2-5 users
- Medium: 5-20 users
- Large: 20-100 users
- Enterprise: 100-500 users

## Validation

After generation, validate data integrity:

```bash
python scripts/validate_data_integrity.py
```

This checks:
- ID ranges compliance
- Foreign key validity
- Business rule adherence
- Data consistency

## Common Issues and Solutions

### Issue: "Foreign key violation" errors

**Cause**: Attempting to generate entities out of order.

**Solution**: Always follow the hierarchical order. Use `generate_all_deterministic.py` for safety.

### Issue: Device location_ids don't exist

**Cause**: This was the original bug - devices referenced location IDs up to 4443 when only 1-99 existed.

**Solution**: The refactored generators now ensure devices only reference valid location IDs (1-1000).

### Issue: Duplicate key violations

**Cause**: Running generators without truncating existing data.

**Solution**: Always respond 'y' to truncate prompts, or manually truncate:

```sql
TRUNCATE TABLE raw.app_database_devices CASCADE;
TRUNCATE TABLE raw.app_database_locations CASCADE;
-- etc.
```

## Testing Data Quality

After generation, run these checks:

```bash
# Check device-location relationships
psql $DATABASE_URL -c "
SELECT COUNT(*) as orphaned_devices
FROM raw.app_database_devices d
LEFT JOIN raw.app_database_locations l ON d.location_id = l.id
WHERE l.id IS NULL;"

# Should return 0

# Check ID ranges
psql $DATABASE_URL -c "
SELECT 
    'devices' as entity,
    MIN(id) as min_id, 
    MAX(id) as max_id,
    COUNT(*) as count
FROM raw.app_database_devices;"

# Should show IDs within 1-30000 range
```

## Docker Integration

To use in Docker initialization:

```dockerfile
# In your Dockerfile or docker-compose
RUN python scripts/generate_all_deterministic.py
```

Or in initialization script:

```bash
#!/bin/bash
echo "Generating deterministic data..."
cd /app/scripts
python generate_all_deterministic.py
```

## Customization

To modify data generation:

1. Edit `scripts/data_generation_config.yaml`
2. Adjust distributions, counts, or ratios
3. Re-run generation pipeline
4. Validate output

### Adding New Entities

1. Define ID range in config
2. Create generator following pattern:
   - Use `DataGenerationConfig` and `IDAllocator`
   - Load parent entity mappings from JSON
   - Generate with proper foreign keys
   - Save mapping for dependent entities
3. Add to pipeline in correct hierarchical position

## Event Generators

For transactional data (tap events, page views, etc.), separate generators handle temporal consistency:

```bash
# After core entities are generated
python generate_tap_events.py
python generate_page_views.py
python generate_feature_usage.py
```

These maintain referential integrity with the core entities.

## Troubleshooting

### Enable Debug Logging

```python
# In any generator script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database State

```bash
# Count all entities
psql $DATABASE_URL -c "
SELECT 
    'accounts' as entity, COUNT(*) FROM raw.app_database_accounts
UNION ALL
SELECT 'locations', COUNT(*) FROM raw.app_database_locations
UNION ALL
SELECT 'devices', COUNT(*) FROM raw.app_database_devices
UNION ALL
SELECT 'users', COUNT(*) FROM raw.app_database_users
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM raw.app_database_subscriptions;"
```

### Reset Everything

```bash
# Nuclear option - drop and recreate schema
psql $DATABASE_URL -c "DROP SCHEMA raw CASCADE;"
psql $DATABASE_URL -c "CREATE SCHEMA raw;"

# Re-run schema creation
psql $DATABASE_URL -f database/01_main_schema.sql

# Generate fresh data
python scripts/generate_all_deterministic.py
```

## Success Criteria

A successful data generation run will show:

1. ✅ All generators complete without errors
2. ✅ Validation passes with no errors
3. ✅ Expected record counts:
   - 150 accounts
   - ~800 locations  
   - ~25,000 devices
   - ~5,000 users
   - ~180 subscriptions
4. ✅ No orphaned foreign keys
5. ✅ Realistic business metrics in reports

## Contact

For issues or questions about the data generation system, refer to:
- `DATA_GENERATION_STRATEGY.md` - Detailed methodology
- `ENTITY_RELATIONSHIPS.md` - Relationship diagrams
- `scripts/data_generation_config.yaml` - All configuration parameters