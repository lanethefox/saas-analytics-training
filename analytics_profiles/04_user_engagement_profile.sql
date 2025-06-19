-- User Engagement and Feature Adoption Profile
-- This script analyzes user behavior and feature usage patterns

-- ========================================
-- 4. USER ENGAGEMENT PROFILE
-- ========================================

WITH user_metrics AS (
    SELECT 
        -- User counts and activity
        COUNT(*) as total_users,
        COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_users,
        COUNT(CASE WHEN days_since_last_login <= 7 THEN 1 END) as weekly_active_users,
        COUNT(CASE WHEN days_since_last_login <= 30 THEN 1 END) as monthly_active_users,
        
        -- Engagement distribution
        AVG(engagement_score) as avg_engagement_score,
        COUNT(CASE WHEN user_engagement_tier = 'highly_engaged' THEN 1 END) as highly_engaged,
        COUNT(CASE WHEN user_engagement_tier = 'moderately_engaged' THEN 1 END) as moderately_engaged,
        COUNT(CASE WHEN user_engagement_tier = 'low_engagement' THEN 1 END) as low_engagement,
        COUNT(CASE WHEN user_engagement_tier = 'at_risk' THEN 1 END) as at_risk,
        
        -- Session metrics
        SUM(total_sessions_30d) as total_sessions_30d,
        AVG(total_sessions_30d) as avg_sessions_per_user_30d,
        AVG(avg_session_duration_30d) as avg_session_duration,
        
        -- Feature adoption
        AVG(features_adopted) as avg_features_adopted,
        AVG(feature_adoption_rate) as avg_feature_adoption_rate
        
    FROM entity.entity_users
    WHERE is_active = TRUE
),
user_roles AS (
    SELECT 
        role,
        COUNT(*) as user_count,
        AVG(engagement_score) as avg_engagement,
        AVG(total_sessions_30d) as avg_sessions
    FROM entity.entity_users
    GROUP BY role
),
feature_adoption AS (
    SELECT 
        feature_name,
        feature_category,
        adoption_percentage,
        monthly_active_users,
        average_sessions_per_user,
        feature_value_score,
        adoption_stage,
        strategic_importance
    FROM entity.entity_features
    ORDER BY adoption_percentage DESC
    LIMIT 15
),
weekly_user_activity AS (
    SELECT 
        week_start_date,
        COUNT(DISTINCT user_id) as active_users,
        AVG(weekly_sessions) as avg_sessions,
        AVG(weekly_engagement_score) as avg_engagement,
        SUM(CASE WHEN weekly_activity_level = 'highly_active' THEN 1 ELSE 0 END) as highly_active_users
    FROM entity.entity_users_weekly
    WHERE week_start_date >= CURRENT_DATE - INTERVAL '4 weeks'
    GROUP BY week_start_date
    ORDER BY week_start_date DESC
)
SELECT 'USER ENGAGEMENT PROFILE' as profile_section, '======================' as value
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'USER ACTIVITY METRICS', '--------------------'
UNION ALL
SELECT 'Total Users', total_users::text FROM user_metrics
UNION ALL
SELECT 'Active Users', active_users::text || ' (' || ROUND(active_users::numeric/total_users*100, 1) || '%)' FROM user_metrics
UNION ALL
SELECT 'Weekly Active Users', weekly_active_users::text || ' (' || ROUND(weekly_active_users::numeric/total_users*100, 1) || '%)' FROM user_metrics
UNION ALL
SELECT 'Monthly Active Users', monthly_active_users::text || ' (' || ROUND(monthly_active_users::numeric/total_users*100, 1) || '%)' FROM user_metrics
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'ENGAGEMENT DISTRIBUTION', '----------------------'
UNION ALL
SELECT 'Highly Engaged', highly_engaged::text || ' (' || ROUND(highly_engaged::numeric/active_users*100, 1) || '%)' FROM user_metrics
UNION ALL
SELECT 'Moderately Engaged', moderately_engaged::text || ' (' || ROUND(moderately_engaged::numeric/active_users*100, 1) || '%)' FROM user_metrics
UNION ALL
SELECT 'Low Engagement', low_engagement::text || ' (' || ROUND(low_engagement::numeric/active_users*100, 1) || '%)' FROM user_metrics
UNION ALL
SELECT 'At Risk', at_risk::text || ' (' || ROUND(at_risk::numeric/active_users*100, 1) || '%)' FROM user_metrics
UNION ALL
SELECT 'Avg Engagement Score', ROUND(avg_engagement_score, 2)::text FROM user_metrics
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'SESSION METRICS (30 DAYS)', '------------------------'
UNION ALL
SELECT 'Total Sessions', TO_CHAR(total_sessions_30d, 'FM999,999,999') FROM user_metrics
UNION ALL
SELECT 'Avg Sessions per User', ROUND(avg_sessions_per_user_30d, 1)::text FROM user_metrics
UNION ALL
SELECT 'Avg Session Duration', ROUND(avg_session_duration, 1)::text || ' minutes' FROM user_metrics
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'USER ROLES', '----------'
UNION ALL
SELECT role || ' (' || user_count || ')', 
       'Engagement: ' || ROUND(avg_engagement, 1)::text || ', Sessions: ' || ROUND(avg_sessions, 1)::text
FROM user_roles
ORDER BY user_count DESC;