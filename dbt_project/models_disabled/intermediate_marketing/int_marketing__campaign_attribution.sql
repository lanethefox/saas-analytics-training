{{ config(materialized='table') }}

-- Intermediate model: Multi-channel marketing attribution
-- Unifies campaign performance across all marketing channels

with google_ads_data as (
    select
        google_ads_campaign_id as campaign_id,
        campaign_name,
        marketing_channel,
        channel_type,
        performance_date,
        impressions,
        clicks,
        cost_usd,
        conversions,
        conversion_value_usd,
        click_through_rate,
        cost_per_click,
        cost_per_conversion
    from {{ ref('stg_google_ads__campaign_performance') }}
),

meta_ads_data as (
    select
        meta_campaign_id as campaign_id,
        campaign_name,
        marketing_channel,
        channel_type,
        performance_date,
        impressions,
        clicks,
        cost_usd,
        conversions,
        conversion_value_usd,
        click_through_rate,
        cost_per_click,
        cost_per_conversion
    from {{ ref('stg_meta_ads__campaign_performance') }}
),

linkedin_ads_data as (
    select
        linkedin_campaign_id as campaign_id,
        campaign_name,
        marketing_channel,
        channel_type,
        performance_date,
        impressions,
        clicks,
        cost_usd,
        conversions,
        conversion_value_usd,
        click_through_rate,
        cost_per_click,
        case when leads > 0 then cost_usd / leads else cost_per_click end as cost_per_conversion
    from {{ ref('stg_linkedin_ads__campaign_performance') }}
),

unified_campaigns as (
    select * from google_ads_data
    union all
    select * from meta_ads_data  
    union all
    select * from linkedin_ads_data
),

campaign_performance_metrics as (
    select
        campaign_id,
        campaign_name,
        marketing_channel,
        channel_type,
        performance_date,
        
        -- Core metrics
        impressions,
        clicks,
        cost_usd,
        conversions,
        conversion_value_usd,
        
        -- Calculated rates
        click_through_rate,
        cost_per_click,
        cost_per_conversion,
        
        -- ROI calculations
        case 
            when cost_usd > 0 then conversion_value_usd / cost_usd
            else 0
        end as return_on_ad_spend,
        
        -- Efficiency metrics
        case 
            when impressions > 0 then conversions / impressions::decimal * 1000
            else 0
        end as conversion_rate_per_mille,
        
        -- Performance scoring (0-1 scale)
        case 
            when channel_type like '%conversion%' then
                case 
                    when cost_per_conversion <= 50 and return_on_ad_spend >= 3.0 then 0.95
                    when cost_per_conversion <= 100 and return_on_ad_spend >= 2.0 then 0.80
                    when cost_per_conversion <= 200 and return_on_ad_spend >= 1.5 then 0.65
                    when cost_per_conversion <= 400 and return_on_ad_spend >= 1.0 then 0.50
                    else 0.30
                end
            when channel_type like '%awareness%' then
                case 
                    when cost_per_click <= 2.0 and click_through_rate >= 0.02 then 0.95
                    when cost_per_click <= 4.0 and click_through_rate >= 0.015 then 0.80
                    when cost_per_click <= 6.0 and click_through_rate >= 0.01 then 0.65
                    when cost_per_click <= 10.0 and click_through_rate >= 0.005 then 0.50
                    else 0.30
                end
            else 0.50
        end as campaign_performance_score
        
    from unified_campaigns
),

campaign_trends as (
    select
        campaign_id,
        campaign_name,
        marketing_channel,
        channel_type,
        
        -- Aggregate metrics
        sum(impressions) as total_impressions,
        sum(clicks) as total_clicks,
        sum(cost_usd) as total_cost_usd,
        sum(conversions) as total_conversions,
        sum(conversion_value_usd) as total_conversion_value_usd,
        
        -- Performance averages
        avg(click_through_rate) as avg_click_through_rate,
        avg(cost_per_click) as avg_cost_per_click,
        avg(cost_per_conversion) as avg_cost_per_conversion,
        avg(return_on_ad_spend) as avg_return_on_ad_spend,
        avg(campaign_performance_score) as avg_campaign_performance_score,
        
        -- Trend indicators (30-day vs previous 30-day)
        count(distinct performance_date) as active_days,
        min(performance_date) as campaign_start_date,
        max(performance_date) as campaign_end_date,
        
        -- Recent performance (last 7 days)
        sum(case when performance_date >= current_date - 7 then cost_usd else 0 end) as cost_last_7d,
        sum(case when performance_date >= current_date - 7 then conversions else 0 end) as conversions_last_7d,
        avg(case when performance_date >= current_date - 7 then campaign_performance_score else null end) as performance_score_last_7d
        
    from campaign_performance_metrics
    group by campaign_id, campaign_name, marketing_channel, channel_type
),

final as (
    select
        -- Campaign identifiers
        ct.campaign_id,
        ct.campaign_name,
        ct.marketing_channel,
        ct.channel_type,
        
        -- Performance metrics
        ct.total_impressions,
        ct.total_clicks,
        ct.total_cost_usd,
        ct.total_conversions,
        ct.total_conversion_value_usd,
        
        -- Efficiency metrics
        ct.avg_click_through_rate,
        ct.avg_cost_per_click,
        ct.avg_cost_per_conversion,
        ct.avg_return_on_ad_spend,
        ct.avg_campaign_performance_score,
        
        -- Campaign lifecycle
        ct.active_days,
        ct.campaign_start_date,
        ct.campaign_end_date,
        extract(days from (ct.campaign_end_date - ct.campaign_start_date + 1)) as campaign_duration_days,
        
        -- Recent performance indicators
        ct.cost_last_7d,
        ct.conversions_last_7d,
        ct.performance_score_last_7d,
        
        -- Campaign health indicators
        case 
            when ct.avg_campaign_performance_score >= 0.8 then 'high_performance'
            when ct.avg_campaign_performance_score >= 0.6 then 'good_performance'
            when ct.avg_campaign_performance_score >= 0.4 then 'average_performance'
            when ct.avg_campaign_performance_score >= 0.2 then 'poor_performance'
            else 'failing'
        end as campaign_health_status,
        
        -- Budget efficiency
        case 
            when ct.total_cost_usd > 0 and ct.total_conversion_value_usd > 0 
            then ct.total_conversion_value_usd / ct.total_cost_usd
            else 0
        end as lifetime_roas,
        
        case 
            when ct.total_conversions > 0 
            then ct.total_cost_usd / ct.total_conversions
            else null
        end as lifetime_cost_per_conversion,
        
        -- Activity indicators
        case 
            when ct.campaign_end_date >= current_date - 3 then 'active'
            when ct.campaign_end_date >= current_date - 7 then 'recent'
            when ct.campaign_end_date >= current_date - 30 then 'paused'
            else 'historical'
        end as campaign_status,
        
        -- Metadata
        current_timestamp as _intermediate_created_at
        
    from campaign_trends ct
)

select * from final
