{{ config(materialized='table') }}

-- Marketing Attribution Analytics
-- Comprehensive multi-channel attribution analysis for marketing optimization

with campaign_performance as (
    select * from {{ ref('entity_campaigns') }}
),

customer_attribution as (
    select
        ec.account_id,
        ec.account_name,
        ec.monthly_recurring_revenue,
        ec.customer_health_score,
        ec.account_created_at,
        
        -- Attribution from HubSpot deals (first-touch)
        hd.analytics_source as first_touch_channel,
        hd.campaign_attribution as first_touch_campaign,
        hd.deal_amount as attributed_deal_value,
        
        -- Customer lifetime value
        ec.monthly_recurring_revenue * 12 as annual_contract_value,
        
        -- Time to conversion (estimate)
        extract(days from (ec.subscription_created_at - ec.account_created_at)) as days_to_conversion
        
    from {{ ref('entity_customers') }} ec
    left join {{ ref('stg_hubspot__deals') }} hd on ec.account_id = hd.account_id
    where hd.deal_stage = 'closedwon'
      or hd.deal_stage is null
),

channel_performance_summary as (
    select
        cp.marketing_channel,
        cp.channel_type,
        
        -- Campaign counts
        count(distinct cp.campaign_id) as total_campaigns,
        count(distinct case when cp.campaign_status = 'active' then cp.campaign_id end) as active_campaigns,
        
        -- Investment metrics
        sum(cp.total_cost_usd) as total_spend,
        sum(cp.cost_last_7d) as spend_last_7d,
        avg(cp.avg_daily_spend) as avg_daily_spend_per_campaign,
        
        -- Performance metrics
        sum(cp.total_impressions) as total_impressions,
        sum(cp.total_clicks) as total_clicks,
        sum(cp.total_conversions) as total_conversions,
        sum(cp.total_conversion_value_usd) as total_conversion_value,
        
        -- Email-specific metrics
        sum(cp.emails_sent_30d) as total_emails_sent,
        sum(cp.email_opens_30d) as total_email_opens,
        sum(cp.email_clicks_30d) as total_email_clicks,
        
        -- Attribution metrics
        sum(cp.hubspot_attributed_deals) as total_attributed_deals,
        sum(cp.hubspot_attributed_value) as total_attributed_value,
        sum(cp.hubspot_won_deals) as total_won_deals,
        sum(cp.hubspot_won_value) as total_won_value,
        
        -- Blended performance
        sum(cp.total_attributed_revenue) as total_attributed_revenue,
        avg(cp.blended_return_on_ad_spend) as avg_blended_roas,
        
        -- Performance distribution
        count(case when cp.performance_tier = 'high_performing' then 1 end) as high_performing_campaigns,
        count(case when cp.performance_tier = 'good_performing' then 1 end) as good_performing_campaigns,
        count(case when cp.performance_tier = 'underperforming' then 1 end) as underperforming_campaigns
        
    from campaign_performance cp
    group by cp.marketing_channel, cp.channel_type
),

customer_acquisition_by_channel as (
    select
        ca.first_touch_channel,
        
        -- Customer acquisition
        count(*) as customers_acquired,
        sum(ca.monthly_recurring_revenue) as total_mrr_acquired,
        sum(ca.annual_contract_value) as total_acv_acquired,
        avg(ca.monthly_recurring_revenue) as avg_mrr_per_customer,
        avg(ca.annual_contract_value) as avg_acv_per_customer,
        
        -- Customer quality
        avg(ca.customer_health_score) as avg_customer_health,
        count(case when ca.customer_health_score >= 0.8 then 1 end) as high_quality_customers,
        
        -- Conversion timeline
        avg(ca.days_to_conversion) as avg_days_to_conversion,
        percentile_cont(0.5) within group (order by ca.days_to_conversion) as median_days_to_conversion
        
    from customer_attribution ca
    where ca.first_touch_channel is not null
    group by ca.first_touch_channel
),

channel_efficiency_analysis as (
    select
        cps.marketing_channel,
        cps.channel_type,
        
        -- Investment and returns
        cps.total_spend,
        cps.total_attributed_revenue,
        cps.total_won_value,
        
        -- Efficiency ratios
        case 
            when cps.total_spend > 0 
            then cps.total_attributed_revenue / cps.total_spend
            else 0
        end as overall_roas,
        
        case 
            when cps.total_spend > 0 
            then cps.total_won_value / cps.total_spend
            else 0
        end as closed_won_roas,
        
        -- Cost metrics
        case 
            when cps.total_clicks > 0 
            then cps.total_spend / cps.total_clicks
            else 0
        end as avg_cost_per_click,
        
        case 
            when cps.total_conversions > 0 
            then cps.total_spend / cps.total_conversions
            else 0
        end as avg_cost_per_conversion,
        
        case 
            when cps.total_won_deals > 0 
            then cps.total_spend / cps.total_won_deals
            else 0
        end as avg_cost_per_customer,
        
        -- Engagement rates
        case 
            when cps.total_impressions > 0 
            then cps.total_clicks / cps.total_impressions::decimal
            else 0
        end as overall_ctr,
        
        case 
            when cps.total_emails_sent > 0 
            then cps.total_email_opens / cps.total_emails_sent::decimal
            else null
        end as email_open_rate,
        
        case 
            when cps.total_email_opens > 0 
            then cps.total_email_clicks / cps.total_email_opens::decimal
            else null
        end as email_ctr,
        
        -- Performance scoring
        case 
            when cps.marketing_channel = 'google_ads' and cps.overall_roas >= 4.0 then 'excellent'
            when cps.marketing_channel = 'meta_ads' and cps.overall_roas >= 3.0 then 'excellent'
            when cps.marketing_channel = 'linkedin_ads' and cps.closed_won_roas >= 2.0 then 'excellent'
            when cps.overall_roas >= 2.0 then 'good'
            when cps.overall_roas >= 1.0 then 'acceptable'
            else 'needs_improvement'
        end as channel_performance_grade
        
    from channel_performance_summary cps
),

final as (
    select
        -- Channel identification
        cea.marketing_channel,
        cea.channel_type,
        
        -- Investment metrics
        cea.total_spend,
        cea.total_spend / nullif(
            sum(cea.total_spend) over(), 0
        ) as spend_share,
        
        -- Revenue attribution
        cea.total_attributed_revenue,
        cea.total_won_value,
        cea.overall_roas,
        cea.closed_won_roas,
        
        -- Cost efficiency
        cea.avg_cost_per_click,
        cea.avg_cost_per_conversion,
        cea.avg_cost_per_customer,
        
        -- Customer acquisition
        coalesce(cabc.customers_acquired, 0) as customers_acquired,
        coalesce(cabc.total_mrr_acquired, 0) as total_mrr_acquired,
        coalesce(cabc.avg_mrr_per_customer, 0) as avg_mrr_per_customer,
        coalesce(cabc.avg_customer_health, 0) as avg_customer_health,
        
        -- Customer lifetime value
        case 
            when cabc.customers_acquired > 0 and cea.avg_cost_per_customer > 0
            then (cabc.avg_mrr_per_customer * 24) / cea.avg_cost_per_customer  -- 2-year LTV/CAC
            else 0
        end as ltv_cac_ratio,
        
        -- Conversion metrics
        cabc.avg_days_to_conversion,
        cabc.median_days_to_conversion,
        
        -- Engagement performance
        cea.overall_ctr,
        cea.email_open_rate,
        cea.email_ctr,
        
        -- Campaign portfolio
        cps.total_campaigns,
        cps.active_campaigns,
        cps.high_performing_campaigns,
        cps.good_performing_campaigns,
        cps.underperforming_campaigns,
        
        -- Performance classification
        cea.channel_performance_grade,
        
        -- Optimization recommendations
        case 
            when cea.overall_roas >= 5.0 then 'scale_aggressively'
            when cea.overall_roas >= 3.0 and cea.channel_performance_grade = 'excellent' then 'increase_investment'
            when cea.overall_roas >= 2.0 then 'maintain_optimize'
            when cea.overall_roas >= 1.0 then 'optimize_before_scaling'
            when cea.overall_roas >= 0.5 then 'reduce_investment'
            else 'consider_pausing'
        end as investment_recommendation,
        
        -- Channel-specific insights
        case 
            when cea.marketing_channel = 'google_ads' then
                case 
                    when cea.avg_cost_per_click > 10 then 'focus_on_keyword_optimization'
                    when cea.overall_ctr < 0.02 then 'improve_ad_copy'
                    else 'optimize_landing_pages'
                end
            when cea.marketing_channel = 'meta_ads' then
                case 
                    when cea.overall_ctr < 0.015 then 'refresh_creative_assets'
                    when cea.avg_cost_per_conversion > 200 then 'refine_audience_targeting'
                    else 'test_new_ad_formats'
                end
            when cea.marketing_channel = 'linkedin_ads' then
                case 
                    when cabc.avg_days_to_conversion > 60 then 'nurture_campaign_needed'
                    when cea.avg_cost_per_click > 15 then 'narrow_targeting'
                    else 'expand_content_offerings'
                end
            else 'monitor_and_optimize'
        end as tactical_recommendation,
        
        -- Market share and competitive position
        cea.total_spend / nullif(
            sum(cea.total_spend) over(), 0
        ) * 100 as budget_allocation_pct,
        
        -- ROI ranking
        row_number() over (order by cea.overall_roas desc) as roas_rank,
        row_number() over (order by cea.avg_cost_per_customer asc) as efficiency_rank,
        
        -- Metadata
        current_timestamp as mart_updated_at
        
    from channel_efficiency_analysis cea
    left join channel_performance_summary cps 
        on cea.marketing_channel = cps.marketing_channel 
        and cea.channel_type = cps.channel_type
    left join customer_acquisition_by_channel cabc 
        on cea.marketing_channel = cabc.first_touch_channel
)

select * from final
order by overall_roas desc, total_spend desc
