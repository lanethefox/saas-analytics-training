{{ config(
    materialized='incremental',
    unique_key=['feature_name', 'month_start_date'],
    on_schema_change='sync_all_columns',
    partition_by={
        'field': 'month_start_date',
        'data_type': 'date'
    },
    cluster_by=['feature_name', 'month_start_date'],
    indexes=[
        {'columns': ['feature_name', 'month_start_date'], 'unique': True},
        {'columns': ['month_start_date']},
        {'columns': ['feature_category']}
    ]
) }}

-- Entity: Features (Monthly Strategic Grain)
-- Monthly feature performance for product planning and strategic decision-making
-- Supports product strategy, roadmap prioritization, and customer value assessment

{% if is_incremental() %}
    {% set lookback_days = 35 %}
{% else %}
    {% set lookback_days = 365 %}
{% endif %}

with date_spine as (
    select distinct
        date_trunc('month', series_date)::date as month_start_date,
        (date_trunc('month', series_date) + interval '1 month' - interval '1 day')::date as month_end_date
    from (
        select generate_series(
            current_date - interval '{{ lookback_days }} days',
            current_date,
            '1 day'::interval
        )::date as series_date
    ) dates
    where date_trunc('month', series_date)::date < date_trunc('month', current_date)
),

feature_base as (
    select distinct
        feature_name,
        feature_key,
        feature_category,
        first_usage_date
    from {{ ref('entity_features') }}
),

-- Get monthly feature usage
monthly_usage as (
    select
        feature_name,
        date_trunc('month', usage_timestamp)::date as month_start_date,
        count(distinct account_id) as monthly_accounts,
        count(distinct user_id) as monthly_users,
        count(*) as monthly_usage_events,
        count(distinct date(usage_timestamp)) as active_days,
        sum(usage_count) as total_usage_count
    from {{ ref('stg_app_database__feature_usage') }}
    where usage_timestamp >= current_date - interval '{{ lookback_days }} days'
    group by 1, 2
),

-- Get current feature metrics as reference
feature_metrics as (
    select
        feature_name,
        feature_value_score,
        strategic_importance,
        adoption_stage,
        engagement_level,
        enterprise_stickiness_rate,
        avg_mrr_adopters
    from {{ ref('entity_features') }}
),

final as (
    select
        -- Identifiers
        fb.feature_name,
        fb.feature_key,
        fb.feature_category,
        d.month_start_date,
        d.month_end_date,
        
        -- Monthly usage metrics
        coalesce(mu.monthly_accounts, 0) as monthly_accounts,
        coalesce(mu.monthly_users, 0) as monthly_users,
        coalesce(mu.monthly_usage_events, 0) as monthly_usage_events,
        coalesce(mu.active_days, 0) as active_days,
        coalesce(mu.total_usage_count, 0) as total_usage_count,
        
        -- Usage rates
        case 
            when mu.active_days > 0 
            then round(mu.monthly_usage_events::numeric / mu.active_days, 2)
            else 0
        end as avg_daily_usage,
        
        case 
            when mu.monthly_accounts > 0 
            then round(mu.monthly_usage_events::numeric / mu.monthly_accounts, 2)
            else 0
        end as avg_usage_per_account,
        
        -- Adoption growth (placeholder - would calculate from previous month)
        0::numeric as accounts_growth_rate,
        0::numeric as usage_growth_rate,
        
        -- Feature value (from current state as proxy)
        fm.feature_value_score,
        fm.strategic_importance,
        fm.adoption_stage,
        fm.engagement_level,
        
        -- Revenue correlation
        case 
            when mu.monthly_accounts > 0 and fm.avg_mrr_adopters > 0
            then round((mu.monthly_accounts * fm.avg_mrr_adopters)::numeric, 2)
            else 0
        end as estimated_monthly_revenue,
        
        -- Monthly adoption rate (would need total accounts for the month)
        case 
            when mu.monthly_accounts > 0 
            then round(mu.monthly_accounts::numeric / 100, 2) -- Placeholder denominator
            else 0
        end as monthly_adoption_rate,
        
        -- Feature momentum
        case 
            when mu.monthly_usage_events > 1000 and mu.active_days >= 20 then 'high_momentum'
            when mu.monthly_usage_events > 500 and mu.active_days >= 15 then 'growing_momentum'
            when mu.monthly_usage_events > 100 and mu.active_days >= 10 then 'steady_momentum'
            when mu.monthly_usage_events > 0 then 'low_momentum'
            else 'no_momentum'
        end as feature_momentum,
        
        -- Lifecycle stage at month
        case 
            when d.month_start_date < fb.first_usage_date then 'not_yet_released'
            when d.month_start_date < fb.first_usage_date + interval '3 months' then 'introduction'
            when d.month_start_date < fb.first_usage_date + interval '12 months' then 'growth'
            else 'mature'
        end as lifecycle_stage_at_month,
        
        -- Strategic value score (monthly)
        round((
            -- Usage component (40%)
            case 
                when mu.monthly_usage_events > 1000 then 40
                when mu.monthly_usage_events > 500 then 30
                when mu.monthly_usage_events > 100 then 20
                when mu.monthly_usage_events > 0 then 10
                else 0
            end +
            -- Adoption component (30%)
            case 
                when mu.monthly_accounts > 50 then 30
                when mu.monthly_accounts > 20 then 20
                when mu.monthly_accounts > 5 then 10
                else 0
            end +
            -- Value score component (30%)
            fm.feature_value_score * 0.3
        )::numeric, 2) as monthly_strategic_value,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from date_spine d
    cross join feature_base fb
    left join monthly_usage mu 
        on fb.feature_name = mu.feature_name 
        and d.month_start_date = mu.month_start_date
    left join feature_metrics fm 
        on fb.feature_name = fm.feature_name
    where d.month_start_date >= date_trunc('month', fb.first_usage_date)::date
    
    {% if is_incremental() %}
        and d.month_start_date >= current_date - interval '{{ lookback_days }} days'
    {% endif %}
)

select * from final