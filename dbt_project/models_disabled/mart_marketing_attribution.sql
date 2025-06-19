{{ config(materialized='table') }}

-- Marketing Attribution and Performance Mart
-- Cross-channel marketing analytics optimized for marketing team workflows
-- Includes attribution modeling, campaign performance, and ROI analysis

with campaign_performance as (
    select
        ec.campaign_key,
        ec.source_campaign_id,
        ec.marketing_channel,
        ec.attribution_channel,
        ec.attribution_channel_group,
        ec.campaign_name,
        ec.campaign_category,
        ec.audience_type,
        ec.campaign_status,
        
        -- Performance metrics
        ec.total_spend,
        ec.total_impressions,
        ec.total_clicks,
        ec.total_conversions,
        ec.total_conversion_value,
        ec.overall_click_through_rate,
        ec.overall_cost_per_click,
        ec.overall_cost_per_acquisition,
        ec.overall_return_on_ad_spend,
        ec.avg_order_value,
        
        -- Attribution metrics
        ec.attributed_contacts,
        ec.attributed_deals,
        ec.attributed_deal_value,
        ec.won_deals,
        ec.won_deal_value,
        ec.deal_win_rate,
        ec.pipeline_roi,
        
        -- Performance classifications
        ec.spend_tier,
        ec.roas_performance,
        ec.pipeline_performance,
        ec.campaign_performance_score,
        
        -- Temporal attributes
        ec.campaign_created_at,
        ec.campaign_age_days,
        ec.latest_data_date,
        ec.days_since_last_data
        
    from {{ ref('entity_campaigns') }} ec
    where ec.campaign_status in ('active', 'paused')  -- Focus on manageable campaigns
),

contact_attribution as (
    select
        hc.hubspot_contact_id,
        hc.contact_email,
        hc.company_name,
        hc.lifecycle_stage,
        hc.lead_status,
        hc.hubspot_score,
        hc.primary_attribution_channel,
        hc.attribution_channel_group,
        hc.first_touch_campaign,
        hc.last_touch_campaign,
        hc.contact_created_at,
        hc.days_since_creation,
        hc.contact_age_category,
        
        -- Associated deals
        coalesce(count(distinct hd.hubspot_deal_id), 0) as associated_deals,
        coalesce(sum(hd.deal_amount_usd), 0) as associated_deal_value,
        coalesce(sum(case when hd.deal_status = 'closed_won' then hd.deal_amount_usd else 0 end), 0) as won_deal_value
        
    from {{ ref('stg_hubspot__contacts') }} hc
    left join {{ ref('stg_hubspot__deals') }} hd on hc.hubspot_contact_id::varchar = hd.deal_owner_id  -- Simplified join
    group by 
        hc.hubspot_contact_id,
        hc.contact_email,
        hc.company_name,
        hc.lifecycle_stage,
        hc.lead_status,
        hc.hubspot_score,
        hc.primary_attribution_channel,
        hc.attribution_channel_group,
        hc.first_touch_campaign,
        hc.last_touch_campaign,
        hc.contact_created_at,
        hc.days_since_creation,
        hc.contact_age_category
),

channel_performance as (
    select
        attribution_channel_group,
        attribution_channel,
        count(distinct campaign_key) as active_campaigns,
        sum(total_spend) as total_channel_spend,
        sum(total_impressions) as total_channel_impressions,
        sum(total_clicks) as total_channel_clicks,
        sum(total_conversions) as total_channel_conversions,
        sum(total_conversion_value) as total_channel_conversion_value,
        sum(attributed_contacts) as total_attributed_contacts,
        sum(attributed_deals) as total_attributed_deals,
        sum(attributed_deal_value) as total_attributed_deal_value,
        sum(won_deals) as total_won_deals,
        sum(won_deal_value) as total_won_deal_value,
        
        -- Channel-level calculated metrics
        case 
            when sum(total_impressions) > 0 
            then sum(total_clicks)::numeric / sum(total_impressions)
            else 0
        end as channel_ctr,
        
        case 
            when sum(total_clicks) > 0 
            then sum(total_spend) / sum(total_clicks)
            else 0
        end as channel_cpc,
        
        case 
            when sum(total_conversions) > 0 
            then sum(total_spend) / sum(total_conversions)
            else 0
        end as channel_cpa,
        
        case 
            when sum(total_spend) > 0 
            then sum(total_conversion_value) / sum(total_spend)
            else 0
        end as channel_roas,
        
        case 
            when sum(total_spend) > 0 
            then sum(won_deal_value) / sum(total_spend)
            else 0
        end as channel_pipeline_roi,
        
        case 
            when sum(attributed_deals) > 0 
            then sum(won_deals)::numeric / sum(attributed_deals)
            else 0
        end as channel_deal_win_rate
        
    from campaign_performance
    group by attribution_channel_group, attribution_channel
),

monthly_trends as (
    select
        date_trunc('month', ecd.snapshot_date) as month_start,
        attribution_channel,
        attribution_channel_group,
        campaign_name,
        sum(daily_spend) as monthly_spend,
        sum(daily_impressions) as monthly_impressions,
        sum(daily_clicks) as monthly_clicks,
        sum(daily_conversions) as monthly_conversions,
        sum(daily_conversion_value) as monthly_conversion_value,
        avg(daily_roas) as avg_monthly_roas,
        
        -- Month-over-month changes
        lag(sum(daily_spend)) over (
            partition by attribution_channel, campaign_name 
            order by date_trunc('month', ecd.snapshot_date)
        ) as prev_month_spend,
        
        lag(sum(daily_conversions)) over (
            partition by attribution_channel, campaign_name 
            order by date_trunc('month', ecd.snapshot_date)
        ) as prev_month_conversions
        
    from {{ ref('entity_campaigns_daily') }} ecd
    where ecd.data_date >= current_date - 365  -- Last year of data
    group by 
        date_trunc('month', ecd.snapshot_date),
        attribution_channel,
        attribution_channel_group,
        campaign_name
),

final as (
    select
        -- Campaign Performance Summary
        'campaign_performance' as mart_section,
        cp.campaign_key,
        cp.source_campaign_id,
        cp.marketing_channel,
        cp.attribution_channel,
        cp.attribution_channel_group,
        cp.campaign_name,
        cp.campaign_category,
        cp.audience_type,
        cp.campaign_status,
        cp.total_spend,
        cp.total_impressions,
        cp.total_clicks,
        cp.total_conversions,
        cp.total_conversion_value,
        cp.overall_click_through_rate as ctr,
        cp.overall_cost_per_click as cpc,
        cp.overall_cost_per_acquisition as cpa,
        cp.overall_return_on_ad_spend as roas,
        cp.avg_order_value,
        cp.attributed_contacts,
        cp.attributed_deals,
        cp.attributed_deal_value,
        cp.won_deals,
        cp.won_deal_value,
        cp.deal_win_rate,
        cp.pipeline_roi,
        cp.spend_tier,
        cp.roas_performance,
        cp.pipeline_performance,
        cp.campaign_performance_score,
        cp.campaign_created_at,
        cp.campaign_age_days,
        cp.latest_data_date,
        null::varchar as contact_email,
        null::varchar as company_name,
        null::varchar as lifecycle_stage,
        null::numeric as hubspot_score,
        null::date as month_start,
        null::numeric as monthly_spend,
        null::numeric as monthly_conversions,
        null::numeric as spend_change_mom,
        null::numeric as conversion_change_mom
        
    from campaign_performance cp
    
    union all
    
    select
        -- Contact Attribution Analysis
        'contact_attribution' as mart_section,
        null::varchar as campaign_key,
        null::varchar as source_campaign_id,
        ca.primary_attribution_channel as marketing_channel,
        ca.primary_attribution_channel as attribution_channel,
        ca.attribution_channel_group,
        ca.first_touch_campaign as campaign_name,
        null::varchar as campaign_category,
        null::varchar as audience_type,
        null::varchar as campaign_status,
        null::numeric as total_spend,
        null::bigint as total_impressions,
        null::bigint as total_clicks,
        null::bigint as total_conversions,
        null::numeric as total_conversion_value,
        null::numeric as ctr,
        null::numeric as cpc,
        null::numeric as cpa,
        null::numeric as roas,
        null::numeric as avg_order_value,
        1 as attributed_contacts,  -- Each row represents one contact
        ca.associated_deals as attributed_deals,
        ca.associated_deal_value as attributed_deal_value,
        case when ca.won_deal_value > 0 then 1 else 0 end as won_deals,
        ca.won_deal_value,
        case when ca.associated_deals > 0 then ca.won_deal_value / ca.associated_deal_value else 0 end as deal_win_rate,
        null::numeric as pipeline_roi,
        null::varchar as spend_tier,
        null::varchar as roas_performance,
        null::varchar as pipeline_performance,
        null::numeric as campaign_performance_score,
        ca.contact_created_at as campaign_created_at,
        ca.days_since_creation as campaign_age_days,
        null::date as latest_data_date,
        ca.contact_email,
        ca.company_name,
        ca.lifecycle_stage,
        ca.hubspot_score,
        null::date as month_start,
        null::numeric as monthly_spend,
        null::numeric as monthly_conversions,
        null::numeric as spend_change_mom,
        null::numeric as conversion_change_mom
        
    from contact_attribution ca
    
    union all
    
    select
        -- Monthly Trends Analysis
        'monthly_trends' as mart_section,
        null::varchar as campaign_key,
        null::varchar as source_campaign_id,
        mt.attribution_channel as marketing_channel,
        mt.attribution_channel,
        mt.attribution_channel_group,
        mt.campaign_name,
        null::varchar as campaign_category,
        null::varchar as audience_type,
        null::varchar as campaign_status,
        null::numeric as total_spend,
        mt.monthly_impressions as total_impressions,
        mt.monthly_clicks as total_clicks,
        mt.monthly_conversions as total_conversions,
        mt.monthly_conversion_value as total_conversion_value,
        case when mt.monthly_impressions > 0 then mt.monthly_clicks::numeric / mt.monthly_impressions else 0 end as ctr,
        case when mt.monthly_clicks > 0 then mt.monthly_spend / mt.monthly_clicks else 0 end as cpc,
        case when mt.monthly_conversions > 0 then mt.monthly_spend / mt.monthly_conversions else 0 end as cpa,
        mt.avg_monthly_roas as roas,
        case when mt.monthly_conversions > 0 then mt.monthly_conversion_value / mt.monthly_conversions else 0 end as avg_order_value,
        null::bigint as attributed_contacts,
        null::bigint as attributed_deals,
        null::numeric as attributed_deal_value,
        null::bigint as won_deals,
        null::numeric as won_deal_value,
        null::numeric as deal_win_rate,
        null::numeric as pipeline_roi,
        null::varchar as spend_tier,
        null::varchar as roas_performance,
        null::varchar as pipeline_performance,
        null::numeric as campaign_performance_score,
        null::timestamp as campaign_created_at,
        null::bigint as campaign_age_days,
        null::date as latest_data_date,
        null::varchar as contact_email,
        null::varchar as company_name,
        null::varchar as lifecycle_stage,
        null::numeric as hubspot_score,
        mt.month_start,
        mt.monthly_spend,
        mt.monthly_conversions,
        case when mt.prev_month_spend > 0 then (mt.monthly_spend - mt.prev_month_spend) / mt.prev_month_spend else 0 end as spend_change_mom,
        case when mt.prev_month_conversions > 0 then (mt.monthly_conversions - mt.prev_month_conversions)::numeric / mt.prev_month_conversions else 0 end as conversion_change_mom
        
    from monthly_trends mt
)

select * from final
