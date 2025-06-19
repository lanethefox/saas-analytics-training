{{ config(
    materialized='view',
    tags=['hubspot', 'users']
) }}

with source as (
    select * from {{ source('hubspot', 'owners') }}
),

renamed as (
    select
        -- IDs
        id as owner_id,
        userid as user_id,
        activeuserid as active_user_id,
        
        -- Owner Information
        lower(trim(email)) as email,
        trim(firstname) as first_name,
        trim(lastname) as last_name,
        type as owner_type,
        archived,
        
        -- Derived Fields
        concat(trim(firstname), ' ', trim(lastname)) as full_name,
        
        -- Owner Type Categorization
        case
            when lower(type) = 'user' then 'Individual User'
            when lower(type) = 'team' then 'Team'
            when lower(type) = 'queue' then 'Queue'
            else 'Other'
        end as owner_category,
        
        -- Email Domain Extraction
        split_part(email, '@', 2) as email_domain,
        
        -- Internal vs External
        case
            when email like '%@hubspot.com' then 'HubSpot Internal'
            when email like '%@example.com' then 'Internal'  -- Replace with actual company domain
            else 'External'
        end as owner_classification,
        
        -- Status
        case
            when archived = true then 'Inactive'
            when activeuserid is not null then 'Active'
            else 'Unknown'
        end as owner_status,
        
        -- Remote list processing (if needed)
        remotelist,
        
        -- Tenure Calculation
        current_date - createdat::date as tenure_days,
        
        case
            when current_date - createdat::date < 90 then 'New'
            when current_date - createdat::date < 365 then 'Experienced'
            else 'Veteran'
        end as tenure_category,
        
        -- Data Quality
        case
            when id is null then 'Missing Owner ID'
            when email is null or email = '' then 'Missing Email'
            when email not like '%@%' then 'Invalid Email Format'
            when firstname is null and lastname is null then 'Missing Name'
            else 'Valid'
        end as data_quality_flag,
        
        -- Timestamps
        createdat as owner_created_at,
        updatedat as owner_updated_at,
        
        -- Audit Fields
        current_timestamp as _stg_loaded_at

    from source
),

final as (
    select * from renamed
)

select * from final
