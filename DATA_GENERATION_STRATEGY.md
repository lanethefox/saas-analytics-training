# Data Generation Strategy

## Overview

This document outlines the deterministic data generation strategy for the SaaS Platform data warehouse demo. The goal is to create realistic, consistent business data that simulates a B2B beverage dispensing platform.

## Business Model

We're simulating "TapFlow Analytics" - a B2B SaaS platform that provides smart beverage dispensing systems to restaurants, bars, stadiums, and other venues. The platform includes:

- Smart tap controllers for beverage dispensing
- IoT sensors for monitoring temperature, pressure, and flow
- Analytics dashboard for venue operators
- Subscription-based pricing model

## Data Generation Principles

### 1. Hierarchical Generation
Data is generated in a strict hierarchy to ensure referential integrity:
```
Accounts → Locations → Devices → Users → Subscriptions → Events
```

### 2. Deterministic IDs
- Use sequential IDs with reserved ranges
- Predictable ID allocation for easy debugging
- No random UUIDs - all IDs are integers

### 3. Seed-Based Randomization
- Fixed seed (42) for all random operations
- Ensures reproducible data across runs
- Allows for consistent testing

### 4. Temporal Consistency
- All timestamps follow logical progression
- Events occur after entity creation
- Maintenance follows installation dates

## Entity Specifications

### Accounts (Customers)
Total: 150 accounts

Distribution:
- Small (70%): 105 accounts, 1-2 locations each
- Medium (20%): 30 accounts, 3-10 locations each
- Large (8%): 12 accounts, 10-50 locations each
- Enterprise (2%): 3 accounts, 50-100 locations each

ID Range: 1-150

### Locations
Total: ~800 locations

Distribution per account type:
- Small accounts: 1-2 locations (avg 1.5)
- Medium accounts: 3-10 locations (avg 6)
- Large accounts: 10-50 locations (avg 25)
- Enterprise accounts: 50-100 locations (avg 75)

ID Range: 1-1000

### Devices
Total: ~25,000 devices

Distribution per location:
- Small account locations: 5-10 devices
- Medium account locations: 10-20 devices
- Large account locations: 20-50 devices
- Enterprise account locations: 30-100 devices

Device Types:
- Tap Controllers (60%): Primary beverage dispensing units
- Sensors (30%): Temperature, pressure, flow monitoring
- Gateways (10%): Network connectivity hubs

ID Range: 1-30000

### Users
Total: ~5,000 users

Distribution:
- Small accounts: 2-5 users
- Medium accounts: 5-20 users
- Large accounts: 20-100 users
- Enterprise accounts: 100-500 users

User Roles:
- Admin (10%): Full system access
- Manager (30%): Location management
- Staff (60%): Operational access

ID Range: 1-6000

### Subscriptions
One active subscription per account

Pricing Tiers:
- Starter ($299/mo): <10 devices
- Professional ($999/mo): 10-50 devices
- Business ($2,999/mo): 50-200 devices
- Enterprise ($9,999/mo): 200+ devices

Features vary by tier (API access, analytics, support level)

## Event Generation Strategy

### Tap Events
- Frequency: Based on venue type and time of day
- Peak hours: 11am-2pm (lunch), 6pm-11pm (dinner/evening)
- Volume: 20-200ml per pour
- Temperature: 2-6°C (normal), with occasional anomalies

### Feature Usage
- Dashboard views: 2-10 per user per day
- Report generation: Weekly/monthly cadence
- API calls: Proportional to device count

### Device Heartbeats
- Every 5 minutes for online devices
- Status: 85% online, 10% offline, 5% maintenance

## Data Quality Rules

### Operational Patterns
- 80-90% devices online during business hours
- 70-80% locations fully operational
- 5-10% devices need maintenance at any time
- 2-5% quality issues (temperature/pressure anomalies)

### Business Metrics
- MRR growth: 5-10% monthly for growing accounts
- Churn rate: 2-3% monthly
- Device utilization: 60-80% during peak hours
- Customer health score: Normal distribution (mean=0.75)

## ID Allocation Strategy

```yaml
id_ranges:
  accounts: [1, 150]
  locations: [1, 1000]
  devices: [1, 30000]
  users: [1, 6000]
  tap_events: [1, 10000000]
  feature_usage: [1, 1000000]
  subscriptions: [1, 200]
```

## Geographic Distribution

Locations distributed across:
- 40% Northeast US
- 25% West Coast
- 20% Southeast
- 15% Midwest

Cities weighted by population with realistic address generation.

## Temporal Distribution

### Account Creation
- 20% created 2+ years ago (established)
- 30% created 1-2 years ago (growing)
- 30% created 6-12 months ago (scaling)
- 20% created <6 months ago (new)

### Event Patterns
- Weekday vs weekend patterns
- Seasonal variations (summer peak for beverages)
- Growth trends for newer accounts

## Validation Requirements

### Referential Integrity
- All device.location_id must exist in locations
- All user.account_id must exist in accounts
- All events reference valid devices

### Business Logic
- Subscription MRR matches device count pricing
- Device status aligns with event activity
- Location operational status reflects device health

### Metrics Consistency
- Customer MRR = Sum of subscription amounts
- Device counts aggregate correctly to locations
- Event volumes align with business type

## Implementation Notes

### Configuration File
All parameters defined in `data_generation_config.yaml`:
- Entity counts and distributions
- Business rules and ratios
- Temporal parameters
- Random seed

### Generation Order
1. Load configuration
2. Generate accounts with business metadata
3. Generate locations mapped to accounts
4. Generate devices mapped to locations
5. Generate users mapped to accounts
6. Generate subscriptions with appropriate pricing
7. Generate historical events
8. Validate all relationships
9. Generate summary report

### Error Handling
- Validate each stage before proceeding
- Rollback on validation failure
- Detailed logging of generation process
- Summary statistics for verification

## Success Criteria

1. Zero referential integrity violations
2. Realistic business metrics:
   - 75%+ device uptime
   - 70%+ location operational rate
   - MRR within 5% of expected based on device counts
3. Temporal consistency across all events
4. Deterministic output (same data every run)