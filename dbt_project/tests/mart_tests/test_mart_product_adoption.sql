-- Test mart_product__adoption for product adoption metrics
WITH adoption_validation AS (
    SELECT 
        COUNT(*) AS total_features,
        COUNT(DISTINCT feature_name) AS unique_features,
        SUM(CASE WHEN adoption_rate < 0 OR adoption_rate > 100 THEN 1 ELSE 0 END) AS invalid_adoption_rate,
        SUM(CASE WHEN user_count < 0 THEN 1 ELSE 0 END) AS negative_users,
        SUM(CASE WHEN customer_count < 0 THEN 1 ELSE 0 END) AS negative_customers,
        SUM(CASE WHEN revenue_impact < 0 THEN 1 ELSE 0 END) AS negative_revenue_impact,
        SUM(CASE WHEN stickiness_score < 0 OR stickiness_score > 100 THEN 1 ELSE 0 END) AS invalid_stickiness
    FROM {{ ref('mart_product__adoption') }}
)-- Test mart_product__adoption for product adoption metrics
WITH adoption_validation AS (
    SELECT 
        COUNT(*) AS total_features,
        COUNT(DISTINCT feature_name) AS unique_features,
        SUM(CASE WHEN adoption_rate < 0 OR adoption_rate > 100 THEN 1 ELSE 0 END) AS invalid_adoption_rate,
        SUM(CASE WHEN user_count < 0 THEN 1 ELSE 0 END) AS negative_users,
        SUM(CASE WHEN customer_count < 0 THEN 1 ELSE 0 END) AS negative_customers,
        SUM(CASE WHEN revenue_impact < 0 THEN 1 ELSE 0 END) AS negative_revenue_impact,
        SUM(CASE WHEN stickiness_score < 0 OR stickiness_score > 100 THEN 1 ELSE 0 END) AS invalid_stickiness
    FROM {{ ref('mart_product__adoption') }}
),
adoption_consistency AS (
    -- User count should be >= customer count (multiple users per customer)
    SELECT 
        COUNT(*) AS inconsistent_counts
    FROM {{ ref('mart_product__adoption') }}
    WHERE user_count < customer_count
      AND user_count > 0
),
feature_categorization AS (
    -- Validate feature categories and stages
    SELECT 
        COUNT(*) AS invalid_categories
    FROM {{ ref('mart_product__adoption') }}
    WHERE feature_category NOT IN ('core', 'advanced', 'enterprise', 'beta', 'deprecated')
       OR adoption_stage NOT IN ('introduction', 'growth', 'maturity', 'decline')
),
revenue_correlation AS (
    -- High adoption should correlate with revenue impact
    SELECT 
        COUNT(*) AS inconsistent_revenue
    FROM {{ ref('mart_product__adoption') }}
    WHERE (adoption_rate > 80 AND revenue_impact = 0)
       OR (adoption_rate < 10 AND revenue_impact > 100000)
),
invalid_data AS (
    SELECT 
        v.*,
        ac.inconsistent_counts,
        fc.invalid_categories,
        rc.inconsistent_revenue
    FROM adoption_validation v
    CROSS JOIN adoption_consistency ac
    CROSS JOIN feature_categorization fc
    CROSS JOIN revenue_correlation rc
    WHERE v.invalid_adoption_rate > 0
       OR v.negative_users > 0
       OR v.negative_customers > 0
       OR v.negative_revenue_impact > 0
       OR v.invalid_stickiness > 0
       OR ac.inconsistent_counts > 0
       OR fc.invalid_categories > 0
       OR rc.inconsistent_revenue > 0
)
-- Test fails if product adoption metrics are invalid
SELECT * FROM invalid_data