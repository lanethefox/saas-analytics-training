# Missing Columns Report

This report identifies all columns that are referenced in the staging models but don't exist in the actual database tables.

## 1. Users Table (`public.users`)

### Existing Columns:
- user_id
- account_id
- email
- role_type
- created_at
- first_name
- last_name

### Missing Columns Referenced in `stg_app_database__users.sql`:
- **location_id** (line 16) - Used for location assignment tracking
- **status** (lines 29-35) - Used for user status standardization
- **last_login_at** (lines 65, 70, 74-79) - Used for engagement calculations and activity status
- **updated_at** (line 66) - Used for tracking record updates

## 2. Accounts Table (`public.accounts`)

### Existing Columns:
- account_id
- account_name
- account_type
- created_at
- billing_email
- total_locations

### Missing Columns Referenced in `stg_app_database__accounts.sql`:
- **industry_vertical** (line 19) - Used for industry classification
- **updated_at** (line 23) - Used for tracking record updates
- **status** (lines 26-32) - Used for account status standardization
- **primary_contact_name** (line 36) - Used for contact information
- **primary_contact_phone** (line 37) - Used for contact information
- **employee_count** (lines 41, 49-55) - Used for company size categorization
- **headquarters_city** (line 44) - Used for geographic data
- **headquarters_state** (line 45) - Used for geographic data
- **headquarters_country** (line 46) - Used for geographic data

## 3. Devices Table (`public.devices`)

### Existing Columns:
- device_id
- location_id
- account_id
- device_type
- model_number
- firmware_version
- installation_date
- status

### Missing Columns Referenced in `stg_app_database__devices.sql`:
- **serial_number** (line 21) - Used for device identification
- **created_at** (lines 42, 43, 129) - Used for device age calculations
- **installer_name** (line 39) - Used for installation tracking
- **last_maintenance_date** (lines 46, 51) - Used for maintenance tracking
- **next_maintenance_due** (lines 47, 52-59) - Used for maintenance scheduling
- **maintenance_interval_days** (line 48) - Used for maintenance interval calculation
- **last_heartbeat_at** (lines 71, 72, 75-81) - Used for connectivity monitoring
- **updated_at** (line 130) - Used for tracking record updates

## 4. Subscriptions Table (`public.subscriptions`)

### Existing Columns:
- subscription_id
- account_id
- plan_type
- billing_cycle
- status
- trial_start_date
- trial_end_date
- created_at

### Missing Columns Referenced in `stg_app_database__subscriptions.sql`:
- **plan_name** (line 19) - Used for plan display name
- **base_price_cents** (lines 21, 22, 26, 28, 31, 33, 149) - Used for pricing and MRR/ARR calculations
- **started_at** (line 85) - Used for subscription start tracking
- **current_period_start** (lines 86, 104) - Used for billing period calculations
- **current_period_end** (lines 87, 98-101, 107, 112) - Used for renewal tracking
- **canceled_at** (lines 88, 116-120) - Used for churn tracking
- **ended_at** (line 89) - Used for subscription end tracking
- **updated_at** (line 90) - Used for tracking record updates

## 5. Locations Table (`public.locations`)

### Existing Columns:
- location_id
- account_id
- location_name
- location_type
- address
- city
- state
- country
- created_at

### Missing Columns Referenced in `stg_app_database__locations.sql`:
- **postal_code** (lines 26, 34) - Used for address standardization
- **latitude** (line 38, 142) - Used for geographic coordinates
- **longitude** (line 39, 142) - Used for geographic coordinates
- **timezone** (line 52) - Used for timezone tracking
- **business_hours** (line 53, 147) - Used for operational hours
- **seating_capacity** (lines 54, 61, 87-93) - Used for capacity planning
- **total_taps** (lines 57, 63) - Used for tap density calculations
- **active_device_count** (lines 58, 76, 82) - Used for operational status
- **status** (lines 68-73, 76, 82, 122) - Used for location status tracking
- **opened_date** (lines 97, 103, 109) - Used for location age calculations
- **closed_date** (lines 98, 115) - Used for closure tracking
- **updated_at** (line 99) - Used for tracking record updates

## Summary

The staging models expect many additional columns that don't exist in the actual database tables. These missing columns fall into several categories:

1. **Status Fields**: Most tables are missing status columns for tracking entity states
2. **Timestamps**: Missing updated_at, last_login_at, and various lifecycle timestamps
3. **Business Attributes**: Missing fields like employee_count, seating_capacity, pricing information
4. **Operational Data**: Missing maintenance dates, heartbeat timestamps, device counts
5. **Geographic Data**: Missing coordinates, postal codes, headquarters information
6. **Contact Information**: Missing primary contact details for accounts

## Recommendations

1. **Option 1**: Update the database schema to include these missing columns
2. **Option 2**: Modify the staging models to remove references to non-existent columns
3. **Option 3**: Create a mapping layer that provides default values for missing columns
4. **Option 4**: Source some of this data from other tables or systems if available elsewhere