-- Test int_users__engagement_metrics for engagement calculations
WITH engagement_validation AS (
    SELECT 
        COUNT(*) AS total_records,
        COUNT(DISTINCT user_id) AS unique_users,
        SUM(CASE WHEN engagement_score < 0 OR engagement_score > 100 THEN 1 ELSE 0 END) AS invalid_engagement_score,
        SUM(CASE WHEN days_since_last_login < 0 THEN 1 ELSE 0 END) AS negative_days_since_login,
        SUM(CASE WHEN total_sessions < 0 THEN 1 ELSE 0 END) AS negative_sessions,
        SUM(CASE WHEN avg_session_duration < 0 THEN 1 ELSE 0 END) AS negative_duration,
        SUM(CASE WHEN feature_adoption_rate < 0 OR feature_adoption_rate > 100 THEN 1 ELSE 0 END) AS invalid_adoption_rate
    FROM {{ ref('int_users__engagement_metrics') }}
),
engagement_consistency AS (
    -- Check engagement score consistency with activity
    SELECT 
        COUNT(*) AS inconsistent_engagement
    FROM {{ ref('int_users__engagement_metrics') }}
    WHERE (engagement_score > 80 AND days_since_last_login > 30)  -- High engagement but inactive
       OR (engagement_score < 20 AND days_since_last_login = 0 AND total_sessions > 100)  -- Low engagement but very active
),
session_validation AS (
    -- Validate session metrics
    SELECT 
        COUNT(*) AS invalid_sessions
    FROM {{ ref('int_users__engagement_metrics') }}
    WHERE total_sessions = 0 
      AND (avg_session_duration > 0 OR pages_per_session > 0)  -- No sessions but metrics exist
),
invalid_metrics AS (
    SELECT 
        v.*,
        c.inconsistent_engagement,
        s.invalid_sessions
    FROM engagement_validation v
    CROSS JOIN engagement_consistency c
    CROSS JOIN session_validation s
    WHERE v.invalid_engagement_score > 0
       OR v.negative_days_since_login > 0
       OR v.negative_sessions > 0
       OR v.negative_duration > 0
       OR v.invalid_adoption_rate > 0
       OR c.inconsistent_engagement > 0
       OR s.invalid_sessions > 0
)
-- Test fails if engagement metrics are invalid
SELECT * FROM invalid_metrics