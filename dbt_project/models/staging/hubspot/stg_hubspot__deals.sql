{{ config(materialized='view') }}

-- Staging model for HubSpot deal data
-- Standardizes sales opportunity tracking with forecasting metrics

with source_data as (
    select * from {{ source('hubspot', 'deals') }}
),

enriched as (
    select
        -- Primary identifiers
        id as hubspot_deal_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as hubspot_deal_key,
        
        -- Deal attributes from columns
        trim(dealname) as deal_name,
        amount as deal_amount,
        lower(trim(dealstage)) as deal_stage,
        lower(trim(pipeline)) as sales_pipeline,
        closedate as expected_close_date,
        archived,
        
        -- Extract additional fields from properties JSON
        trim(properties->>'hubspot_owner_id') as deal_owner_id,
        lower(trim(properties->>'dealtype')) as deal_type,
        trim(properties->>'hs_forecast_category') as forecast_category,
        
        -- Deal source attribution from properties
        trim(properties->>'hs_deal_source') as deal_source,
        trim(properties->>'hs_campaign') as source_campaign,
        lower(trim(properties->>'leadsource')) as lead_source,
        
        -- Sales process indicators from properties
        case
            when properties->>'hs_deal_stage_probability' ~ '^\d+(\.\d+)?$'
            then (properties->>'hs_deal_stage_probability')::numeric / 100.0
            else null
        end as close_probability,
        
        case
            when properties->>'num_notes' ~ '^\d+$'
            then (properties->>'num_notes')::integer
            else 0
        end as activity_count,
        
        -- Deal stage mapping
        case
            when lower(dealstage) like '%appoint%' or lower(dealstage) like '%qualif%' then 'Qualification'
            when lower(dealstage) like '%present%' or lower(dealstage) like '%demo%' then 'Presentation'
            when lower(dealstage) like '%proposal%' or lower(dealstage) like '%quote%' then 'Proposal'
            when lower(dealstage) like '%negotiat%' or lower(dealstage) like '%review%' then 'Negotiation'
            when lower(dealstage) like '%closed%won%' or lower(dealstage) like '%won%' then 'Closed Won'
            when lower(dealstage) like '%closed%lost%' or lower(dealstage) like '%lost%' then 'Closed Lost'
            else 'Other'
        end as standardized_stage,
        
        -- Deal size categorization
        case
            when amount < 1000 then 'Small'
            when amount < 10000 then 'Medium'
            when amount < 50000 then 'Large'
            when amount < 100000 then 'Extra Large'
            else 'Enterprise'
        end as deal_size_category,
        
        -- Time-based metrics
        current_date - closedate as days_until_close,
        current_date - date(createdat) as deal_age_days,
        
        case
            when closedate < current_date then 'Overdue'
            when closedate <= current_date + interval '7 days' then 'This Week'
            when closedate <= current_date + interval '30 days' then 'This Month'
            when closedate <= current_date + interval '90 days' then 'This Quarter'
            else 'Future'
        end as close_timeline,
        
        -- Deal health scoring
        case
            when lower(dealstage) like '%closed%' then 'Closed'
            when amount is null or amount = 0 then 'No Value'
            when closedate < current_date - interval '30 days' then 'At Risk'
            when properties->>'hs_deal_stage_probability' is null then 'Needs Attention'
            when (properties->>'hs_deal_stage_probability')::numeric > 70 then 'Healthy'
            when (properties->>'hs_deal_stage_probability')::numeric > 40 then 'Fair'
            else 'Poor'
        end as deal_health_status,
        
        -- Weighted pipeline value
        case
            when properties->>'hs_deal_stage_probability' ~ '^\d+(\.\d+)?$'
            then amount * ((properties->>'hs_deal_stage_probability')::numeric / 100.0)
            else amount * 0.1  -- Default 10% for unknown probability
        end as weighted_amount,
        
        -- Data quality flags
        case when dealname is null or trim(dealname) = '' then true else false end as missing_deal_name,
        case when amount is null or amount <= 0 then true else false end as invalid_amount,
        case when dealstage is null or trim(dealstage) = '' then true else false end as missing_stage,
        
        -- Timestamps
        createdat as deal_created_at,
        updatedat as deal_modified_at,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
