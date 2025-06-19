{{ config(materialized='table') }}

-- Intermediate model: Campaign core information
-- Unified campaign data across all marketing channels with standardized attribution

with google_ads_campaigns as (
    select
        campaign_key,
        campaign_id as source_campaign_id,
        'google_ads' as marketing_channel,
        campaign_name,
        campaign_type,
        campaign_status,
        data_date,
        spend_usd,
        impressions,
        clicks,
        conversions,
        conversion_value_usd,
        click_through_rate,
        cost_per_click,
        cost_per_acquisition,
        conversion_rate,
        campaign_category,
        audience_type,
        traffic_volume_tier,
        ctr_performance_tier,
        attribution_channel,
        attribution_channel_group,
        is_paid_acquisition,
        campaign_created_date as campaign_created_at,
        campaign_modified_date as campaign_modified_at,
        _stg_loaded_at
    from {{ ref('stg_marketing__google_ads_campaigns') }}
),

meta_campaigns as (
    select
        campaign_key,
        campaign_id as source_campaign_id,
        'meta' as marketing_channel,
        campaign_name,
        campaign_objective as campaign_type,
        campaign_status,
        data_date,
        spend_usd,
        impressions,
        clicks,
        purchases as conversions,
        purchase_value_usd as conversion_value_usd,
        click_through_rate,
        cost_per_click,
        cost_per_acquisition,
        return_on_ad_spend as conversion_rate,  -- Using ROAS as proxy for conversion rate
        targeting_strategy as campaign_category,
        targeting_strategy as audience_type,
        volume_tier as traffic_volume_tier,
        ctr_performance_tier,
        attribution_channel,
        attribution_channel_group,
        is_paid_acquisition,
        campaign_created_at,
        campaign_updated_at as campaign_modified_at,
        _stg_loaded_at
    from {{ ref('stg_marketing__meta_campaigns') }}
),

linkedin_campaigns as (
    select
        campaign_key,
        campaign_id as source_campaign_id,
        'linkedin' as marketing_channel,
        campaign_name,
        campaign_objective as campaign_type,
        campaign_status,
        data_date,
        spend_usd,
        impressions,
        clicks,
        external_website_conversions as conversions,
        0 as conversion_value_usd,  -- LinkedIn doesn't track revenue directly
        click_through_rate,
        cost_per_click,
        cost_per_conversion as cost_per_acquisition,
        website_conversion_rate as conversion_rate,
        campaign_category,
        target_audience_type as audience_type,
        volume_tier as traffic_volume_tier,
        ctr_performance_tier,
        attribution_channel,
        attribution_channel_group,
        is_paid_acquisition,
        campaign_created_at,
        campaign_modified_at,
        _stg_loaded_at
    from {{ ref('stg_marketing__linkedin_campaigns') }}
),

email_campaigns as (
    select
        campaign_key,
        campaign_id as source_campaign_id,
        'email' as marketing_channel,
        campaign_name,
        campaign_type,
        campaign_status,
        send_date as data_date,
        0 as spend_usd,  -- Email is typically owned media
        unique_sends as impressions,
        unique_clicks as clicks,
        purchases as conversions,
        revenue_usd as conversion_value_usd,
        click_through_rate,
        0 as cost_per_click,  -- No cost per click for email
        0 as cost_per_acquisition,  -- No cost per acquisition for email
        email_conversion_rate as conversion_rate,
        email_category as campaign_category,
        delivery_type as audience_type,
        engagement_tier as traffic_volume_tier,
        ctr_performance_tier,
        attribution_channel,
        attribution_channel_group,
        is_paid_acquisition,
        campaign_created_at,
        campaign_updated_at as campaign_modified_at,
        _stg_loaded_at
    from {{ ref('stg_marketing__iterable_campaigns') }}
),

unified_campaigns as (
    select * from google_ads_campaigns
    union all
    select * from meta_campaigns
    union all
    select * from linkedin_campaigns
    union all
    select * from email_campaigns
),

final as (
    select
        -- Core identifiers
        campaign_key,
        source_campaign_id,
        marketing_channel,
        attribution_channel,
        attribution_channel_group,
        
        -- Campaign attributes
        campaign_name,
        campaign_type,
        campaign_status,
        campaign_category,
        audience_type,
        
        -- Performance metrics
        spend_usd,
        impressions,
        clicks,
        conversions,
        conversion_value_usd,
        
        -- Calculated metrics
        click_through_rate,
        cost_per_click,
        cost_per_acquisition,
        conversion_rate,
        
        case 
            when spend_usd > 0 then conversion_value_usd / spend_usd
            else 0
        end as return_on_ad_spend,
        
        case 
            when conversions > 0 then conversion_value_usd / conversions
            else 0
        end as avg_order_value,
        
        -- Performance classifications
        traffic_volume_tier,
        ctr_performance_tier,
        
        case 
            when return_on_ad_spend >= 3.0 then 'high_roas'
            when return_on_ad_spend >= 1.5 then 'medium_roas'
            when return_on_ad_spend >= 1.0 then 'break_even'
            when return_on_ad_spend > 0 then 'negative_roas'
            else 'no_revenue'
        end as roas_tier,
        
        -- Channel classification
        is_paid_acquisition,
        case 
            when marketing_channel in ('google_ads', 'meta', 'linkedin') then 'paid_digital'
            when marketing_channel = 'email' then 'owned_media'
            else 'other'
        end as media_type,
        
        -- Temporal attributes
        data_date,
        campaign_created_at,
        campaign_modified_at,
        
        -- Metadata
        current_timestamp as _intermediate_created_at
        
    from unified_campaigns
)

select * from final
