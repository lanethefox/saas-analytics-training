{{ config(materialized='table') }}

-- Intermediate model: Campaign core information
-- Combines campaign data from multiple marketing platforms (Google Ads, Facebook, LinkedIn, Iterable)
-- Provides unified view of all marketing campaigns across channels

with google_ads_campaigns as (
    select * from {{ ref('stg_marketing__google_ads_campaigns') }}
),

facebook_campaigns as (
    select * from {{ ref('stg_marketing__facebook_ads_campaigns') }}
),

linkedin_campaigns as (
    select * from {{ ref('stg_marketing__linkedin_ads_campaigns') }}
),

iterable_campaigns as (
    select * from {{ ref('stg_marketing__iterable_campaigns') }}
),

-- Union all campaigns into a single view with standardized fields
campaigns_unified as (
    -- Google Ads Campaigns
    select
        campaign_id,
        'google_ads' as platform,
        campaign_name,
        campaign_subtype as campaign_type,
        campaign_status,
        current_timestamp as campaign_created_at,  -- Not available in staging
        current_timestamp as campaign_updated_at,  -- Not available in staging
        start_date,
        end_date,
        cost as total_spend,
        impressions,
        clicks,
        conversions,
        0 as conversion_value,  -- Not available in staging
        null as target_audience,  -- Could parse from targeting_settings JSON
        null as target_location,  -- Could parse from targeting_settings JSON
        null as bid_strategy,
        case when campaign_status = 'ENABLED' then true else false end as is_active
    from google_ads_campaigns
    
    union all
    
    -- Facebook Ads Campaigns
    select
        campaign_id,
        'facebook' as platform,
        campaign_name,
        objective as campaign_type,
        campaign_status,
        created_time as campaign_created_at,
        created_time as campaign_updated_at,  -- No updated_at in staging
        start_time as start_date,
        stop_time as end_date,
        spend as total_spend,
        impressions,
        clicks,
        0 as conversions,  -- Not available in staging
        0 as conversion_value,  -- Not available in staging
        null as target_audience,
        null as target_location,
        bid_strategy,
        case when campaign_status = 'ACTIVE' then true else false end as is_active
    from facebook_campaigns
    
    union all
    
    -- LinkedIn Ads Campaigns
    select
        campaign_id,
        'linkedin' as platform,
        campaign_name,
        campaign_type,
        campaign_status,
        created_time as campaign_created_at,
        created_time as campaign_updated_at,  -- No updated_at in staging
        start_date as start_date,
        end_date as end_date,
        cost as total_spend,
        impressions,
        clicks,
        conversions,
        0 as conversion_value,  -- Not available in staging
        null as target_audience,
        null as target_location,
        null as bid_strategy,
        case when campaign_status = 'ACTIVE' then true else false end as is_active
    from linkedin_campaigns
    
    union all
    
    -- Iterable Email Campaigns (different structure, adapt accordingly)
    select
        campaign_id,
        'iterable' as platform,
        campaign_name,
        campaign_type,
        campaign_status,
        created_at as campaign_created_at,
        created_at as campaign_updated_at,  -- No updated_at in staging
        start_at as start_date,
        ended_at as end_date,
        0 as total_spend, -- Email campaigns typically don't have direct spend
        send_size as impressions,
        0 as clicks,  -- Not available in staging
        0 as conversions,  -- Not available in staging
        0 as conversion_value,
        null as target_audience,
        null as target_location,
        null as bid_strategy,
        case when campaign_status = 'ACTIVE' then true else false end as is_active
    from iterable_campaigns
),

-- Calculate metrics in a separate CTE
campaigns_with_metrics as (
    select
        -- Core identifiers
        {{ dbt_utils.generate_surrogate_key(['campaign_id', 'platform']) }} as campaign_key,
        campaign_id,
        platform,
        campaign_name,
        campaign_type,
        campaign_status,
        
        -- Campaign dates
        campaign_created_at,
        campaign_updated_at,
        start_date,
        end_date,
        
        -- Performance metrics
        coalesce(total_spend, 0) as total_spend,
        coalesce(impressions, 0) as impressions,
        coalesce(clicks, 0) as clicks,
        coalesce(conversions, 0) as conversions,
        coalesce(conversion_value, 0) as conversion_value,
        
        -- Calculated metrics
        case 
            when impressions > 0 then clicks::float / impressions * 100
            else 0
        end as click_through_rate,
        
        case 
            when clicks > 0 then conversions::float / clicks * 100
            else 0
        end as conversion_rate,
        
        case 
            when conversions > 0 then total_spend / conversions
            else null
        end as cost_per_conversion,
        
        case 
            when clicks > 0 then total_spend / clicks
            else null
        end as cost_per_click,
        
        case 
            when impressions > 0 then total_spend / impressions * 1000
            else null
        end as cost_per_thousand_impressions,
        
        -- ROI calculations
        case 
            when total_spend > 0 then (conversion_value - total_spend) / total_spend * 100
            else null
        end as roi_percentage,
        
        -- Campaign attributes
        target_audience,
        target_location,
        bid_strategy,
        is_active,
        
        -- Days active
        case 
            when start_date is not null then extract(days from current_date - start_date)::integer
            else 0
        end as days_active
        
    from campaigns_unified
),

final as (
    select
        *,
        
        -- Campaign health indicators (now can reference conversion_rate and cost_per_conversion)
        case 
            when conversion_rate >= 3 and cost_per_conversion < 100 then 'high_performing'
            when conversion_rate >= 1.5 and cost_per_conversion < 200 then 'good_performing'
            when conversion_rate >= 0.5 then 'average_performing'
            else 'under_performing'
        end as performance_tier,
        
        -- Lifecycle stage
        case 
            when is_active and current_date between start_date and coalesce(end_date, current_date + 1) then 'running'
            when is_active and current_date < start_date then 'scheduled'
            when not is_active and campaign_status ilike '%pause%' then 'paused'
            when current_date > coalesce(end_date, campaign_created_at + interval '90 days') then 'completed'
            else 'draft'
        end as campaign_lifecycle_stage,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from campaigns_with_metrics
)

select * from final