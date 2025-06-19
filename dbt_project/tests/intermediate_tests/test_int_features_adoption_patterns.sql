-- Test int_features__adoption_patterns for adoption metrics
WITH adoption_validation AS (
    SELECT 
        COUNT(*) AS total_records,
        COUNT(DISTINCT feature_name) AS unique_features,
        SUM(CASE WHEN adoption_rate < 0 OR adoption_rate > 100 THEN 1 ELSE 0 END) AS invalid_adoption_rate,
        SUM(CASE WHEN monthly_active_users < 0 THEN 1 ELSE 0 END) AS negative_mau,
        SUM(CASE WHEN usage_frequency < 0 THEN 1 ELSE 0 END) AS negative_frequency,
        SUM(CASE WHEN adoption_velocity < -100 OR adoption_velocity > 100 THEN 1 ELSE 0 END) AS invalid_velocity
    FROM {{ ref('int_features__adoption_patterns') }}
),
adoption_consistency AS (
    -- Check that adoption patterns make sense
    SELECT 
        COUNT(*) AS inconsistent_adoptions
    FROM {{ ref('int_features__adoption_patterns') }}
    WHERE adoption_rate > 0 
      AND monthly_active_users = 0  -- If adopted, should have users
),
invalid_patterns AS (
    SELECT 
        v.*,
        c.inconsistent_adoptions
    FROM adoption_validation v
    CROSS JOIN adoption_consistency c
    WHERE v.invalid_adoption_rate > 0
       OR v.negative_mau > 0
       OR v.negative_frequency > 0
       OR v.invalid_velocity > 0
       OR c.inconsistent_adoptions > 0
)
-- Test fails if adoption patterns are invalid
SELECT * FROM invalid_patterns
WHERE invalid_adoption_rate > 0
   OR negative_mau > 0
   OR negative_frequency > 0
   OR invalid_velocity > 0
   OR inconsistent_adoptions > 0