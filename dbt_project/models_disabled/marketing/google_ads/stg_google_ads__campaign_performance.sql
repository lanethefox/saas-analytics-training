{{ config(
    materialized='incremental',
    unique_key=['campaign_id', 'date'],
    on_schema_change='append_new_columns'
) }}

-- Staging model for Google Ads campaign performance
-- Daily campaign metrics for attribution analysis

select
    -- Campaign identifiers
    campaign_id::varchar as google_ads_campaign_id,
    campaign_name,
    campaign_status,
    campaign_type,
    
    -- Date and performance metrics
    date::date as performance_date,
    impressions,
    clicks,
    cost_micros / 1000000.0 as cost_usd,
    conversions,
    conversion_value / 1000000.0 as conversion_value_usd,
    
    -- Calculated metrics
    case 
        when impressions > 0 then clicks / impressions::decimal
        else 0
    end as click_through_rate,
    
    case 
        when clicks > 0 then (cost_micros / 1000000.0) / clicks
        else 0
    end as cost_per_click,
    
    case 
        when conversions > 0 then (cost_micros / 1000000.0) / conversions
        else 0
    end as cost_per_conversion,
    
    -- Channel standardization
    'google_ads' as marketing_channel,
    'paid_search' as channel_type,
    
    -- Account information
    customer_id as google_ads_account_id,
    
    -- Timestamps
    current_timestamp as _stg_loaded_at
    
from {{ source('google_ads', 'campaign_performance') }}

{% if is_incremental() %}
    where date >= (select max(performance_date) from {{ this }})
{% endif %}
