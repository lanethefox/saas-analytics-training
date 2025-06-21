-- Test int_features__core for feature integrity
WITH feature_validation AS (
    SELECT 
        COUNT(*) AS total_features,
        COUNT(DISTINCT feature_name) AS unique_features,
        SUM(CASE WHEN feature_category IS NULL OR TRIM(feature_category) = '' THEN 1 ELSE 0 END) AS missing_category,
        SUM(CASE WHEN release_date > CURRENT_DATE THEN 1 ELSE 0 END) AS future_release_dates,
        SUM(CASE WHEN is_active = FALSE AND deprecated_date IS NULL THEN 1 ELSE 0 END) AS missing_deprecation_date,
        SUM(CASE WHEN is_active = TRUE AND deprecated_date IS NOT NULL THEN 1 ELSE 0 END) AS invalid_active_status
    FROM {{ ref('int_features__core') }}
),
duplicate_features AS (
    SELECT 
        feature_name,
        COUNT(*) AS occurrences
    FROM {{ ref('int_features__core') }}
    GROUP BY feature_name
    HAVING COUNT(*) > 1
),
invalid_data AS (
    SELECT *
    FROM feature_validation
    WHERE missing_category > 0
       OR future_release_dates > 0
       OR missing_deprecation_date > 0
       OR invalid_active_status > 0
       OR unique_features != total_features
)
-- Test fails if feature data is invalid
SELECT 
    (SELECT COUNT(*) FROM duplicate_features) AS duplicate_count,
    v.*
FROM invalid_data v
WHERE (SELECT COUNT(*) FROM duplicate_features) > 0
   OR v.missing_category > 0
   OR v.future_release_dates > 0
   OR v.missing_deprecation_date > 0
   OR v.invalid_active_status > 0