{{
    config(
        materialized = 'table'
    )
}}

with campaign_performance as (
    select
        campaign_id,
        campaign_source,
        campaign_name,
        campaign_type,
        campaign_channel,
        campaign_status,
        normalized_status,
        performance_score,
        performance_tier,
        total_spend,
        total_impressions,
        total_clicks,
        total_conversions,
        total_revenue,
        click_through_rate,
        conversion_rate,
        return_on_ad_spend,
        cost_per_conversion
    from {{ ref('int_campaigns__performance_metrics') }}
),

campaign_daily_metrics as (
    select
        campaign_id,
        campaign_source,
        date_day,
        spend,
        impressions,
        clicks,
        conversions,
        revenue,
        cumulative_spend,
        cumulative_conversions,
        cumulative_revenue,
        daily_performance_score
    from {{ ref('entity_campaigns_daily') }}
    where date_day >= current_date() - 90 -- Last 90 days
),

contact_attribution as (
    select
        c.contact_id,
        c.email,
        c.lifecycle_stage,
        c.first_campaign_touched,
        c.last_campaign_touched,
        c.first_touch_date,
        c.last_touch_date,
        c.lead_source,
        c.hs_analytics_source,
        c.hs_analytics_source_data_1,
        c.hs_analytics_source_data_2,
        d.deal_id,
        d.deal_name,
        d.deal_amount,
        d.deal_stage,
        d.close_date,
        d.is_closed_won
    from {{ ref('stg_hubspot__contacts') }} c
    left join {{ ref('stg_hubspot__deals') }} d
        on c.contact_id = d.contact_id
),

-- Attribution by campaign source
source_attribution as (
    select
        cp.campaign_source,
        count(distinct cp.campaign_id) as total_campaigns,
        count(distinct case when cp.normalized_status = 'Active' then cp.campaign_id end) as active_campaigns,
        
        -- Performance metrics
        sum(cp.total_spend) as total_spend,
        sum(cp.total_conversions) as total_conversions,
        sum(cp.total_revenue) as total_revenue,
        avg(cp.return_on_ad_spend) as avg_roas,
        
        -- Contact attribution
        count(distinct ca.contact_id) as attributed_contacts,
        count(distinct case when ca.deal_id is not null then ca.contact_id end) as contacts_with_deals,
        count(distinct ca.deal_id) as attributed_deals,
        sum(case when ca.is_closed_won then ca.deal_amount else 0 end) as closed_won_revenue,
        
        -- Efficiency metrics
        case when sum(cp.total_spend) > 0 then sum(cp.total_revenue) / sum(cp.total_spend) else 0 end as overall_roas,
        case when sum(cp.total_conversions) > 0 then sum(cp.total_spend) / sum(cp.total_conversions) else 0 end as overall_cpa,
        case when count(distinct ca.contact_id) > 0 then sum(cp.total_spend) / count(distinct ca.contact_id) else 0 end as cost_per_contact,
        case when count(distinct ca.deal_id) > 0 then sum(cp.total_spend) / count(distinct ca.deal_id) else 0 end as cost_per_deal
        
    from campaign_performance cp
    left join contact_attribution ca
        on (cp.campaign_name = ca.first_campaign_touched 
            or cp.campaign_name = ca.last_campaign_touched
            or cp.campaign_source = lower(ca.lead_source))
    group by 1
),

-- Campaign type performance
campaign_type_performance as (
    select
        campaign_type,
        count(distinct campaign_id) as campaigns,
        sum(total_spend) as total_spend,
        sum(total_conversions) as total_conversions,
        sum(total_revenue) as total_revenue,
        avg(performance_score) as avg_performance_score,
        
        -- Performance distribution
        count(case when performance_tier = 'High Performer' then 1 end) as high_performers,
        count(case when performance_tier = 'Good Performer' then 1 end) as good_performers,
        count(case when performance_tier = 'Average Performer' then 1 end) as average_performers,
        count(case when performance_tier = 'Under Performer' then 1 end) as under_performers
        
    from campaign_performance
    group by 1
),

-- Time-based trends
monthly_trends as (
    select
        date_trunc('month', date_day) as month,
        campaign_source,
        sum(spend) as monthly_spend,
        sum(conversions) as monthly_conversions,
        sum(revenue) as monthly_revenue,
        avg(daily_performance_score) as avg_monthly_score,
        
        -- Month-over-month calculations
        lag(sum(spend)) over (partition by campaign_source order by date_trunc('month', date_day)) as prev_month_spend,
        lag(sum(conversions)) over (partition by campaign_source order by date_trunc('month', date_day)) as prev_month_conversions
        
    from campaign_daily_metrics
    group by 1, 2
),

-- Multi-touch attribution model
multi_touch_attribution as (
    select
        'First Touch' as attribution_model,
        first_campaign_touched as campaign_name,
        count(distinct contact_id) as attributed_contacts,
        count(distinct deal_id) as attributed_deals,
        sum(case when is_closed_won then deal_amount else 0 end) as attributed_revenue
    from contact_attribution
    where first_campaign_touched is not null
    group by 1, 2
    
    union all
    
    select
        'Last Touch' as attribution_model,
        last_campaign_touched as campaign_name,
        count(distinct contact_id) as attributed_contacts,
        count(distinct deal_id) as attributed_deals,
        sum(case when is_closed_won then deal_amount else 0 end) as attributed_revenue
    from contact_attribution
    where last_campaign_touched is not null
    group by 1, 2
),

-- Final attribution dashboard
attribution_summary as (
    select
        'Overall' as dimension_type,
        'All Campaigns' as dimension_value,
        count(distinct campaign_id) as total_campaigns,
        sum(total_spend) as total_spend,
        sum(total_conversions) as total_conversions,
        sum(total_revenue) as total_revenue,
        case when sum(total_spend) > 0 then sum(total_revenue) / sum(total_spend) else 0 end as overall_roas,
        case when sum(total_conversions) > 0 then sum(total_spend) / sum(total_conversions) else 0 end as overall_cpa
    from campaign_performance
    
    union all
    
    select
        'Source' as dimension_type,
        campaign_source as dimension_value,
        total_campaigns,
        total_spend,
        total_conversions,
        total_revenue,
        overall_roas,
        overall_cpa
    from source_attribution
    
    union all
    
    select
        'Type' as dimension_type,
        campaign_type as dimension_value,
        campaigns as total_campaigns,
        total_spend,
        total_conversions,
        total_revenue,
        case when total_spend > 0 then total_revenue / total_spend else 0 end as overall_roas,
        case when total_conversions > 0 then total_spend / total_conversions else 0 end as overall_cpa
    from campaign_type_performance
)

select 
    *,
    
    -- Performance categorization
    case
        when overall_roas >= 4 then 'Excellent ROI'
        when overall_roas >= 2 then 'Good ROI'
        when overall_roas >= 1 then 'Break Even'
        else 'Negative ROI'
    end as roi_category,
    
    -- Spend efficiency
    case
        when total_spend >= 100000 then 'High Spend'
        when total_spend >= 50000 then 'Medium Spend'
        when total_spend >= 10000 then 'Low Spend'
        else 'Minimal Spend'
    end as spend_category,
    
    current_timestamp() as _synced_at
    
from attribution_summary
order by dimension_type, total_revenue desc