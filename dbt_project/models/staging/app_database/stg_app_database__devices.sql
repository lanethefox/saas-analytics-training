{{ config(materialized='view') }}

-- Staging model for devices
-- Standardizes data types, adds derived fields, and enriches with business logic
-- Updated to match actual database schema

with source_data as (
    select * from {{ source('app_database', 'devices') }}
),

enriched as (
    select
        -- Primary identifiers
        id as device_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as device_key,
        location_id,
        customer_id,
        
        -- Core attributes
        device_type,
        category,
        manufacturer,
        model,
        serial_number,
        firmware_version,
        ip_address,
        mac_address,
        
        -- Device categorization
        case 
            when device_type = 'tap_controller' then 'primary'
            when device_type = 'sensor' then 'secondary'
            when device_type = 'gateway' then 'infrastructure'
            else 'other'
        end as device_priority,
        
        -- Status and connectivity
        status,
        usage_pattern,
        network_connectivity,
        case 
            when lower(status) = 'online' then true 
            else false 
        end as is_online,
        
        case 
            when lower(status) = 'online' then 'operational'
            when lower(status) = 'offline' then 'non_operational'
            when lower(status) = 'maintenance' then 'maintenance'
            when lower(status) = 'error' then 'error'
            else 'unknown'
        end as operational_status,
        
        -- Dates and lifecycle
        install_date,
        warranty_expiry,
        expected_lifespan_years,
        current_date - install_date as days_since_install,
        warranty_expiry - current_date as days_until_warranty_expiry,
        
        case
            when warranty_expiry < current_date then 'Expired'
            when warranty_expiry <= current_date + interval '90 days' then 'Expiring Soon'
            else 'Active'
        end as warranty_status,
        
        -- Financial and operational metrics
        purchase_price,
        energy_consumption_watts,
        
        -- Calculate daily energy cost (assuming $0.12 per kWh)
        case
            when energy_consumption_watts is not null then
                (energy_consumption_watts * 24 / 1000.0) * 0.12
            else null
        end as estimated_daily_energy_cost,
        
        -- Data quality flags
        case 
            when id is null then true else false 
        end as missing_device_id,
        
        case 
            when location_id is null then true else false 
        end as missing_location_id,
        
        case 
            when device_type is null or trim(device_type) = '' then true else false 
        end as missing_device_type,
        
        -- Timestamps
        created_at as device_created_at,
        updated_at as device_updated_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
