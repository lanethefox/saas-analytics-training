-- Test entity_subscriptions for subscription lifecycle integrity
WITH subscription_validation AS (
    SELECT 
        COUNT(*) AS total_subscriptions,
        COUNT(DISTINCT subscription_id) AS unique_subscriptions,
        SUM(CASE WHEN monthly_recurring_revenue < 0 THEN 1 ELSE 0 END) AS negative_mrr,
        SUM(CASE WHEN churn_risk_score < 0 OR churn_risk_score > 100 THEN 1 ELSE 0 END) AS invalid_churn_risk,
        SUM(CASE WHEN payment_health_score < 0 OR payment_health_score > 100 THEN 1 ELSE 0 END) AS invalid_payment_health,
        SUM(CASE WHEN subscription_status NOT IN ('active', 'cancelled', 'trial', 'past_due', 'paused') THEN 1 ELSE 0 END) AS invalid_status
    FROM {{ ref('entity_subscriptions') }}
),
lifecycle_consistency AS (
    -- Check lifecycle stage consistency
    SELECT 
        COUNT(*) AS inconsistent_lifecycle
    FROM {{ ref('entity_subscriptions') }}
    WHERE (lifecycle_stage = 'trial' AND subscription_status != 'trial')
       OR (lifecycle_stage = 'churned' AND subscription_status != 'cancelled')
       OR (lifecycle_stage = 'active' AND subscription_status NOT IN ('active', 'past_due'))
),
risk_validation AS (
    -- High churn risk should correlate with payment issues or low usage
    SELECT 
        COUNT(*) AS inconsistent_risk_factors
    FROM {{ ref('entity_subscriptions') }}
    WHERE churn_risk_score > 80
      AND payment_health_score > 90
      AND usage_health_score > 90
),
revenue_validation AS (
    -- Validate revenue calculations
    SELECT 
        COUNT(*) AS invalid_revenue_calcs
    FROM {{ ref('entity_subscriptions') }}
    WHERE (subscription_status = 'active' AND monthly_recurring_revenue = 0)
       OR (subscription_status = 'cancelled' AND monthly_recurring_revenue > 0)
       OR (annual_recurring_revenue != monthly_recurring_revenue * 12 AND ABS(annual_recurring_revenue - monthly_recurring_revenue * 12) > 0.01)
),
invalid_data AS (
    SELECT 
        v.*,
        lc.inconsistent_lifecycle,
        rv.inconsistent_risk_factors,
        rev.invalid_revenue_calcs
    FROM subscription_validation v
    CROSS JOIN lifecycle_consistency lc
    CROSS JOIN risk_validation rv
    CROSS JOIN revenue_validation rev
    WHERE v.negative_mrr > 0
       OR v.invalid_churn_risk > 0
       OR v.invalid_payment_health > 0
       OR v.invalid_status > 0
       OR lc.inconsistent_lifecycle > 0
       OR rv.inconsistent_risk_factors > 0
       OR rev.invalid_revenue_calcs > 0
)
-- Test fails if subscription entity data is invalid
SELECT * FROM invalid_data