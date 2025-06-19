-- 06_user_engagement_scores.sql
-- Phase 2: Generate Realistic User Engagement Scores
-- ==================================================
-- Replace synthetic engagement scores with role-based distributions

-- Ensure we have the helper functions
CREATE OR REPLACE FUNCTION IF NOT EXISTS normalized.generate_normal_random(mean NUMERIC, stddev NUMERIC) 
RETURNS NUMERIC AS $$
DECLARE
    u1 NUMERIC;
    u2 NUMERIC;
    z0 NUMERIC;
BEGIN
    u1 := random();
    u2 := random();
    z0 := sqrt(-2 * ln(u1)) * cos(2 * pi() * u2);
    RETURN mean + (stddev * z0);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION IF NOT EXISTS normalized.generate_beta_random(alpha NUMERIC, beta NUMERIC) 
RETURNS NUMERIC AS $$
DECLARE
    x NUMERIC;
    y NUMERIC;
BEGIN
    x := random() ^ (1.0 / alpha);
    y := random() ^ (1.0 / beta);
    RETURN x / (x + y);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION normalized.generate_gamma_random(alpha NUMERIC, beta NUMERIC) 
RETURNS NUMERIC AS $$
DECLARE
    d NUMERIC;
    c NUMERIC;
    x NUMERIC;
    v NUMERIC;
    u NUMERIC;
BEGIN
    -- Marsaglia and Tsang method
    d := alpha - 1.0/3.0;
    c := 1.0/sqrt(9.0*d);
    
    LOOP
        x := normalized.generate_normal_random(0, 1);
        v := power(1 + c*x, 3);
        EXIT WHEN v > 0;
    END LOOP;
    
    u := random();
    IF u < 1 - 0.0331*power(x, 4) THEN
        RETURN d*v/beta;
    END IF;
    
    IF ln(u) < 0.5*power(x, 2) + d*(1 - v + ln(v)) THEN
        RETURN d*v/beta;
    END IF;
    
    -- If neither condition met, use approximation
    RETURN alpha/beta;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- Step 1: Analyze Current User Distribution
-- ========================================

\echo 'CURRENT USER ENGAGEMENT STATE'
\echo '============================='
\echo ''
\echo 'User Role Distribution:'

SELECT 
    role_type_standardized,
    COUNT(*) as user_count,
    ROUND(AVG(engagement_score), 4) as current_avg_engagement,
    MIN(engagement_score) as min_engagement,
    MAX(engagement_score) as max_engagement
FROM normalized.users
GROUP BY role_type_standardized
ORDER BY user_count DESC;

-- ========================================
-- Step 2: Update Engagement Scores by Role
-- ========================================

UPDATE normalized.users
SET 
    -- Engagement score based on role type
    engagement_score = CASE role_type_standardized
        WHEN 'Admin' THEN 
            LEAST(100, GREATEST(0, 
                normalized.generate_beta_random(4, 1.2) * 100
            ))
        WHEN 'Manager' THEN 
            LEAST(100, GREATEST(0, 
                normalized.generate_normal_random(65, 10)
            ))
        WHEN 'Standard' THEN 
            LEAST(100, GREATEST(0, 
                normalized.generate_gamma_random(2, 0.03)
            ))
        ELSE -- Other roles
            LEAST(100, GREATEST(0, 
                normalized.generate_normal_random(50, 15)
            ))
    END;

-- ========================================
-- Step 3: Adjust Engagement Based on Activity
-- ========================================

-- First, generate realistic activity metrics
UPDATE normalized.users
SET 
    -- Days since last login (lower for engaged users)
    days_since_last_login = CASE 
        WHEN engagement_score > 80 THEN FLOOR(normalized.generate_gamma_random(1.5, 0.5))
        WHEN engagement_score > 60 THEN FLOOR(normalized.generate_gamma_random(2, 0.3))
        WHEN engagement_score > 40 THEN FLOOR(normalized.generate_normal_random(15, 10))
        ELSE FLOOR(normalized.generate_normal_random(45, 30))
    END,
    
    -- Total sessions in 30 days
    total_sessions_30d = CASE 
        WHEN role_type_standardized = 'Admin' THEN 
            FLOOR(normalized.generate_normal_random(80, 20))
        WHEN role_type_standardized = 'Manager' THEN 
            FLOOR(normalized.generate_normal_random(60, 20))
        ELSE 
            FLOOR(normalized.generate_normal_random(40, 25))
    END,
    
    -- Session minutes
    total_session_minutes_30d = CASE 
        WHEN role_type_standardized = 'Admin' THEN 
            normalized.generate_normal_random(1200, 300)
        WHEN role_type_standardized = 'Manager' THEN 
            normalized.generate_normal_random(900, 250)
        ELSE 
            normalized.generate_normal_random(600, 300)
    END,
    
    -- Active days
    active_days_30d = CASE 
        WHEN engagement_score > 80 THEN FLOOR(normalized.generate_normal_random(25, 3))
        WHEN engagement_score > 60 THEN FLOOR(normalized.generate_normal_random(20, 5))
        WHEN engagement_score > 40 THEN FLOOR(normalized.generate_normal_random(15, 5))
        ELSE FLOOR(normalized.generate_normal_random(8, 5))
    END;

-- Update calculated fields
UPDATE normalized.users
SET 
    avg_session_minutes_30d = CASE 
        WHEN total_sessions_30d > 0 THEN total_session_minutes_30d / total_sessions_30d
        ELSE 0
    END,
    sessions_per_active_day_30d = CASE 
        WHEN active_days_30d > 0 THEN total_sessions_30d::NUMERIC / active_days_30d
        ELSE 0
    END;

-- ========================================
-- Step 4: Generate Feature Usage Metrics
-- ========================================

UPDATE normalized.users
SET 
    -- Features used (higher for admins)
    features_used_30d = CASE 
        WHEN role_type_standardized = 'Admin' THEN 
            FLOOR(normalized.generate_normal_random(25, 8))
        WHEN role_type_standardized = 'Manager' THEN 
            FLOOR(normalized.generate_normal_random(18, 6))
        ELSE 
            FLOOR(normalized.generate_normal_random(10, 5))
    END,
    
    -- Power features (advanced functionality)
    power_features_used_30d = CASE 
        WHEN role_type_standardized = 'Admin' THEN 
            FLOOR(normalized.generate_normal_random(10, 4))
        WHEN role_type_standardized = 'Manager' THEN 
            FLOOR(normalized.generate_normal_random(5, 3))
        ELSE 
            FLOOR(normalized.generate_normal_random(2, 2))
    END,
    
    -- Mobile usage
    mobile_app_usage_30d = FLOOR(total_sessions_30d * normalized.generate_beta_random(2, 5)),
    
    -- API usage (higher for power users)
    api_calls_30d = CASE 
        WHEN engagement_score > 80 THEN FLOOR(normalized.generate_normal_random(500, 200))
        WHEN engagement_score > 60 THEN FLOOR(normalized.generate_normal_random(200, 100))
        ELSE FLOOR(normalized.generate_normal_random(50, 50))
    END,
    
    -- Data export (managers export more)
    data_exported_mb_30d = CASE 
        WHEN role_type_standardized = 'Manager' THEN 
            normalized.generate_normal_random(100, 50)
        WHEN role_type_standardized = 'Admin' THEN 
            normalized.generate_normal_random(50, 30)
        ELSE 
            normalized.generate_normal_random(10, 10)
    END,
    
    -- Reports generated
    reports_generated_30d = CASE 
        WHEN role_type_standardized = 'Manager' THEN 
            FLOOR(normalized.generate_normal_random(15, 8))
        WHEN role_type_standardized = 'Admin' THEN 
            FLOOR(normalized.generate_normal_random(8, 5))
        ELSE 
            FLOOR(normalized.generate_normal_random(3, 3))
    END;

-- Update mobile usage percentage
UPDATE normalized.users
SET mobile_usage_percentage = CASE 
    WHEN total_sessions_30d > 0 THEN (mobile_app_usage_30d::NUMERIC / total_sessions_30d) * 100
    ELSE 0
END;

-- ========================================
-- Step 5: Generate User Behavior Metrics
-- ========================================

UPDATE normalized.users
SET 
    -- Failed login attempts (inverse of engagement)
    failed_login_attempts_7d = CASE 
        WHEN engagement_score > 80 THEN FLOOR(normalized.generate_normal_random(0.5, 1))
        ELSE FLOOR(normalized.generate_normal_random(2, 2))
    END,
    
    -- Alerts configured (power users configure more)
    alerts_configured = CASE 
        WHEN engagement_score > 70 THEN FLOOR(normalized.generate_normal_random(5, 3))
        ELSE FLOOR(normalized.generate_normal_random(1, 2))
    END,
    
    -- Integrations active
    integrations_active = CASE 
        WHEN role_type_standardized = 'Admin' THEN FLOOR(normalized.generate_normal_random(3, 2))
        ELSE FLOOR(normalized.generate_normal_random(1, 1))
    END,
    
    -- Time to first value (minutes)
    time_to_first_value_minutes = CASE 
        WHEN engagement_score > 70 THEN normalized.generate_normal_random(15, 10)
        ELSE normalized.generate_normal_random(45, 30)
    END,
    
    -- Days to habit formation
    days_to_habit_formation = CASE 
        WHEN engagement_score > 70 THEN FLOOR(normalized.generate_normal_random(14, 7))
        ELSE FLOOR(normalized.generate_normal_random(30, 20))
    END;

-- ========================================
-- Step 6: Generate Advanced User Metrics
-- ========================================

UPDATE normalized.users
SET 
    -- Engagement trend (-100 to +100)
    engagement_trend = CASE 
        WHEN engagement_score > 70 THEN normalized.generate_normal_random(10, 20)
        WHEN engagement_score > 40 THEN normalized.generate_normal_random(0, 25)
        ELSE normalized.generate_normal_random(-10, 30)
    END,
    
    -- Influence score (based on role and engagement)
    influence_score = CASE 
        WHEN role_type_standardized = 'Admin' THEN 
            engagement_score * 1.2 + normalized.generate_normal_random(0, 10)
        WHEN role_type_standardized = 'Manager' THEN 
            engagement_score * 1.1 + normalized.generate_normal_random(0, 10)
        ELSE 
            engagement_score * 0.8 + normalized.generate_normal_random(0, 10)
    END,
    
    -- Knowledge sharing score
    knowledge_sharing_score = CASE 
        WHEN engagement_score > 70 THEN normalized.generate_normal_random(75, 15)
        ELSE normalized.generate_normal_random(40, 20)
    END,
    
    -- Champion user flag
    is_champion_user = CASE 
        WHEN engagement_score > 85 AND role_type_standardized IN ('Admin', 'Manager') THEN true
        ELSE false
    END,
    
    -- Training needs
    needs_training = CASE 
        WHEN engagement_score < 40 THEN true
        WHEN features_used_30d < 5 THEN true
        ELSE false
    END,
    
    -- Support metrics
    support_tickets_created_30d = CASE 
        WHEN engagement_score < 40 THEN FLOOR(normalized.generate_normal_random(3, 2))
        ELSE FLOOR(normalized.generate_normal_random(0.5, 1))
    END,
    
    -- Satisfaction score
    satisfaction_score = CASE 
        WHEN engagement_score > 70 THEN normalized.generate_normal_random(85, 10)
        WHEN engagement_score > 40 THEN normalized.generate_normal_random(70, 15)
        ELSE normalized.generate_normal_random(50, 20)
    END,
    
    -- Predicted churn risk (inverse of engagement)
    predicted_churn_risk = LEAST(100, GREATEST(0, 
        100 - engagement_score + normalized.generate_normal_random(0, 15)
    ));

-- ========================================
-- Generate Engagement Summary Report
-- ========================================

\echo ''
\echo 'USER ENGAGEMENT GENERATION SUMMARY'
\echo '================================='
\echo ''
\echo 'Engagement Score Distribution by Role:'

SELECT 
    role_type_standardized,
    COUNT(*) as user_count,
    ROUND(MIN(engagement_score), 2) as min_engagement,
    ROUND(AVG(engagement_score), 2) as avg_engagement,
    ROUND(MAX(engagement_score), 2) as max_engagement,
    ROUND(STDDEV(engagement_score), 2) as stddev_engagement
FROM normalized.users
GROUP BY role_type_standardized
ORDER BY avg_engagement DESC;

\echo ''
\echo 'Activity Metrics by Engagement Level:'

SELECT 
    CASE 
        WHEN engagement_score >= 80 THEN '80-100 (Highly Engaged)'
        WHEN engagement_score >= 60 THEN '60-79 (Engaged)'
        WHEN engagement_score >= 40 THEN '40-59 (Moderate)'
        ELSE '0-39 (Low)'
    END as engagement_level,
    COUNT(*) as user_count,
    ROUND(AVG(total_sessions_30d), 1) as avg_sessions,
    ROUND(AVG(active_days_30d), 1) as avg_active_days,
    ROUND(AVG(features_used_30d), 1) as avg_features,
    ROUND(AVG(satisfaction_score), 1) as avg_satisfaction
FROM normalized.users
GROUP BY engagement_level
ORDER BY 
    CASE 
        WHEN engagement_score >= 80 THEN 1
        WHEN engagement_score >= 60 THEN 2
        WHEN engagement_score >= 40 THEN 3
        ELSE 4
    END;

\echo ''
\echo 'Champion Users by Account:'

SELECT 
    u.account_id,
    COUNT(*) as total_users,
    COUNT(CASE WHEN is_champion_user THEN 1 END) as champion_users,
    ROUND(AVG(engagement_score), 2) as avg_engagement
FROM normalized.users u
GROUP BY u.account_id
HAVING COUNT(CASE WHEN is_champion_user THEN 1 END) > 0
ORDER BY champion_users DESC
LIMIT 10;

-- Clean up functions
DROP FUNCTION IF EXISTS normalized.generate_gamma_random(NUMERIC, NUMERIC);

\echo ''
\echo 'User engagement score generation completed successfully!'
