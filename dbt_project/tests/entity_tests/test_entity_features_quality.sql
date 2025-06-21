-- Test entity_features for feature adoption and value metrics
WITH feature_validation AS (
    SELECT 
        COUNT(*) AS total_features,
        COUNT(DISTINCT feature_name) AS unique_features,
        SUM(CASE WHEN feature_value_score < 0 OR feature_value_score > 100 THEN 1 ELSE 0 END) AS invalid_value_score,
        SUM(CASE WHEN adoption_percentage < 0 OR adoption_percentage > 100 THEN 1 ELSE 0 END) AS invalid_adoption,
        SUM(CASE WHEN monthly_active_users < 0 THEN 1 ELSE 0 END) AS negative_mau,
        SUM(CASE WHEN adoption_stage NOT IN ('introduction', 'growth', 'maturity', 'decline') THEN 1 ELSE 0 END) AS invalid_stage
    FROM {{ ref('entity_features') }}
),
strategic_validation AS (
    -- Check strategic importance aligns with adoption
    SELECT 
        COUNT(*) AS inconsistent_strategy
    FROM {{ ref('entity_features') }}
    WHERE (strategic_importance = 'critical' AND adoption_percentage < 20)
       OR (strategic_importance = 'low' AND adoption_percentage > 80 AND feature_value_score > 80)
),
usage_pattern_validation AS (
    -- Validate usage patterns
    SELECT 
        COUNT(*) AS invalid_usage_patterns
    FROM {{ ref('entity_features') }}
    WHERE (monthly_active_users = 0 AND adoption_percentage > 0)
       OR (average_sessions_per_user < 0)
       OR (total_usage_minutes < 0)
),
revenue_impact_check AS (
    -- High-value features should have revenue correlation
    SELECT 
        COUNT(*) AS missing_revenue_impact
    FROM {{ ref('entity_features') }}
    WHERE feature_value_score > 80
      AND revenue_correlation < 0.3
      AND adoption_percentage > 50
),
invalid_data AS (
    SELECT 
        v.*,
        sv.inconsistent_strategy,
        up.invalid_usage_patterns,
        ri.missing_revenue_impact
    FROM feature_validation v
    CROSS JOIN strategic_validation sv
    CROSS JOIN usage_pattern_validation up
    CROSS JOIN revenue_impact_check ri
    WHERE v.invalid_value_score > 0
       OR v.invalid_adoption > 0
       OR v.negative_mau > 0
       OR v.invalid_stage > 0
       OR sv.inconsistent_strategy > 0
       OR up.invalid_usage_patterns > 0
       OR ri.missing_revenue_impact > 0
)
-- Test fails if feature entity data is invalid
SELECT * FROM invalid_data