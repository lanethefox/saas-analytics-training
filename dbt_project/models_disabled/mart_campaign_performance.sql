{{ config(materialized='table') }}

-- Marketing Mart: Campaign Performance Dashboard
-- Unified marketing performance across all channels with attribution analysis
-- Primary users: Marketing managers, growth teams, executives

with campaign_performance as (
    select
        marketing_channel,
        attribution_channel_group,
        campaign_category,
        campaign_status,
        
        -- Performance aggregates
        count(distinct campaign_key) as total_campaigns,
        count(distinct case when campaign_status = 'active' then campaign_key end) as active_campaigns,
        
        sum(total_spend) as total_spend,
        sum(total_impressions) as total_impressions,
        sum(total_clicks) as total_clicks,
        sum(total_conversions) as total_conversions,
        sum(total_conversion_value) as total_conversion_value,
        sum(attributed_contacts) as total_attributed_contacts,
        sum(attributed_deals) as total_attributed_deals,
        sum(attributed_deal_value) as total_attributed_deal_value,
        sum(won_deals) as total_won_deals,
        sum(won_deal_value) as total_won_deal_value,
        
        -- Calculated metrics
        case 
            when sum(total_impressions) > 0 
            then sum(total_clicks)::numeric / sum(total_impressions)
            else 0
        end as overall_ctr,
        
        case 
            when sum(total_clicks) > 0 
            then sum(total_spend) / sum(total_clicks)
            else 0
        end as overall_cpc,
        
        case 
            when sum(total_conversions) > 0 
            then sum(total_spend) / sum(total_conversions)
            else 0
        end as overall_cpa,
        
        case 
            when sum(total_spend) > 0 
            then sum(total_conversion_value) / sum(total_spend)
            else 0
        end as overall_roas,
        
        case 
            when sum(total_spend) > 0 
            then sum(won_deal_value) / sum(total_spend)
            else 0
        end as pipeline_roi,
        
        case 
            when sum(attributed_deals) > 0 
            then sum(won_deals)::numeric / sum(attributed_deals)
            else 0
        end as deal_win_rate,
        
        case 
            when sum(total_attributed_contacts) > 0 
            then sum(total_spend) / sum(total_attributed_contacts)
            else 0
        end as cost_per_contact,
        
        case 
            when sum(attributed_deals) > 0 
            then sum(total_spend) / sum(attributed_deals)
            else 0
        end as cost_per_deal
        
    from {{ ref('entity_campaigns') }}
    group by marketing_channel, attribution_channel_group, campaign_category, campaign_status
),

daily_trends as (
    select
        data_date,
        marketing_channel,
        
        sum(daily_spend) as daily_spend,
        sum(daily_conversions) as daily_conversions,
        avg(daily_roas) as avg_daily_roas,
        
        -- Week-over-week growth
        sum(daily_spend) - lag(sum(daily_spend), 7) over (
            partition by marketing_channel 
            order by data_date
        ) as spend_wow_change,
        
        sum(daily_conversions) - lag(sum(daily_conversions), 7) over (
            partition by marketing_channel 
            order by data_date
        ) as conversions_wow_change
        
    from {{ ref('entity_campaigns_daily') }}
    where data_date >= current_date - 30
    group by data_date, marketing_channel
),

channel_attribution as (
    select
        attribution_channel_group,
        
        -- Contact journey analysis
        count(distinct hc.hubspot_contact_id) as total_contacts,
        count(distinct case when hd.deal_status = 'closed_won' then hc.hubspot_contact_id end) as converted_contacts,
        
        -- Revenue attribution
        sum(case when hd.deal_status = 'closed_won' then hd.deal_amount_usd else 0 end) as attributed_revenue,
        avg(case when hd.deal_status = 'closed_won' then hd.deal_amount_usd else null end) as avg_deal_size,
        
        -- Time to conversion
        avg(case 
            when hd.deal_status = 'closed_won' and hd.actual_close_date is not null
            then extract(days from (hd.actual_close_date - hc.contact_created_at))
            else null
        end) as avg_days_to_conversion
        
    from {{ ref('stg_hubspot__contacts') }} hc
    left join {{ ref('stg_hubspot__deals') }} hd on hc.hubspot_contact_id::varchar = hd.deal_owner_id
    group by attribution_channel_group
),

top_performing_campaigns as (
    select
        campaign_name,
        marketing_channel,
        campaign_category,
        total_spend,
        total_conversions,
        overall_return_on_ad_spend as roas,
        pipeline_roi,
        
        row_number() over (order by overall_return_on_ad_spend desc) as roas_rank,
        row_number() over (order by pipeline_roi desc) as pipeline_rank,
        row_number() over (order by total_conversions desc) as volume_rank
        
    from {{ ref('entity_campaigns') }}
    where campaign_status = 'active' and total_spend > 1000
),

final as (
    select
        current_date as report_date,
        
        -- Channel performance summary
        cp.marketing_channel,
        cp.attribution_channel_group,
        cp.campaign_category,
        cp.total_campaigns,
        cp.active_campaigns,
        cp.total_spend,
        cp.total_impressions,
        cp.total_clicks,
        cp.total_conversions,
        cp.total_conversion_value,
        cp.overall_ctr,
        cp.overall_cpc,
        cp.overall_cpa,
        cp.overall_roas,
        cp.pipeline_roi,
        cp.deal_win_rate,
        cp.cost_per_contact,
        cp.cost_per_deal,
        
        -- Attribution analysis
        ca.total_contacts as attributed_contacts,
        ca.converted_contacts,
        ca.attributed_revenue,
        ca.avg_deal_size,
        ca.avg_days_to_conversion,
        
        case 
            when ca.total_contacts > 0 
            then ca.converted_contacts::numeric / ca.total_contacts
            else 0
        end as contact_conversion_rate,
        
        -- Performance classification
        case 
            when cp.overall_roas >= 3.0 then 'excellent'
            when cp.overall_roas >= 1.5 then 'good'
            when cp.overall_roas >= 1.0 then 'break_even'
            when cp.overall_roas > 0 then 'poor'
            else 'no_return'
        end as roas_performance_tier,
        
        case 
            when cp.pipeline_roi >= 5.0 then 'excellent'
            when cp.pipeline_roi >= 2.0 then 'good'
            when cp.pipeline_roi >= 1.0 then 'moderate'
            when cp.pipeline_roi > 0 then 'weak'
            else 'no_pipeline'
        end as pipeline_performance_tier,
        
        case 
            when cp.overall_ctr >= 0.05 then 'high'
            when cp.overall_ctr >= 0.02 then 'medium'
            when cp.overall_ctr >= 0.01 then 'low'
            else 'very_low'
        end as engagement_tier,
        
        -- Budget allocation recommendations
        case 
            when cp.overall_roas >= 2.0 and cp.pipeline_roi >= 3.0 then 'increase_budget'
            when cp.overall_roas >= 1.5 and cp.pipeline_roi >= 2.0 then 'maintain_budget'
            when cp.overall_roas >= 1.0 then 'optimize_campaigns'
            when cp.overall_roas < 1.0 and cp.total_spend > 5000 then 'reduce_or_pause'
            else 'test_further'
        end as budget_recommendation,
        
        -- Market opportunity indicators
        case 
            when cp.total_impressions > 1000000 and cp.overall_ctr < 0.02 then 'creative_optimization'
            when cp.overall_ctr > 0.03 and cp.overall_roas < 1.5 then 'landing_page_optimization'
            when ca.avg_days_to_conversion > 90 then 'nurture_improvement'
            when cp.deal_win_rate < 0.2 and cp.total_attributed_deals > 10 then 'sales_process_optimization'
            else 'standard'
        end as optimization_opportunity,
        
        current_timestamp as _mart_created_at
        
    from campaign_performance cp
    left join channel_attribution ca on cp.attribution_channel_group = ca.attribution_channel_group
    where cp.total_spend > 0  -- Only include channels with spend
)

select * from final
