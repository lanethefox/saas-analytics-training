{{ config(
    materialized='incremental',
    unique_key=['subscription_id', 'month_start_date'],
    on_schema_change='sync_all_columns',
    partition_by={
        'field': 'month_start_date',
        'data_type': 'date'
    },
    cluster_by=['subscription_id', 'month_start_date'],
    indexes=[
        {'columns': ['subscription_id', 'month_start_date'], 'unique': True},
        {'columns': ['month_start_date']},
        {'columns': ['account_id']}
    ]
) }}

-- Entity: Subscriptions (Monthly Strategic Grain)
-- Monthly subscription performance for financial reporting and strategic planning
-- Supports SaaS metrics calculation, cohort revenue analysis, and growth accounting

{% if is_incremental() %}
    {% set lookback_days = 35 %}
{% else %}
    {% set lookback_days = 730 %}
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

subscription_base as (
    select distinct
        subscription_id,
        subscription_key,
        account_id,
        subscription_created_at,
        subscription_started_at,
        canceled_at,
        plan_type,
        billing_interval
    from {{ ref('entity_subscriptions') }}
),

-- Get subscription states at each month
subscription_monthly_states as (
    select
        s.subscription_id,
        s.subscription_key,
        s.account_id,
        d.month_start_date,
        d.month_end_date,
        s.plan_type,
        s.billing_interval,
        
        -- Subscription state for the month
        case
            when s.subscription_started_at::date <= d.month_end_date 
                and (s.canceled_at is null or s.canceled_at::date > d.month_end_date)
            then 'active'
            when s.canceled_at::date between d.month_start_date and d.month_end_date
            then 'churned'
            when s.subscription_started_at::date between d.month_start_date and d.month_end_date
            then 'new'
            else 'inactive'
        end as subscription_state,
        
        -- Cohort information
        date_trunc('month', s.subscription_started_at)::date as cohort_month,
        extract(months from age(d.month_start_date, date_trunc('month', s.subscription_started_at))) as months_since_start
        
    from date_spine d
    cross join subscription_base s
    where d.month_start_date >= date_trunc('month', s.subscription_created_at)::date
    
    {% if is_incremental() %}
        and d.month_start_date >= current_date - interval '{{ lookback_days }} days'
    {% endif %}
),

-- Get revenue metrics from current entity table
subscription_revenue as (
    select
        subscription_id,
        monthly_recurring_revenue,
        annual_recurring_revenue,
        payment_health_score,
        churn_risk_score,
        subscription_value_tier,
        risk_classification,
        expansion_opportunity_score
    from {{ ref('entity_subscriptions') }}
),

final as (
    select
        -- Identifiers
        sms.subscription_id,
        sms.subscription_key,
        sms.account_id,
        sms.month_start_date,
        sms.month_end_date,
        
        -- Subscription details
        sms.plan_type,
        sms.billing_interval,
        sms.subscription_state,
        
        -- Revenue metrics (current values as proxy for historical)
        case 
            when sms.subscription_state in ('active', 'churned') 
            then coalesce(sr.monthly_recurring_revenue, 0)
            else 0
        end as monthly_recurring_revenue,
        
        case 
            when sms.subscription_state in ('active', 'churned') 
            then coalesce(sr.annual_recurring_revenue, 0)
            else 0
        end as annual_recurring_revenue,
        
        -- Health metrics
        coalesce(sr.payment_health_score, 0) as payment_health_score,
        coalesce(sr.churn_risk_score, 0) as churn_risk_score,
        coalesce(sr.subscription_value_tier, 'no_value') as subscription_value_tier,
        coalesce(sr.risk_classification, 'unknown') as risk_classification,
        
        -- Growth accounting components
        case 
            when sms.subscription_state = 'new' 
            then coalesce(sr.monthly_recurring_revenue, 0)
            else 0
        end as new_mrr,
        
        case 
            when sms.subscription_state = 'churned' 
            then coalesce(sr.monthly_recurring_revenue, 0)
            else 0
        end as churned_mrr,
        
        -- Expansion/contraction (placeholder - would need historical data)
        0::numeric as expansion_mrr,
        0::numeric as contraction_mrr,
        
        -- Cohort metrics
        sms.cohort_month,
        sms.months_since_start,
        
        -- Retention indicators
        case 
            when sms.subscription_state = 'active' then 1
            else 0
        end as is_retained,
        
        -- Value metrics
        coalesce(sr.expansion_opportunity_score, 0) as expansion_opportunity_score,
        
        -- SaaS metrics support
        case 
            when sms.subscription_state = 'active' then 1
            else 0
        end as active_subscription_count,
        
        case 
            when sms.subscription_state = 'new' then 1
            else 0
        end as new_subscription_count,
        
        case 
            when sms.subscription_state = 'churned' then 1
            else 0
        end as churned_subscription_count,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from subscription_monthly_states sms
    left join subscription_revenue sr on sms.subscription_id = sr.subscription_id
    where sms.subscription_state != 'inactive'
)

select * from final