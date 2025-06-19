{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Entity: Campaigns Daily Grain
-- Daily campaign performance aggregations for trend analysis and operational reporting
-- Primary use cases: Daily marketing operations, budget pacing, performance trending

with daily_campaign_performance as (
    select
        campaign_key,
        marketing_channel,
        attribution_channel,
        attribution_channel_group,
        campaign_name,
        campaign_status,
        data_date,
        
        -- Daily performance metrics
        spend_usd,
        impressions,
        clicks,
        conversions,
        conversion_value_usd,
        click_through_rate,
        cost_per_click,
        cost_per_acquisition,
        return_on_ad_spend,
        
        -- Campaign attributes
        campaign_category,
        audience_type,
        media_type,
        is_paid_acquisition
        
    from {{ ref('int_campaigns__core') }}
    where data_date is not null
),

daily_aggregates as (
    select
        data_date,
        campaign_key,
        marketing_channel,
        attribution_channel,
        attribution_channel_group,
        campaign_name,
        campaign_status,
        campaign_category,
        audience_type,
        media_type,
        is_paid_acquisition,
        
        -- Daily metrics
        spend_usd,
        impressions,
        clicks,
        conversions,
        conversion_value_usd,
        click_through_rate,
        cost_per_click,
        cost_per_acquisition,
        return_on_ad_spend,
        
        -- Rolling calculations (7-day)
        avg(spend_usd) over (
            partition by campaign_key 
            order by data_date 
            rows between 6 preceding and current row
        ) as spend_7d_avg,
        
        avg(return_on_ad_spend) over (
            partition by campaign_key 
            order by data_date 
            rows between 6 preceding and current row
        ) as roas_7d_avg,
        
        sum(conversions) over (
            partition by campaign_key 
            order by data_date 
            rows between 6 preceding and current row
        ) as conversions_7d_total,
        
        -- Rolling calculations (30-day)
        avg(spend_usd) over (
            partition by campaign_key 
            order by data_date 
            rows between 29 preceding and current row
        ) as spend_30d_avg,
        
        sum(spend_usd) over (
            partition by campaign_key 
            order by data_date 
            rows between 29 preceding and current row
        ) as spend_30d_total,
        
        sum(conversions) over (
            partition by campaign_key 
            order by data_date 
            rows between 29 preceding and current row
        ) as conversions_30d_total,
        
        avg(return_on_ad_spend) over (
            partition by campaign_key 
            order by data_date 
            rows between 29 preceding and current row
        ) as roas_30d_avg,
        
        -- Day-over-day changes
        lag(spend_usd) over (partition by campaign_key order by data_date) as prev_day_spend,
        lag(conversions) over (partition by campaign_key order by data_date) as prev_day_conversions,
        lag(return_on_ad_spend) over (partition by campaign_key order by data_date) as prev_day_roas,
        
        -- Week-over-week changes  
        lag(spend_usd, 7) over (partition by campaign_key order by data_date) as week_ago_spend,
        lag(conversions, 7) over (partition by campaign_key order by data_date) as week_ago_conversions,
        
        -- Cumulative metrics
        sum(spend_usd) over (
            partition by campaign_key 
            order by data_date 
            rows unbounded preceding
        ) as cumulative_spend,
        
        sum(conversions) over (
            partition by campaign_key 
            order by data_date 
            rows unbounded preceding
        ) as cumulative_conversions,
        
        sum(conversion_value_usd) over (
            partition by campaign_key 
            order by data_date 
            rows unbounded preceding
        ) as cumulative_revenue
        
    from daily_campaign_performance
),

final as (
    select
        -- Identifiers and dimensions
        data_date,
        campaign_key,
        marketing_channel,
        attribution_channel,
        attribution_channel_group,
        campaign_name,
        campaign_status,
        campaign_category,
        audience_type,
        media_type,
        is_paid_acquisition,
        
        -- Core daily metrics
        spend_usd as daily_spend,
        impressions as daily_impressions,
        clicks as daily_clicks,
        conversions as daily_conversions,
        conversion_value_usd as daily_conversion_value,
        click_through_rate as daily_ctr,
        cost_per_click as daily_cpc,
        cost_per_acquisition as daily_cpa,
        return_on_ad_spend as daily_roas,
        
        -- Rolling averages and totals
        spend_7d_avg,
        spend_30d_avg,
        spend_30d_total,
        roas_7d_avg,
        roas_30d_avg,
        conversions_7d_total,
        conversions_30d_total,
        
        -- Change calculations
        case 
            when prev_day_spend > 0 
            then (spend_usd - prev_day_spend) / prev_day_spend
            else 0
        end as spend_change_day_over_day,
        
        conversions - coalesce(prev_day_conversions, 0) as conversions_change_day_over_day,
        
        case 
            when prev_day_roas > 0 
            then (return_on_ad_spend - prev_day_roas) / prev_day_roas
            else 0
        end as roas_change_day_over_day,
        
        case 
            when week_ago_spend > 0 
            then (spend_usd - week_ago_spend) / week_ago_spend
            else 0
        end as spend_change_week_over_week,
        
        conversions - coalesce(week_ago_conversions, 0) as conversions_change_week_over_week,
        
        -- Cumulative metrics
        cumulative_spend,
        cumulative_conversions,
        cumulative_revenue,
        
        case 
            when cumulative_spend > 0 
            then cumulative_revenue / cumulative_spend
            else 0
        end as cumulative_roas,
        
        case 
            when cumulative_conversions > 0 
            then cumulative_spend / cumulative_conversions
            else 0
        end as cumulative_cpa,
        
        -- Performance indicators
        case 
            when spend_usd >= spend_30d_avg * 1.5 then 'high_spend_day'
            when spend_usd <= spend_30d_avg * 0.5 then 'low_spend_day'
            else 'normal_spend_day'
        end as spend_anomaly_flag,
        
        case 
            when conversions >= conversions_7d_total / 7 * 2 then 'high_conversion_day'
            when conversions = 0 and conversions_7d_total > 0 then 'zero_conversion_day'
            else 'normal_conversion_day'
        end as conversion_anomaly_flag,
        
        case 
            when return_on_ad_spend >= roas_30d_avg * 1.5 then 'high_roas_day'
            when return_on_ad_spend <= roas_30d_avg * 0.5 and roas_30d_avg > 0 then 'low_roas_day'
            else 'normal_roas_day'
        end as roas_anomaly_flag,
        
        -- Date attributes
        extract(dow from data_date) as day_of_week,
        extract(month from data_date) as month_of_year,
        date_trunc('week', data_date) as week_start_date,
        date_trunc('month', data_date) as month_start_date,
        date_trunc('quarter', data_date) as quarter_start_date,
        
        case 
            when extract(dow from data_date) in (0, 6) then 'weekend'
            else 'weekday'
        end as day_type,
        
        -- Metadata
        current_timestamp as _grain_created_at
        
    from daily_aggregates
)

select * from final
