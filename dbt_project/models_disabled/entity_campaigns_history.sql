{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Entity: Campaigns History
-- Complete audit trail capturing every campaign state change over time
-- Primary use cases: Attribution modeling, campaign lifecycle analysis, optimization impact assessment

with campaign_daily_snapshots as (
    select
        campaign_key,
        marketing_channel,
        campaign_name,
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
        return_on_ad_spend,
        
        -- Calculate daily changes
        lag(spend_usd) over (partition by campaign_key order by data_date) as prev_day_spend,
        lag(conversions) over (partition by campaign_key order by data_date) as prev_day_conversions,
        lag(campaign_status) over (partition by campaign_key order by data_date) as prev_day_status,
        
        -- Identify significant changes
        case 
            when lag(campaign_status) over (partition by campaign_key order by data_date) != campaign_status 
            then 'status_change'
            when abs(spend_usd - lag(spend_usd, 1, 0) over (partition by campaign_key order by data_date)) > 100
            then 'budget_change'
            when conversions > lag(conversions, 1, 0) over (partition by campaign_key order by data_date)
            then 'conversion_event'
            else 'daily_update'
        end as change_type,
        
        campaign_created_at,
        campaign_modified_at
        
    from {{ ref('int_campaigns__core') }}
    where data_date is not null
),

campaign_change_events as (
    select
        -- Identifiers
        campaign_key,
        marketing_channel,
        campaign_name,
        
        -- Change tracking
        data_date as valid_from,
        lead(data_date) over (partition by campaign_key order by data_date) as valid_to,
        change_type,
        
        -- Performance state
        campaign_status,
        spend_usd,
        impressions,
        clicks,
        conversions,
        conversion_value_usd,
        click_through_rate,
        cost_per_click,
        cost_per_acquisition,
        return_on_ad_spend,
        
        -- Change metrics
        spend_usd - coalesce(prev_day_spend, 0) as daily_spend_change,
        conversions - coalesce(prev_day_conversions, 0) as daily_conversion_change,
        
        case 
            when prev_day_status is not null and prev_day_status != campaign_status
            then prev_day_status
            else null
        end as previous_status,
        
        -- Performance deltas
        case 
            when prev_day_spend > 0 
            then (spend_usd - prev_day_spend) / prev_day_spend
            else 0
        end as spend_change_rate,
        
        -- Cumulative metrics
        sum(spend_usd) over (partition by campaign_key order by data_date rows unbounded preceding) as cumulative_spend,
        sum(conversions) over (partition by campaign_key order by data_date rows unbounded preceding) as cumulative_conversions,
        sum(conversion_value_usd) over (partition by campaign_key order by data_date rows unbounded preceding) as cumulative_revenue,
        
        -- Campaign lifecycle context
        campaign_created_at,
        extract(days from (data_date - campaign_created_at::date)) as campaign_age_at_change,
        
        -- Row metadata
        row_number() over (partition by campaign_key order by data_date) as change_sequence_number,
        case 
            when lead(data_date) over (partition by campaign_key order by data_date) is null 
            then true 
            else false 
        end as is_current_state
        
    from campaign_daily_snapshots
),

final as (
    select
        -- Core identifiers
        campaign_key,
        marketing_channel,
        campaign_name,
        
        -- Temporal validity
        valid_from,
        coalesce(valid_to, '2099-12-31'::date) as valid_to,
        is_current_state,
        
        -- Change classification
        change_type,
        change_sequence_number,
        campaign_age_at_change,
        
        -- Campaign state
        campaign_status,
        previous_status,
        
        -- Performance metrics at change
        spend_usd as daily_spend,
        impressions as daily_impressions,
        clicks as daily_clicks,
        conversions as daily_conversions,
        conversion_value_usd as daily_conversion_value,
        
        -- Performance rates
        click_through_rate,
        cost_per_click,
        cost_per_acquisition,
        return_on_ad_spend,
        
        -- Change metrics
        daily_spend_change,
        daily_conversion_change,
        spend_change_rate,
        
        -- Cumulative metrics
        cumulative_spend,
        cumulative_conversions,
        cumulative_revenue,
        
        case 
            when cumulative_spend > 0 
            then cumulative_revenue / cumulative_spend
            else 0
        end as cumulative_roas,
        
        -- Temporal attributes
        campaign_created_at,
        
        -- Metadata
        current_timestamp as _history_created_at
        
    from campaign_change_events
)

select * from final
