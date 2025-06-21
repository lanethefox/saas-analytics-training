-- Test int_subscriptions__revenue_metrics for revenue calculations
WITH revenue_validation AS (
    SELECT 
        COUNT(*) AS total_records,
        COUNT(DISTINCT subscription_id) AS unique_subscriptions,
        SUM(CASE WHEN monthly_recurring_revenue < 0 THEN 1 ELSE 0 END) AS negative_mrr,
        SUM(CASE WHEN annual_recurring_revenue < 0 THEN 1 ELSE 0 END) AS negative_arr,
        SUM(CASE WHEN lifetime_value < 0 THEN 1 ELSE 0 END) AS negative_ltv,
        SUM(CASE WHEN churn_probability < 0 OR churn_probability > 1 THEN 1 ELSE 0 END) AS invalid_churn_prob,
        SUM(CASE WHEN discount_percentage < 0 OR discount_percentage > 100 THEN 1 ELSE 0 END) AS invalid_discount
    FROM {{ ref('int_subscriptions__revenue_metrics') }}
),
revenue_consistency AS (
    -- Check ARR = MRR * 12 (with small tolerance for rounding)
    SELECT 
        COUNT(*) AS inconsistent_arr_mrr
    FROM {{ ref('int_subscriptions__revenue_metrics') }}
    WHERE ABS(annual_recurring_revenue - (monthly_recurring_revenue * 12)) > 0.01
      AND monthly_recurring_revenue > 0
),
ltv_validation AS (
    -- LTV should be reasonable compared to MRR and churn
    SELECT 
        COUNT(*) AS unreasonable_ltv
    FROM {{ ref('int_subscriptions__revenue_metrics') }}
    WHERE lifetime_value > (monthly_recurring_revenue * 1000)  -- More than 83 years
       OR (churn_probability > 0.5 AND lifetime_value > monthly_recurring_revenue * 24)  -- High churn but high LTV
),
invalid_metrics AS (
    SELECT 
        v.*,
        c.inconsistent_arr_mrr,
        l.unreasonable_ltv
    FROM revenue_validation v
    CROSS JOIN revenue_consistency c
    CROSS JOIN ltv_validation l
    WHERE v.negative_mrr > 0
       OR v.negative_arr > 0
       OR v.negative_ltv > 0
       OR v.invalid_churn_prob > 0
       OR v.invalid_discount > 0
       OR c.inconsistent_arr_mrr > 0
       OR l.unreasonable_ltv > 0
)
-- Test fails if revenue metrics are invalid
SELECT * FROM invalid_metrics