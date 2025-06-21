-- Test int_campaigns__attribution for attribution logic
WITH attribution_validation AS (
    SELECT 
        COUNT(*) AS total_touchpoints,
        COUNT(DISTINCT campaign_id) AS unique_campaigns,
        SUM(CASE WHEN attribution_credit < 0 OR attribution_credit > 1 THEN 1 ELSE 0 END) AS invalid_credits,
        SUM(CASE WHEN touchpoint_rank < 1 THEN 1 ELSE 0 END) AS invalid_ranks,
        SUM(CASE WHEN attributed_revenue < 0 THEN 1 ELSE 0 END) AS negative_revenue
    FROM {{ ref('int_campaigns__attribution') }}
),
credit_totals AS (
    -- Check that attribution credits sum to 1 per conversion
    SELECT 
        conversion_id,
        SUM(attribution_credit) AS total_credit
    FROM {{ ref('int_campaigns__attribution') }}
    GROUP BY conversion_id
    HAVING ABS(SUM(attribution_credit) - 1.0) > 0.01
),
invalid_attribution AS (
    SELECT 
        (SELECT COUNT(*) FROM credit_totals) AS invalid_credit_totals,
        negative_revenue,
        invalid_credits,
        invalid_ranks
    FROM attribution_validation
    WHERE negative_revenue > 0
       OR invalid_credits > 0
       OR invalid_ranks > 0
)
-- Test fails if attribution logic is invalid
SELECT * FROM invalid_attribution
WHERE invalid_credit_totals > 0
   OR negative_revenue > 0
   OR invalid_credits > 0
   OR invalid_ranks > 0