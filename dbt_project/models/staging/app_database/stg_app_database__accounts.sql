{{ config(materialized='view') }}

-- Staging model for customer accounts
-- Updated to match actual raw schema with basic columns

with source_data as (
    select * from {{ source('app_database', 'accounts') }}
),

enriched as (
    select
        -- Primary identifiers
        id as account_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as account_key,
        
        -- Core attributes (using available columns)
        trim(name) as account_name,
        lower(business_type) as account_type,
        email,
        location_count,
        
        -- Standardized timestamps
        created_at::timestamp as account_created_at,
        updated_at::timestamp as account_updated_at,
        
        -- Status standardization (business_type as proxy for status)
        case 
            when business_type in ('enterprise', 'professional', 'business') then 'active'
            when business_type = 'trial' then 'trial'
            else 'active'
        end as account_status,
        
        -- Derived categorizations based on business type
        case 
            when business_type = 'enterprise' then 'enterprise'
            when business_type = 'professional' then 'mid_market'
            when business_type = 'business' then 'small_business'
            else 'startup'
        end as company_size_category,
        
        case 
            when business_type = 'enterprise' then 1
            when business_type = 'professional' then 2
            when business_type = 'business' then 3
            else 4
        end as account_type_tier,
        
        -- Lifecycle calculations
        (current_date - created_at::date) as account_age_days,
        (extract(days from age(current_timestamp, created_at)) / 30)::integer as account_age_months,
        
        case 
            when created_at >= current_date - interval '90 days' then true
            else false
        end as is_new_customer,
        
        -- Data quality flags (based on available data)
        case 
            when name is null or trim(name) = '' then true
            else false
        end as missing_account_name,
        
        case 
            when business_type is null or trim(business_type) = '' then true
            else false
        end as missing_account_type,
        
        -- Metadata
        current_timestamp as _stg_loaded_at,
        current_timestamp as _stg_run_started_at
        
    from source_data
)

select * from enriched
