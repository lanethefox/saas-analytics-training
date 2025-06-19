{{ config(materialized='view') }}

-- Staging model for locations
-- Standardizes geographic data, adds enrichments for operations analysis

with source_data as (
    select * from {{ source('app_database', 'locations') }}
),

enriched as (
    select
        -- Primary identifiers
        id as location_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as location_key,
        customer_id as account_id,
        
        -- Location details
        trim(name) as location_name,
        trim(address) as address,
        trim(city) as city,
        upper(trim(state)) as state,
        trim(zip_code) as zip_code,
        upper(trim(country)) as country,
        
        -- Business attributes
        location_type,
        business_type,
        size as location_size,
        expected_device_count,
        
        -- Standardized address
        concat_ws(', ', 
            trim(address), 
            trim(city), 
            upper(trim(state)), 
            trim(zip_code)
        ) as full_address,
        
        -- Geographic categorizations
        case 
            when country = 'US' then 
                case
                    when state in ('CA', 'OR', 'WA', 'NV', 'AZ') then 'West'
                    when state in ('TX', 'OK', 'AR', 'LA', 'NM') then 'Southwest'
                    when state in ('IL', 'IN', 'MI', 'OH', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS') then 'Midwest'
                    when state in ('NY', 'NJ', 'PA', 'CT', 'RI', 'MA', 'VT', 'NH', 'ME') then 'Northeast'
                    when state in ('FL', 'GA', 'SC', 'NC', 'VA', 'WV', 'KY', 'TN', 'AL', 'MS') then 'Southeast'
                    else 'Other'
                end
            else 'International'
        end as region,
        
        -- Location type categorization
        case
            when lower(location_type) like '%flagship%' then 'Flagship'
            when lower(location_type) like '%standard%' then 'Standard'
            when lower(location_type) like '%express%' then 'Express'
            when lower(location_type) like '%kiosk%' then 'Kiosk'
            else 'Other'
        end as location_category,
        
        -- Business type grouping
        case
            when lower(business_type) like '%restaurant%' then 'Restaurant'
            when lower(business_type) like '%bar%' then 'Bar'
            when lower(business_type) like '%brewery%' then 'Brewery'
            when lower(business_type) like '%hotel%' then 'Hotel'
            when lower(business_type) like '%club%' then 'Club'
            else 'Other'
        end as business_category,
        
        -- Size categorization
        case
            when lower(size) = 'small' then 1
            when lower(size) = 'medium' then 2
            when lower(size) = 'large' then 3
            when lower(size) = 'enterprise' then 4
            else 0
        end as size_tier,
        
        -- Installation tracking
        install_date,
        current_date - install_date as days_since_install,
        
        case
            when install_date is null then 'Not Installed'
            when install_date > current_date then 'Scheduled'
            when install_date >= current_date - interval '30 days' then 'Recently Installed'
            when install_date >= current_date - interval '90 days' then 'New'
            when install_date >= current_date - interval '365 days' then 'Established'
            else 'Mature'
        end as installation_status,
        
        -- Data quality flags
        case 
            when name is null or trim(name) = '' then true else false 
        end as missing_location_name,
        
        case 
            when address is null or trim(address) = '' then true else false 
        end as missing_address,
        
        case 
            when city is null or state is null then true else false 
        end as incomplete_address,
        
        -- Timestamps
        created_at as location_created_at,
        updated_at as location_updated_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
