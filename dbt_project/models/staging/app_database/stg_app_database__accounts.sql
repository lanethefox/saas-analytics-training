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
        business_type as industry, -- Expose industry from business_type
        email,
        location_count,
        employee_count,
        annual_revenue,
        website,
        status,
        
        -- Standardized timestamps
        created_at::timestamp as account_created_at,
        updated_at::timestamp as account_updated_at,
        
        -- Status standardization (use actual status field)
        lower(status) as account_status,
        
        -- Derived categorizations based on employee count (size-based)
        case 
            when employee_count > 1000 then 'enterprise'
            when employee_count > 250 then 'mid_market'
            when employee_count > 50 then 'small_business'
            else 'startup'
        end as company_size_category,
        
        case 
            when employee_count > 1000 then 1  -- Enterprise
            when employee_count > 250 then 2   -- Large/Business
            when employee_count > 50 then 3    -- Medium/Professional
            else 4                             -- Small/Starter
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
