{{ config(
    materialized='incremental',
    unique_key='lead_id',
    on_schema_change='fail',
    tags=['marketing', 'leads']
) }}

with source as (
    select * from {{ source('marketing', 'marketing_qualified_leads') }}
    
    {% if is_incremental() %}
        where created_at > (select max(created_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        -- IDs
        id as lead_id,
        contact_id,
        account_id,
        campaign_id,
        
        -- Lead Information
        lower(trim(email)) as email,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        trim(company_name) as company_name,
        lead_source,
        mql_score as lead_score,
        
        -- Additional metrics
        conversion_probability,
        days_to_mql,
        engagement_score,
        
        -- Dates
        mql_date,
        created_at_source,
        created_at,
        created_date,
        
        -- Lead Scoring Categories
        case
            when mql_score >= 90 then 'Hot'
            when mql_score >= 70 then 'Warm'
            when mql_score >= 50 then 'Cool'
            else 'Cold'
        end as lead_temperature,
        
        -- Lead Source Groupings
        case
            when lower(lead_source) like '%google%' then 'Google'
            when lower(lead_source) like '%linkedin%' then 'LinkedIn'
            when lower(lead_source) like '%facebook%' or lower(lead_source) like '%meta%' then 'Meta'
            when lower(lead_source) like '%organic%' then 'Organic'
            when lower(lead_source) like '%email%' then 'Email'
            when lower(lead_source) like '%event%' then 'Events'
            when lower(lead_source) like '%partner%' then 'Partner'
            when lower(lead_source) like '%direct%' then 'Direct'
            else 'Other'
        end as lead_source_category,
        
        -- Company Size Estimation (based on email domain)
        case
            when email like '%gmail.com' or email like '%yahoo.com' or email like '%hotmail.com' then 'Personal'
            when company_name is not null and length(company_name) > 20 then 'Enterprise'
            else 'Business'
        end as estimated_company_size,
        
        -- Lead Quality Indicators
        case
            when email is not null 
                and email like '%@%' 
                and email not like '%test%' 
                and email not like '%example%' then true
            else false
        end as has_valid_email,
        
        case
            when company_name is not null 
                and company_name != '' 
                and lower(company_name) not like '%test%' then true
            else false
        end as has_valid_company,
        
        -- Time-based Metrics
        current_date - mql_date::date as days_since_mql,
        extract(quarter from mql_date) as mql_quarter,
        extract(year from mql_date) as mql_year,
        
        -- Data Quality
        case
            when email is null or email = '' then 'Missing Email'
            when mql_score is null then 'Missing Score'
            when mql_date is null then 'Missing MQL Date'
            when email not like '%@%' then 'Invalid Email Format'
            else 'Valid'
        end as data_quality_flag,
        
        -- Audit Fields
        current_timestamp as _dbt_inserted_at,
        '{{ var("dbt_job_id", "manual_run") }}' as _dbt_job_id

    from source
),

final as (
    select * from renamed
)

select * from final
