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
        id::text as owner_id,
        userid::text as user_id,
        
        -- Owner Information (handle null columns gracefully)
        lower(trim(coalesce(email, '')))::text as email,
        trim(coalesce(firstname, ''))::text as first_name,
        trim(coalesce(lastname, ''))::text as last_name,
        coalesce(archived, false)::boolean as archived,
        
        -- Derived Fields
        case
            when firstname is not null and lastname is not null then
                concat(trim(firstname), ' ', trim(lastname))
            when firstname is not null then trim(firstname)
            when lastname is not null then trim(lastname)
            else 'Unknown'
        end::text as full_name,
        
        -- Owner Type (defaulting since 'type' column doesn't exist)
        'User'::text as owner_type,
        'Individual User'::text as owner_category,
        
        -- Email Domain Extraction
        case
            when email like '%@%' then split_part(email, '@', 2)
            else null
        end::text as email_domain,
        
        -- Internal vs External
        case
            when email like '%@hubspot.com' then 'HubSpot Internal'
            when email like '%@example.com' then 'Internal'  -- Replace with actual company domain
            else 'External'
        end::text as owner_classification,
        
        -- Status (simplified since activeuserid doesn't exist)
        case
            when archived = true then 'Inactive'
            else 'Active'
        end::text as owner_status,
        
        -- Tenure Calculation
        case
            when createdat is not null then (current_date - createdat::date)::integer
            else 0
        end::integer as tenure_days,
        
        case
            when createdat is null then 'Unknown'
            when current_date - createdat::date < 90 then 'New'
            when current_date - createdat::date < 365 then 'Experienced'
            else 'Veteran'
        end::text as tenure_category,
        
        -- Data Quality
        case
            when id is null then 'Missing Owner ID'
            when email is null or email = '' then 'Missing Email'
            when email not like '%@%' then 'Invalid Email Format'
            when firstname is null and lastname is null then 'Missing Name'
            else 'Valid'
        end::text as data_quality_flag,
        
        -- Timestamps
        createdat::timestamp as owner_created_at,
        updatedat::timestamp as owner_updated_at,
        
        -- Audit Fields
        current_timestamp::timestamp as _stg_loaded_at

    from source
),

final as (
    select * from renamed
)

select * from final
