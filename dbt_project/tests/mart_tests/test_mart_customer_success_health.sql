-- Test mart_customer_success__health for customer health calculations
WITH health_validation AS (
    SELECT 
        COUNT(*) AS total_customers,
        COUNT(DISTINCT account_id) AS unique_customers,
        SUM(CASE WHEN overall_health_score < 0 OR overall_health_score > 100 THEN 1 ELSE 0 END) AS invalid_health_score,
        SUM(CASE WHEN revenue_health < 0 OR revenue_health > 100 THEN 1 ELSE 0 END) AS invalid_revenue_health,
        SUM(CASE WHEN usage_health < 0 OR usage_health > 100 THEN 1 ELSE 0 END) AS invalid_usage_health,
        SUM(CASE WHEN engagement_health < 0 OR engagement_health > 100 THEN 1 ELSE 0 END) AS invalid_engagement_health,
        SUM(CASE WHEN churn_risk_score < 0 OR churn_risk_score > 100 THEN 1 ELSE 0 END) AS invalid_churn_risk
    FROM {{ ref('mart_customer_success__health') }}
),
health_consistency AS (
    -- Check that overall health is reasonable given component scores
    SELECT 
        COUNT(*) AS inconsistent_health
    FROM {{ ref('mart_customer_success__health') }}
    WHERE overall_health_score > GREATEST(revenue_health, usage_health, engagement_health) + 10
       OR overall_health_score < LEAST(revenue_health, usage_health, engagement_health) - 10
),
risk_consistency AS (
    -- High health should mean low churn risk
    SELECT 
        COUNT(*) AS inconsistent_risk
    FROM {{ ref('mart_customer_success__health') }}
    WHERE (overall_health_score > 80 AND churn_risk_score > 70)
       OR (overall_health_score < 30 AND churn_risk_score < 30)
),
action_validation AS (
    -- Verify recommended actions exist for at-risk customers
    SELECT 
        COUNT(*) AS missing_actions
    FROM {{ ref('mart_customer_success__health') }}
    WHERE churn_risk_score > 70
      AND (recommended_action IS NULL OR TRIM(recommended_action) = '')
),
invalid_data AS (
    SELECT 
        v.*,
        hc.inconsistent_health,
        rc.inconsistent_risk,
        av.missing_actions
    FROM health_validation v
    CROSS JOIN health_consistency hc
    CROSS JOIN risk_consistency rc
    CROSS JOIN action_validation av
    WHERE v.invalid_health_score > 0
       OR v.invalid_revenue_health > 0
       OR v.invalid_usage_health > 0
       OR v.invalid_engagement_health > 0
       OR v.invalid_churn_risk > 0
       OR hc.inconsistent_health > 0
       OR rc.inconsistent_risk > 0
       OR av.missing_actions > 0
)
-- Test fails if health calculations are invalid
SELECT * FROM invalid_data