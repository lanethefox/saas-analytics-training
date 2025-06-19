-- Test int_subscriptions__core for subscription data integrity
WITH subscription_validation AS (
    SELECT 
        COUNT(*) AS total_subscriptions,
        COUNT(DISTINCT subscription_id) AS unique_subscriptions,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS missing_account_id,
        SUM(CASE WHEN plan_name IS NULL OR TRIM(plan_name) = '' THEN 1 ELSE 0 END) AS missing_plan_name,
        SUM(CASE WHEN start_date > CURRENT_DATE THEN 1 ELSE 0 END) AS future_start_dates,
        SUM(CASE WHEN end_date < start_date THEN 1 ELSE 0 END) AS invalid_date_ranges,
        SUM(CASE WHEN status NOT IN ('active', 'cancelled', 'trial', 'past_due', 'paused') THEN 1 ELSE 0 END) AS invalid_status
    FROM {{ ref('int_subscriptions__core') }}
),
status_consistency AS (
    -- Check status consistency with dates
    SELECT 
        COUNT(*) AS inconsistent_statuses
    FROM {{ ref('int_subscriptions__core') }}
    WHERE (status = 'active' AND end_date < CURRENT_DATE)
       OR (status = 'cancelled' AND end_date IS NULL)
       OR (status = 'trial' AND trial_end_date < CURRENT_DATE)
),
duplicate_check AS (
    SELECT 
        subscription_id,
        COUNT(*) AS occurrences
    FROM {{ ref('int_subscriptions__core') }}
    GROUP BY subscription_id
    HAVING COUNT(*) > 1
),
invalid_data AS (
    SELECT 
        v.*,
        s.inconsistent_statuses,
        (SELECT COUNT(*) FROM duplicate_check) AS duplicate_count
    FROM subscription_validation v
    CROSS JOIN status_consistency s
    WHERE v.missing_account_id > 0
       OR v.missing_plan_name > 0
       OR v.future_start_dates > 0
       OR v.invalid_date_ranges > 0
       OR v.invalid_status > 0
       OR v.unique_subscriptions != v.total_subscriptions
       OR s.inconsistent_statuses > 0
)
-- Test fails if subscription data is invalid
SELECT * FROM invalid_data