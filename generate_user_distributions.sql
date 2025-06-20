-- Generate realistic data distributions for normalized tables
-- Task 2: Create realistic distributions for engagement, performance metrics, etc.

-- 1. Update user engagement scores based on role
-- Admin: 70-95, Manager: 50-80, Standard: 20-70

-- First add engagement_score column to normalized.users if not exists
ALTER TABLE normalized.users ADD COLUMN IF NOT EXISTS engagement_score NUMERIC(5,2);

-- Update engagement scores with realistic distribution by role
WITH score_updates AS (
    SELECT 
        user_id,
        role_type_standardized,
        -- Generate scores based on role with normal distribution
        CASE role_type_standardized
            WHEN 'Admin' THEN 
                -- Admin scores: 70-95, centered around 82.5
                LEAST(95, GREATEST(70, 82.5 + (RANDOM() - 0.5) * 25))::NUMERIC
            WHEN 'Manager' THEN 
                -- Manager scores: 50-80, centered around 65
                LEAST(80, GREATEST(50, 65 + (RANDOM() - 0.5) * 30))::NUMERIC
            WHEN 'Standard' THEN 
                -- Standard scores: 20-70, centered around 45
                LEAST(70, GREATEST(20, 45 + (RANDOM() - 0.5) * 50))::NUMERIC
            ELSE 50::NUMERIC -- Default
        END as engagement_score
    FROM normalized.users
)
UPDATE normalized.users u
SET engagement_score = ROUND(su.engagement_score::NUMERIC, 2)
FROM score_updates su
WHERE u.user_id = su.user_id;

-- Show engagement score distribution
SELECT 
    role_type_standardized,
    COUNT(*) as user_count,
    ROUND(MIN(engagement_score)::NUMERIC, 2) as min_score,
    ROUND(AVG(engagement_score)::NUMERIC, 2) as avg_score,
    ROUND(MAX(engagement_score)::NUMERIC, 2) as max_score,
    ROUND(STDDEV(engagement_score)::NUMERIC, 2) as std_dev
FROM normalized.users
GROUP BY role_type_standardized
ORDER BY avg_score DESC;

-- 2. Update user activity patterns
-- Add columns for activity metrics if not exists
ALTER TABLE normalized.users 
ADD COLUMN IF NOT EXISTS days_active_last_30 INTEGER,
ADD COLUMN IF NOT EXISTS total_sessions_last_30 INTEGER,
ADD COLUMN IF NOT EXISTS avg_session_minutes NUMERIC(5,2);

-- Update activity based on engagement scores
UPDATE normalized.users
SET 
    days_active_last_30 = CASE 
        WHEN engagement_score >= 80 THEN 20 + FLOOR(RANDOM() * 11)::INTEGER  -- 20-30 days
        WHEN engagement_score >= 60 THEN 10 + FLOOR(RANDOM() * 11)::INTEGER  -- 10-20 days
        WHEN engagement_score >= 40 THEN 5 + FLOOR(RANDOM() * 11)::INTEGER   -- 5-15 days
        ELSE FLOOR(RANDOM() * 10)::INTEGER  -- 0-9 days
    END,
    total_sessions_last_30 = CASE 
        WHEN engagement_score >= 80 THEN 40 + FLOOR(RANDOM() * 61)::INTEGER  -- 40-100 sessions
        WHEN engagement_score >= 60 THEN 20 + FLOOR(RANDOM() * 31)::INTEGER  -- 20-50 sessions
        WHEN engagement_score >= 40 THEN 10 + FLOOR(RANDOM() * 21)::INTEGER  -- 10-30 sessions
        ELSE FLOOR(RANDOM() * 15)::INTEGER  -- 0-14 sessions
    END,
    avg_session_minutes = ROUND(CASE 
        WHEN engagement_score >= 80 THEN 15 + RANDOM() * 30  -- 15-45 minutes
        WHEN engagement_score >= 60 THEN 10 + RANDOM() * 20  -- 10-30 minutes
        WHEN engagement_score >= 40 THEN 5 + RANDOM() * 15   -- 5-20 minutes
        ELSE 1 + RANDOM() * 9  -- 1-10 minutes
    END::NUMERIC, 2);

-- 3. Update last login dates based on engagement
UPDATE normalized.users
SET last_login_at = CASE 
    WHEN engagement_score >= 80 THEN 
        CURRENT_TIMESTAMP - (RANDOM() * 3 || ' days')::INTERVAL  -- 0-3 days ago
    WHEN engagement_score >= 60 THEN 
        CURRENT_TIMESTAMP - ((3 + RANDOM() * 7) || ' days')::INTERVAL  -- 3-10 days ago
    WHEN engagement_score >= 40 THEN 
        CURRENT_TIMESTAMP - ((10 + RANDOM() * 20) || ' days')::INTERVAL  -- 10-30 days ago
    ELSE 
        CURRENT_TIMESTAMP - ((30 + RANDOM() * 60) || ' days')::INTERVAL  -- 30-90 days ago
END;

-- Show updated user activity distribution
SELECT 
    role_type_standardized,
    COUNT(*) as users,
    ROUND(AVG(engagement_score)::NUMERIC, 2) as avg_engagement,
    ROUND(AVG(days_active_last_30)::NUMERIC, 1) as avg_days_active,
    ROUND(AVG(total_sessions_last_30)::NUMERIC, 1) as avg_sessions,
    ROUND(AVG(avg_session_minutes)::NUMERIC, 1) as avg_session_mins
FROM normalized.users
GROUP BY role_type_standardized
ORDER BY avg_engagement DESC;

-- Show engagement distribution by score bands
WITH engagement_bands AS (
    SELECT 
        user_id,
        engagement_score,
        CASE 
            WHEN engagement_score >= 80 THEN '80-100 (Highly Engaged)'
            WHEN engagement_score >= 60 THEN '60-79 (Engaged)'
            WHEN engagement_score >= 40 THEN '40-59 (Moderately Engaged)'
            WHEN engagement_score >= 20 THEN '20-39 (Low Engagement)'
            ELSE '0-19 (Inactive)'
        END as engagement_band
    FROM normalized.users
)
SELECT 
    engagement_band,
    COUNT(*) as user_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM engagement_bands
GROUP BY engagement_band
ORDER BY 
    CASE engagement_band
        WHEN '80-100 (Highly Engaged)' THEN 1
        WHEN '60-79 (Engaged)' THEN 2
        WHEN '40-59 (Moderately Engaged)' THEN 3
        WHEN '20-39 (Low Engagement)' THEN 4
        ELSE 5
    END;

-- Sample some users to verify the distribution
SELECT 
    user_id,
    role_type_standardized,
    engagement_score,
    days_active_last_30,
    total_sessions_last_30,
    avg_session_minutes,
    DATE(last_login_at) as last_login_date
FROM normalized.users
ORDER BY RANDOM()
LIMIT 10;
