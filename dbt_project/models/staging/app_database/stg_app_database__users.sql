{{ config(materialized='view') }}

-- Staging model for users
-- Standardizes user data and adds engagement metrics

with source_data as (
    select * from {{ source('app_database', 'users') }}
),

enriched as (
    select
        -- Primary identifiers
        id as user_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as user_key,
        customer_id as account_id,
        
        -- User information
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        concat(trim(first_name), ' ', trim(last_name)) as full_name,
        lower(trim(email)) as email,
        
        -- Email domain extraction
        split_part(lower(trim(email)), '@', 2) as email_domain,
        
        -- Role information
        role as user_role,
        case
            when lower(role) like '%admin%' then 'Admin'
            when lower(role) like '%manager%' then 'Manager'
            when lower(role) like '%operator%' then 'Operator'
            when lower(role) like '%viewer%' then 'Viewer'
            else 'Standard'
        end as role_category,
        
        -- Permission levels
        case
            when lower(role) like '%admin%' then 4
            when lower(role) like '%manager%' then 3
            when lower(role) like '%operator%' then 2
            else 1
        end as permission_level,
        
        -- Activity tracking
        created_date,
        last_login_date,
        current_date - last_login_date as days_since_last_login,
        current_date - created_date as account_age_days,
        
        -- User status
        case
            when last_login_date is null then 'Never Logged In'
            when current_date - last_login_date <= 7 then 'Active'
            when current_date - last_login_date <= 30 then 'Recent'
            when current_date - last_login_date <= 90 then 'Inactive'
            else 'Dormant'
        end as user_status,
        
        -- Engagement scoring
        case
            when last_login_date is null then 0
            when current_date - last_login_date <= 1 then 100
            when current_date - last_login_date <= 7 then 80
            when current_date - last_login_date <= 30 then 60
            when current_date - last_login_date <= 90 then 30
            else 10
        end as engagement_score,
        
        -- Lifecycle stage
        case
            when created_date >= current_date - interval '7 days' then 'New'
            when created_date >= current_date - interval '30 days' then 'Onboarding'
            when created_date >= current_date - interval '90 days' then 'Adopting'
            when created_date >= current_date - interval '365 days' then 'Established'
            else 'Veteran'
        end as lifecycle_stage,
        
        -- Data quality flags
        case 
            when email is null or email = '' then true 
            else false 
        end as missing_email,
        
        case 
            when email not like '%@%' then true 
            else false 
        end as invalid_email,
        
        case 
            when first_name is null or trim(first_name) = '' then true 
            else false 
        end as missing_first_name,
        
        case 
            when last_name is null or trim(last_name) = '' then true 
            else false 
        end as missing_last_name,
        
        -- Timestamps
        created_at as user_created_at,
        updated_at as user_updated_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
