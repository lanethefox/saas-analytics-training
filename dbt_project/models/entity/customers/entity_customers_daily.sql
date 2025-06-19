{{
    config(
        materialized='incremental',
        unique_key=['account_id', 'snapshot_date'],
        on_schema_change='merge',
        indexes=[
            {'columns': ['snapshot_date']},
            {'columns': ['account_id', 'snapshot_date']}
        ]
    )
}}

-- Entity: Customers (Strategic Grain - Daily) - Simplified
-- Description: Daily snapshots optimized for trend analysis
-- Primary Use Cases: Executive dashboards, board reporting, trend analysis

WITH date_spine AS (
    SELECT 
        generate_series(
            {% if is_incremental() %}
                (SELECT MAX(snapshot_date) FROM {{ this }})::date + interval '1 day',
            {% else %}
                CURRENT_DATE - interval '30 days',
            {% endif %}
            CURRENT_DATE,
            '1 day'::interval
        )::date as snapshot_date
),

current_customers AS (
    SELECT * FROM {{ ref('entity_customers') }}
)

SELECT 
    d.snapshot_date,
    c.account_id,
    c.company_name,
    c.industry,
    c.customer_tier,
    c.customer_status,
    c.created_at,
    c.first_subscription_date,
    c.monthly_recurring_revenue,
    c.active_subscriptions,
    c.total_devices,
    c.device_events_30d,
    c.active_users_30d,
    c.customer_health_score,
    c.churn_risk_score,
    
    -- Calculate customer age at snapshot
    EXTRACT(DAY FROM d.snapshot_date - c.created_at) as customer_lifetime_days,
    
    -- Cohort information
    DATE_TRUNC('month', c.created_at)::date as cohort_month,
    DATE_TRUNC('quarter', c.created_at)::date as cohort_quarter,
    
    -- Period indicators
    EXTRACT(YEAR FROM d.snapshot_date) as snapshot_year,
    EXTRACT(MONTH FROM d.snapshot_date) as snapshot_month,
    EXTRACT(QUARTER FROM d.snapshot_date) as snapshot_quarter,
    EXTRACT(DOW FROM d.snapshot_date) as snapshot_day_of_week,
    
    -- Placeholder metrics for trends
    0 as mrr_daily_change,
    0 as health_score_daily_change,
    0 as mrr_30d_change,
    0 as health_score_30d_change,
    0 as mrr_daily_growth_rate,
    0 as mrr_30d_growth_rate,
    
    c.monthly_recurring_revenue as avg_mrr_30d,
    c.customer_health_score as avg_health_score_30d,
    0 as mrr_volatility_30d,
    c.monthly_recurring_revenue as max_mrr_30d,
    c.monthly_recurring_revenue as min_mrr_30d,
    0 as mrr_range_coefficient_30d,
    
    -- Simple trajectory classifications
    'stable' as health_trajectory_30d,
    'stable' as mrr_trajectory_30d,
    
    -- Technical metadata
    ROW_NUMBER() OVER (PARTITION BY c.account_id ORDER BY d.snapshot_date) as day_sequence,
    CURRENT_TIMESTAMP as last_updated_at
    
FROM date_spine d
CROSS JOIN current_customers c
WHERE d.snapshot_date >= c.created_at::date
  AND d.snapshot_date <= CURRENT_DATE