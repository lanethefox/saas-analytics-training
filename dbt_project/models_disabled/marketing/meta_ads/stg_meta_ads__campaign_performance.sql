{{ config(
    materialized='incremental',
    unique_key=['campaign_id', 'date'],
    on_schema_change='append_new_columns'
) }}

-- Staging model for Meta Ads (Facebook/Instagram) campaign performance

select
    -- Campaign identifiers
    campaign_id::varchar as meta_campaign_id,
    campaign_name,
    campaign_status,
    campaign_objective,
    
    -- Ad set and ad details
    adset_id::varchar as meta_adset_id,
    adset_name,
    ad_id::varchar as meta_ad_id,
    ad_name,
    
    -- Date and performance metrics
    date_start::date as performance_date,
    impressions,
    clicks,
    spend::decimal as cost_usd,
    
    -- Conversion metrics
    actions_value::decimal as conversion_value_usd,
    coalesce(actions_count, 0) as conversions,
    
    -- Video metrics (if applicable)
    video_views,
    video_play_actions,
    
    -- Engagement metrics
    post_engagements,
    page_likes,
    page_engagement,
    
    -- Calculated metrics
    case 
        when impressions > 0 then clicks / impressions::decimal
        else 0
    end as click_through_rate,
    
    case 
        when clicks > 0 then spend / clicks
        else 0
    end as cost_per_click,
    
    case 
        when conversions > 0 then spend / conversions
        else 0
    end as cost_per_conversion,
    
    -- Channel standardization
    'meta_ads' as marketing_channel,
    case 
        when campaign_objective in ('CONVERSIONS', 'CATALOG_SALES') then 'paid_social_conversion'
        when campaign_objective in ('REACH', 'BRAND_AWARENESS') then 'paid_social_awareness'
        when campaign_objective = 'TRAFFIC' then 'paid_social_traffic'
        else 'paid_social_other'
    end as channel_type,
    
    -- Account information
    account_id as meta_account_id,
    
    -- Metadata
    current_timestamp as _stg_loaded_at
    
from {{ source('meta_ads', 'campaign_insights') }}

{% if is_incremental() %}
    where date_start >= (select max(performance_date) from {{ this }})
{% endif %}
