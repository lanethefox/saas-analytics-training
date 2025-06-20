{{ config(
    materialized='incremental',
    unique_key=['campaign_id', 'performance_date'],
    on_schema_change='sync_all_columns',
    partition_by={
        'field': 'performance_date',
        'data_type': 'date'
    },
    cluster_by=['campaign_id', 'performance_date'],
    indexes=[
        {'columns': ['campaign_id', 'performance_date'], 'unique': True},
        {'columns': ['performance_date']},
        {'columns': ['platform']}
    ]
) }}

-- Entity: Campaigns (Daily Strategic Grain)
-- Daily campaign performance for marketing optimization and tactical decision-making
-- Supports daily operations, budget pacing, performance trending, and anomaly detection

{% if is_incremental() %}
    {% set lookback_days = 7 %}
{% else %}
    {% set lookback_days = 90 %}
{% endif %}

with date_spine as (
    select generate_series(
        current_date - interval '{{ lookback_days }} days',
        current_date - interval '1 day',
        '1 day'::interval
    )::date as performance_date
),

campaign_base as (
    select distinct
        campaign_id,
        campaign_key,
        platform,
        campaign_name,
        campaign_type,
        start_date,
        end_date,
        campaign_created_at
    from {{ ref('entity_campaigns') }}
),

-- Generate daily records for active campaigns
campaign_daily_spine as (
    select
        c.campaign_id,
        c.campaign_key,
        c.platform,
        c.campaign_name,
        c.campaign_type,
        d.performance_date
    from date_spine d
    cross join campaign_base c
    where d.performance_date >= c.start_date::date
      and d.performance_date <= coalesce(c.end_date::date, current_date)
      and d.performance_date >= c.campaign_created_at::date
    
    {% if is_incremental() %}
        and d.performance_date >= current_date - interval '{{ lookback_days }} days'
    {% endif %}
),

-- Get current campaign metrics (as proxy for daily metrics)
campaign_metrics as (
    select
        campaign_id,
        total_spend,
        impressions,
        clicks,
        conversions,
        conversion_value,
        click_through_rate,
        conversion_rate,
        cost_per_conversion,
        cost_per_click,
        performance_score,
        performance_tier,
        daily_spend_rate,
        linear_conversions,
        linear_cpa
    from {{ ref('entity_campaigns') }}
),

final as (
    select
        -- Identifiers
        cds.campaign_id,
        cds.campaign_key,
        cds.platform,
        cds.campaign_name,
        cds.campaign_type,
        cds.performance_date,
        
        -- Daily metrics (simulated - in reality would come from daily snapshots)
        -- Using average daily values as proxy
        coalesce(cm.daily_spend_rate, 0) as daily_spend,
        case 
            when cm.total_spend > 0 and cm.impressions > 0 then
                round(cm.impressions * cm.daily_spend_rate / cm.total_spend)::integer
            else 0
        end as daily_impressions,
        
        case 
            when cm.total_spend > 0 and cm.clicks > 0 then
                round(cm.clicks * cm.daily_spend_rate / cm.total_spend)::integer
            else 0
        end as daily_clicks,
        
        case 
            when cm.total_spend > 0 and cm.conversions > 0 then
                round(cm.conversions * cm.daily_spend_rate / cm.total_spend, 2)::numeric
            else 0
        end as daily_conversions,
        
        -- Performance rates (current snapshot)
        cm.click_through_rate,
        cm.conversion_rate,
        cm.cost_per_conversion,
        cm.cost_per_click,
        
        -- Cumulative metrics
        sum(coalesce(cm.daily_spend_rate, 0)) over (
            partition by cds.campaign_id 
            order by cds.performance_date
        ) as cumulative_spend,
        
        -- Day of week patterns
        extract(dow from cds.performance_date) as day_of_week,
        to_char(cds.performance_date, 'Day') as day_name,
        
        -- Performance classification
        cm.performance_score,
        cm.performance_tier,
        
        -- Attribution metrics
        cm.linear_conversions / greatest(date_part('day', age(current_date, cds.performance_date)), 1) as daily_attributed_conversions,
        cm.linear_cpa as attributed_cpa,
        
        -- Budget pacing
        case 
            when cm.daily_spend_rate > 0 then
                'on_pace'
            else 'no_spend'
        end as budget_pacing_status,
        
        -- Trend indicators (placeholder - would calculate from historical data)
        0::numeric as spend_trend_7d,
        0::numeric as performance_trend_7d,
        
        -- Anomaly flags (placeholder - would use statistical methods)
        false as is_spend_anomaly,
        false as is_performance_anomaly,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from campaign_daily_spine cds
    left join campaign_metrics cm on cds.campaign_id = cm.campaign_id
)

select * from final