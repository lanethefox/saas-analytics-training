{{ config(
    materialized='table',
    indexes=[
        {'columns': ['campaign_id'], 'unique': True},
        {'columns': ['platform']},
        {'columns': ['campaign_status']},
        {'columns': ['performance_tier']},
        {'columns': ['total_spend']}
    ]
) }}

-- Entity: Campaigns (Atomic/Current State)
-- Attribution focus capturing spend, conversion rates, and attribution metrics
-- Provides comprehensive view of current campaign performance for marketing optimization

with campaign_core as (
    select * from {{ ref('int_campaigns__core') }}
),

campaign_attribution as (
    select * from {{ ref('int_campaigns__attribution') }}
),

final as (
    select
        -- Primary identifiers
        cc.campaign_key,
        cc.campaign_id,
        cc.platform,
        
        -- Campaign details
        cc.campaign_name,
        cc.campaign_type,
        cc.campaign_status,
        cc.is_active,
        cc.campaign_lifecycle_stage,
        
        -- Campaign timeline
        cc.campaign_created_at,
        cc.campaign_updated_at,
        cc.start_date,
        cc.end_date,
        cc.days_active,
        
        -- Performance metrics
        cc.total_spend,
        cc.impressions,
        cc.clicks,
        cc.conversions,
        cc.conversion_value,
        
        -- Calculated rates
        cc.click_through_rate,
        cc.conversion_rate,
        cc.cost_per_conversion,
        cc.cost_per_click,
        cc.cost_per_thousand_impressions,
        cc.roi_percentage,
        
        -- Performance classification
        cc.performance_tier,
        
        -- Attribution metrics
        coalesce(ca.total_leads_touched, 0) as total_leads_touched,
        coalesce(ca.converted_leads, 0) as converted_leads,
        coalesce(ca.lead_conversion_rate, 0) as lead_conversion_rate,
        
        -- Multi-touch attribution conversions
        coalesce(ca.first_touch_conversions, 0) as first_touch_conversions,
        coalesce(ca.last_touch_conversions, 0) as last_touch_conversions,
        coalesce(ca.linear_conversions, 0) as linear_conversions,
        coalesce(ca.time_decay_conversions, 0) as time_decay_conversions,
        coalesce(ca.position_based_conversions, 0) as position_based_conversions,
        
        -- Cost per acquisition by attribution model
        ca.first_touch_cpa,
        ca.last_touch_cpa,
        ca.linear_cpa,
        ca.time_decay_cpa,
        ca.position_based_cpa,
        
        -- Attribution patterns
        coalesce(ca.attribution_pattern, 'no_attribution') as attribution_pattern,
        coalesce(ca.attribution_performance, 'no_conversions') as attribution_performance,
        
        -- Touchpoint metrics
        coalesce(ca.avg_touchpoints_per_lead, 0) as avg_touchpoints_per_lead,
        coalesce(ca.first_touches, 0) as first_touches,
        coalesce(ca.last_touches, 0) as last_touches,
        coalesce(ca.total_touchpoints, 0) as total_touchpoints,
        
        -- Campaign targeting
        cc.target_audience,
        cc.target_location,
        cc.bid_strategy,
        
        -- Performance scoring (composite of efficiency and effectiveness)
        case 
            when cc.total_spend > 0 and ca.linear_conversions > 0 then
                round((
                    -- Efficiency component (40%)
                    (case 
                        when cc.cost_per_conversion < 50 then 100
                        when cc.cost_per_conversion < 100 then 80
                        when cc.cost_per_conversion < 200 then 60
                        when cc.cost_per_conversion < 500 then 40
                        else 20
                    end * 0.4) +
                    -- Effectiveness component (40%)
                    (case 
                        when cc.conversion_rate > 5 then 100
                        when cc.conversion_rate > 3 then 80
                        when cc.conversion_rate > 1.5 then 60
                        when cc.conversion_rate > 0.5 then 40
                        else 20
                    end * 0.4) +
                    -- Scale component (20%)
                    (case 
                        when ca.converted_leads > 100 then 100
                        when ca.converted_leads > 50 then 80
                        when ca.converted_leads > 20 then 60
                        when ca.converted_leads > 5 then 40
                        else 20
                    end * 0.2)
                )::numeric, 2)
            else 0
        end as performance_score,
        
        -- Budget utilization
        case 
            when cc.is_active and cc.days_active > 0 then
                cc.total_spend / cc.days_active
            else 0
        end as daily_spend_rate,
        
        -- Optimization opportunities
        case 
            when cc.click_through_rate < 1 and cc.impressions > 10000 then 'improve_creative'
            when cc.conversion_rate < 1 and cc.clicks > 100 then 'improve_landing_page'
            when cc.cost_per_conversion > 200 and ca.avg_touchpoints_per_lead > 5 then 'simplify_journey'
            when cc.roi_percentage < 0 then 'reassess_strategy'
            else 'maintain_course'
        end as optimization_recommendation,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from campaign_core cc
    left join campaign_attribution ca on cc.campaign_key = ca.campaign_key
)

select * from final