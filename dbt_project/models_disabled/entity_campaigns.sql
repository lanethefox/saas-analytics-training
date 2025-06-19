{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Entity: Campaigns (Atomic View)
-- Current-state campaign view with real-time performance metrics and attribution
-- Primary use cases: Marketing optimization, budget allocation, campaign management

with campaign_core as (
    select * from {{ ref('int_campaigns__core') }}
),

latest_performance as (
    select
        campaign_key,
        marketing_channel,
        max(data_date) as latest_data_date,
        sum(spend_usd) as total_spend,
        sum(impressions) as total_impressions,
        sum(clicks) as total_clicks,
        sum(conversions) as total_conversions,
        sum(conversion_value_usd) as total_conversion_value,
        avg(click_through_rate) as avg_click_through_rate,
        avg(cost_per_click) as avg_cost_per_click,
        avg(cost_per_acquisition) as avg_cost_per_acquisition,
        avg(return_on_ad_spend) as avg_return_on_ad_spend
    from campaign_core
    where data_date >= current_date - 30  -- Last 30 days performance
    group by campaign_key, marketing_channel
),

attribution_summary as (
    select
        cc.campaign_key,
        count(distinct hc.hubspot_contact_id) as attributed_contacts,
        count(distinct hd.hubspot_deal_id) as attributed_deals,
        sum(hd.deal_amount_usd) as attributed_deal_value,
        count(distinct case when hd.deal_status = 'closed_won' then hd.hubspot_deal_id end) as won_deals,
        sum(case when hd.deal_status = 'closed_won' then hd.deal_amount_usd else 0 end) as won_deal_value
    from campaign_core cc
    left join {{ ref('stg_hubspot__contacts') }} hc 
        on lower(cc.attribution_channel) = hc.primary_attribution_channel
        and hc.first_touch_campaign = cc.campaign_name
    left join {{ ref('stg_hubspot__deals') }} hd 
        on hc.hubspot_contact_id::varchar = hd.deal_owner_id  -- Simplified attribution
    group by cc.campaign_key
),

final as (
    select
        -- Core identifiers and attributes
        cc.campaign_key,
        cc.source_campaign_id,
        cc.marketing_channel,
        cc.attribution_channel,
        cc.attribution_channel_group,
        cc.campaign_name,
        cc.campaign_type,
        cc.campaign_status,
        cc.campaign_category,
        cc.audience_type,
        
        -- Performance metrics (lifetime)
        lp.total_spend,
        lp.total_impressions,
        lp.total_clicks,
        lp.total_conversions,
        lp.total_conversion_value,
        
        -- Calculated performance metrics
        case 
            when lp.total_impressions > 0 then lp.total_clicks::numeric / lp.total_impressions
            else 0
        end as overall_click_through_rate,
        
        case 
            when lp.total_clicks > 0 then lp.total_spend / lp.total_clicks
            else 0
        end as overall_cost_per_click,
        
        case 
            when lp.total_conversions > 0 then lp.total_spend / lp.total_conversions
            else 0
        end as overall_cost_per_acquisition,
        
        case 
            when lp.total_spend > 0 then lp.total_conversion_value / lp.total_spend
            else 0
        end as overall_return_on_ad_spend,
        
        case 
            when lp.total_conversions > 0 then lp.total_conversion_value / lp.total_conversions
            else 0
        end as avg_order_value,
        
        -- Attribution metrics
        coalesce(att.attributed_contacts, 0) as attributed_contacts,
        coalesce(att.attributed_deals, 0) as attributed_deals,
        coalesce(att.attributed_deal_value, 0) as attributed_deal_value,
        coalesce(att.won_deals, 0) as won_deals,
        coalesce(att.won_deal_value, 0) as won_deal_value,
        
        case 
            when att.attributed_deals > 0 then att.won_deals::numeric / att.attributed_deals
            else 0
        end as deal_win_rate,
        
        case 
            when lp.total_spend > 0 then att.won_deal_value / lp.total_spend
            else 0
        end as pipeline_roi,
        
        -- Performance classifications
        cc.media_type,
        cc.is_paid_acquisition,
        
        case 
            when lp.total_spend >= 10000 then 'high_budget'
            when lp.total_spend >= 2500 then 'medium_budget'
            when lp.total_spend >= 500 then 'low_budget'
            when lp.total_spend > 0 then 'minimal_budget'
            else 'no_spend'
        end as spend_tier,
        
        case 
            when overall_return_on_ad_spend >= 4.0 then 'excellent_roas'
            when overall_return_on_ad_spend >= 2.0 then 'good_roas'
            when overall_return_on_ad_spend >= 1.0 then 'break_even_roas'
            when overall_return_on_ad_spend > 0 then 'poor_roas'
            else 'no_roas'
        end as roas_performance,
        
        case 
            when pipeline_roi >= 10.0 then 'excellent_pipeline'
            when pipeline_roi >= 5.0 then 'good_pipeline'
            when pipeline_roi >= 2.0 then 'moderate_pipeline'
            when pipeline_roi > 0 then 'weak_pipeline'
            else 'no_pipeline'
        end as pipeline_performance,
        
        -- Campaign health scoring
        case 
            when cc.campaign_status = 'active' 
                and overall_return_on_ad_spend >= 2.0
                and overall_click_through_rate >= 0.02
                and lp.total_conversions >= 10
            then 0.95
            when cc.campaign_status = 'active' 
                and overall_return_on_ad_spend >= 1.0
                and overall_click_through_rate >= 0.01
                and lp.total_conversions >= 5
            then 0.75
            when cc.campaign_status = 'active' 
                and lp.total_conversions >= 1
            then 0.5
            when cc.campaign_status = 'active'
            then 0.25
            else 0.0
        end as campaign_performance_score,
        
        -- Efficiency metrics
        case 
            when lp.total_clicks > 0 then lp.total_conversions::numeric / lp.total_clicks
            else 0
        end as conversion_rate,
        
        case 
            when att.attributed_contacts > 0 then lp.total_spend / att.attributed_contacts
            else 0
        end as cost_per_attributed_contact,
        
        case 
            when att.attributed_deals > 0 then lp.total_spend / att.attributed_deals
            else 0
        end as cost_per_attributed_deal,
        
        -- Temporal attributes
        cc.campaign_created_at,
        cc.campaign_modified_at,
        lp.latest_data_date,
        
        extract(days from (current_date - cc.campaign_created_at::date)) as campaign_age_days,
        extract(days from (current_date - lp.latest_data_date)) as days_since_last_data,
        
        -- Campaign lifecycle indicators
        case 
            when cc.campaign_status = 'paused' and lp.latest_data_date < current_date - 7 then 'inactive'
            when cc.campaign_status = 'ended' then 'completed'
            when lp.latest_data_date < current_date - 3 then 'stale_data'
            when cc.campaign_status = 'active' then 'running'
            else 'unknown'
        end as campaign_lifecycle_status,
        
        -- Metadata
        current_timestamp as entity_updated_at
        
    from campaign_core cc
    left join latest_performance lp on cc.campaign_key = lp.campaign_key
    left join attribution_summary att on cc.campaign_key = att.campaign_key
)

select * from final
