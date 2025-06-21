{{ config(materialized='view') }}

-- Staging model for HubSpot contact data
-- Standardizes lead and contact information for sales/marketing attribution

with source_data as (
    select * from {{ source('hubspot', 'contacts') }}
),

enriched as (
    select
        -- Primary identifiers
        id as hubspot_contact_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as hubspot_contact_key,
        
        -- Personal information from properties JSON
        lower(trim(properties->>'email')) as contact_email,
        trim(properties->>'firstname') as first_name,
        trim(properties->>'lastname') as last_name,
        concat_ws(' ', trim(properties->>'firstname'), trim(properties->>'lastname')) as full_name,
        trim(properties->>'company') as company_name,
        
        -- Contact attributes from properties
        trim(properties->>'jobtitle') as job_title,
        trim(properties->>'phone') as phone_number,
        trim(properties->>'country') as country,
        trim(properties->>'city') as city,
        trim(properties->>'state') as state,
        
        -- Lead management fields
        lower(trim(properties->>'lifecyclestage')) as lifecycle_stage,
        lower(trim(properties->>'lead_status')) as lead_status,
        lower(trim(properties->>'hs_lead_status')) as hubspot_lead_status,
        
        -- Source attribution
        trim(properties->>'hs_analytics_first_touch_converting_campaign') as first_touch_campaign,
        trim(properties->>'hs_analytics_last_touch_converting_campaign') as last_touch_campaign,
        lower(trim(properties->>'hs_analytics_source')) as traffic_source,
        lower(trim(properties->>'hs_analytics_source_data_1')) as source_data_1,
        lower(trim(properties->>'hs_analytics_source_data_2')) as source_data_2,
        
        -- Engagement scoring (converting to numeric)
        case 
            when properties->>'hubspotscore' ~ '^\d+(\.\d+)?$' 
            then (properties->>'hubspotscore')::numeric
            else null
        end as hubspot_score,
        
        case 
            when properties->>'hs_lead_score' ~ '^\d+(\.\d+)?$'
            then (properties->>'hs_lead_score')::numeric
            else null
        end as lead_score,
        
        -- Timestamps (use actual column names)
        createdat as contact_created_at,
        updatedat as contact_modified_at,
        
        -- Parse HubSpot timestamp if available
        case 
            when properties->>'hs_marketable_until_renewal' ~ '^\d+$'
            then to_timestamp((properties->>'hs_marketable_until_renewal')::bigint / 1000)
            else null
        end as marketable_until,
        
        -- Email engagement
        coalesce((properties->>'hs_email_optout')::boolean, false) as email_opted_out,
        coalesce((properties->>'hs_email_bounce')::boolean, false) as email_bounced,
        coalesce((properties->>'hs_sequences_is_enrolled')::boolean, false) as in_sequence,
        
        -- Sales qualification
        case 
            when lower(trim(properties->>'lifecyclestage')) = 'subscriber' then 1
            when lower(trim(properties->>'lifecyclestage')) = 'lead' then 2
            when lower(trim(properties->>'lifecyclestage')) = 'marketingqualifiedlead' then 3
            when lower(trim(properties->>'lifecyclestage')) = 'salesqualifiedlead' then 4
            when lower(trim(properties->>'lifecyclestage')) = 'opportunity' then 5
            when lower(trim(properties->>'lifecyclestage')) = 'customer' then 6
            when lower(trim(properties->>'lifecyclestage')) = 'evangelist' then 7
            else 0
        end as lifecycle_stage_order,
        
        -- Lead scoring categories
        case 
            when (properties->>'hubspotscore')::numeric >= 80 then 'hot'
            when (properties->>'hubspotscore')::numeric >= 60 then 'warm'
            when (properties->>'hubspotscore')::numeric >= 40 then 'cool'
            when (properties->>'hubspotscore')::numeric > 0 then 'cold'
            else 'unscored'
        end as lead_temperature,
        
        -- Contact quality indicators
        case 
            when properties->>'email' is not null 
                and properties->>'firstname' is not null 
                and properties->>'lastname' is not null 
                and properties->>'company' is not null then 'complete'
            when properties->>'email' is not null 
                and (properties->>'firstname' is not null or properties->>'lastname' is not null) then 'partial'
            when properties->>'email' is not null then 'minimal'
            else 'incomplete'
        end as contact_data_quality,
        
        -- Attribution channel classification
        case 
            when lower(properties->>'hs_analytics_source') like '%google%' then 'google'
            when lower(properties->>'hs_analytics_source') like '%facebook%' 
                or lower(properties->>'hs_analytics_source') like '%meta%' then 'meta'
            when lower(properties->>'hs_analytics_source') like '%linkedin%' then 'linkedin'
            when lower(properties->>'hs_analytics_source') like '%email%' then 'email'
            when lower(properties->>'hs_analytics_source') = 'direct traffic' then 'direct'
            when lower(properties->>'hs_analytics_source') = 'organic search' then 'organic_search'
            when lower(properties->>'hs_analytics_source') like '%referral%' then 'referral'
            else 'unknown'
        end as primary_attribution_channel,
        
        case 
            when lower(properties->>'hs_analytics_source') in ('paid search', 'paid social', 'display ads') then 'paid'
            when lower(properties->>'hs_analytics_source') in ('organic search', 'social media', 'referrals') then 'organic'
            when lower(properties->>'hs_analytics_source') = 'direct traffic' then 'direct'
            when lower(properties->>'hs_analytics_source') like '%email%' then 'email'
            else 'unknown'
        end as attribution_channel_group,
        
        -- Engagement indicators
        case 
            when coalesce((properties->>'hs_sequences_is_enrolled')::boolean, false) then 'in_sequence'
            when coalesce((properties->>'hs_email_optout')::boolean, false) then 'opted_out'
            when coalesce((properties->>'hs_email_bounce')::boolean, false) then 'bounced'
            else 'marketable'
        end as email_marketing_status,
        
        -- Time-based analysis
        extract(days from (current_timestamp - createdat)) as days_since_creation,
        extract(days from (current_timestamp - updatedat)) as days_since_last_update,
        
        case 
            when extract(days from (current_timestamp - createdat)) <= 7 then 'this_week'
            when extract(days from (current_timestamp - createdat)) <= 30 then 'this_month'
            when extract(days from (current_timestamp - createdat)) <= 90 then 'this_quarter'
            else 'older'
        end as contact_age_category,
        
        -- Data quality flags
        case 
            when properties->>'email' is null or properties->>'email' = '' then true
            else false
        end as missing_email,
        
        case 
            when properties->>'email' is not null 
                and properties->>'email' !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' then true
            else false
        end as invalid_email_format,
        
        case 
            when properties->>'firstname' is null and properties->>'lastname' is null then true
            else false
        end as missing_name,
        
        case 
            when properties->>'company' is null or properties->>'company' = '' then true
            else false
        end as missing_company,
        
        case 
            when properties->>'hs_analytics_source' is null then true
            else false
        end as missing_attribution,
        
        -- Metadata
        current_timestamp as _stg_loaded_at,
        current_timestamp as _stg_run_started_at
        
    from source_data
)

select * from enriched