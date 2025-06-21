{{ config(materialized='view') }}

-- Staging model for HubSpot companies
-- Advanced CRM analytics with sales intelligence and lead scoring

with source_data as (
    select * from {{ source('hubspot', 'companies') }}
),

enriched as (
    select
        -- Primary identifiers
        id as hubspot_company_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as hubspot_company_key,
        
        -- Company details with standardization
        trim(properties::json->>'name') as company_name,
        lower(trim(properties::json->>'domain')) as company_domain,
        coalesce(trim(properties::json->>'industry'), 'unspecified') as industry,
        trim(properties::json->>'description') as company_description,
        
        -- Business metrics
        case 
            when properties::json->>'numberofemployees' ~ '^[0-9]+$' 
            then (properties::json->>'numberofemployees')::int
            else null
        end as employee_count,
        
        case 
            when properties::json->>'annualrevenue' ~ '^[0-9.]+$' 
            then (properties::json->>'annualrevenue')::decimal
            else null
        end as annual_revenue,
        
        lower(trim(properties::json->>'type')) as company_type,
        
        -- Company size categorization
        case 
            when (properties::json->>'numberofemployees')::int >= 1000 then 'enterprise'
            when (properties::json->>'numberofemployees')::int >= 100 then 'mid_market'
            when (properties::json->>'numberofemployees')::int >= 10 then 'small_business'
            when (properties::json->>'numberofemployees')::int > 0 then 'startup'
            else 'unknown'
        end as company_size_category,
        
        -- Revenue tier classification
        case 
            when (properties::json->>'annualrevenue')::decimal >= 100000000 then 'tier_1' -- $100M+
            when (properties::json->>'annualrevenue')::decimal >= 10000000 then 'tier_2' -- $10M+
            when (properties::json->>'annualrevenue')::decimal >= 1000000 then 'tier_3' -- $1M+
            when (properties::json->>'annualrevenue')::decimal >= 100000 then 'tier_4' -- $100K+
            when (properties::json->>'annualrevenue')::decimal > 0 then 'tier_5' -- <$100K
            else 'unknown'
        end as revenue_tier,
        
        -- Geographic information
        trim(properties::json->>'city') as city,
        upper(trim(properties::json->>'state')) as state_code,
        upper(trim(properties::json->>'country')) as country_code,
        trim(properties::json->>'zip') as postal_code,
        regexp_replace(properties::json->>'phone', '[^0-9+]', '', 'g') as phone_cleaned,
        lower(trim(properties::json->>'website')) as website,
        
        -- Extract domain from website if domain field is empty
        case 
            when properties::json->>'domain' is null or properties::json->>'domain' = ''
            then regexp_replace(
                lower(trim(properties::json->>'website')), 
                '^(https?://)?(www\.)?([^/]+).*$', 
                '\3'
            )
            else lower(trim(properties::json->>'domain'))
        end as primary_domain,
        
        -- Account mapping
        properties::json->>'account_id' as account_id,
        
        -- Sales lifecycle
        lower(properties::json->>'lifecyclestage') as lifecycle_stage,
        properties::json->>'hubspot_owner_id' as owner_id,
        lower(properties::json->>'hs_lead_status') as lead_status,
        
        -- Lead scoring components
        case 
            when lower(properties::json->>'lifecyclestage') = 'customer' then 100
            when lower(properties::json->>'lifecyclestage') = 'opportunity' then 80
            when lower(properties::json->>'lifecyclestage') = 'salesqualifiedlead' then 60
            when lower(properties::json->>'lifecyclestage') = 'marketingqualifiedlead' then 40
            when lower(properties::json->>'lifecyclestage') = 'lead' then 20
            when lower(properties::json->>'lifecyclestage') = 'subscriber' then 10
            else 0
        end as lifecycle_score,
        
        -- Engagement metrics from HubSpot
        case 
            when properties::json->>'hs_analytics_num_page_views' ~ '^[0-9]+$'
            then (properties::json->>'hs_analytics_num_page_views')::int
            else 0
        end as total_page_views,
        
        case 
            when properties::json->>'hs_analytics_num_visits' ~ '^[0-9]+$'
            then (properties::json->>'hs_analytics_num_visits')::int
            else 0
        end as total_website_visits,
        
        case 
            when properties::json->>'hs_analytics_source' is not null
            then lower(properties::json->>'hs_analytics_source')
            else 'unknown'
        end as analytics_source,
        
        -- Deal information
        case 
            when properties::json->>'num_associated_deals' ~ '^[0-9]+$'
            then (properties::json->>'num_associated_deals')::int
            else 0
        end as associated_deals_count,
        
        case 
            when properties::json->>'total_revenue' ~ '^[0-9.]+$'
            then (properties::json->>'total_revenue')::decimal
            else 0
        end as total_deal_value,
        
        -- Lead quality scoring
        case 
            when lower(properties::json->>'lifecyclestage') = 'customer' then 'existing_customer'
            when (properties::json->>'num_associated_deals')::int > 0 then 'high_quality'
            when (properties::json->>'hs_analytics_num_page_views')::int > 10 then 'engaged'
            when (properties::json->>'numberofemployees')::int >= 100 then 'target_size'
            when lower(properties::json->>'lifecyclestage') in ('salesqualifiedlead', 'marketingqualifiedlead') then 'qualified'
            else 'needs_nurturing'
        end as lead_quality_tier,
        
        -- Timestamps with proper conversion
        case 
            when properties::json->>'createdate' ~ '^[0-9]+$'
            then to_timestamp((properties::json->>'createdate')::bigint / 1000)
            else null
        end as hubspot_company_created_at,
        
        case 
            when properties::json->>'hs_lastmodifieddate' ~ '^[0-9]+$'
            then to_timestamp((properties::json->>'hs_lastmodifieddate')::bigint / 1000)
            else null
        end as hubspot_company_updated_at,
        
        case 
            when properties::json->>'hs_analytics_first_visit_timestamp' ~ '^[0-9]+$'
            then to_timestamp((properties::json->>'hs_analytics_first_visit_timestamp')::bigint / 1000)
            else null
        end as first_website_visit_at,
        
        case 
            when properties::json->>'hs_analytics_last_visit_timestamp' ~ '^[0-9]+$'
            then to_timestamp((properties::json->>'hs_analytics_last_visit_timestamp')::bigint / 1000)
            else null
        end as last_website_visit_at,
        
        -- Calculate days since last engagement
        case 
            when properties::json->>'hs_analytics_last_visit_timestamp' ~ '^[0-9]+$'
            then extract(days from (current_timestamp - to_timestamp((properties::json->>'hs_analytics_last_visit_timestamp')::bigint / 1000)))
            else null
        end as days_since_last_visit,
        
        -- Data quality flags
        case 
            when properties::json->>'name' is null or properties::json->>'name' = '' then true
            else false
        end as missing_company_name,
        
        case 
            when properties::json->>'domain' is null or properties::json->>'domain' = '' 
                and properties::json->>'website' is null or properties::json->>'website' = '' then true
            else false
        end as missing_domain,
        
        case 
            when properties::json->>'account_id' is null or properties::json->>'account_id' = '' then true
            else false
        end as missing_account_mapping,
        
        -- Technology stack (if tracked)
        properties::json->>'hs_analytics_source_data_1' as source_campaign,
        properties::json->>'hs_analytics_source_data_2' as source_medium,
        
        -- Metadata
        current_timestamp as _stg_loaded_at,
        current_timestamp as _stg_run_started_at
        
    from source_data
)

select * from enriched
