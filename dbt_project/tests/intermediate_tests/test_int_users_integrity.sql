-- Test int_users__core for user data integrity
WITH user_validation AS (
    SELECT 
        COUNT(*) AS total_users,
        COUNT(DISTINCT user_id) AS unique_users,
        SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS missing_account_id,
        SUM(CASE WHEN email IS NULL OR email NOT LIKE '%@%' THEN 1 ELSE 0 END) AS invalid_emails,
        SUM(CASE WHEN created_at > CURRENT_DATE THEN 1 ELSE 0 END) AS future_created_dates,
        SUM(CASE WHEN last_login_at > CURRENT_DATE THEN 1 ELSE 0 END) AS future_login_dates,
        SUM(CASE WHEN last_login_at < created_at THEN 1 ELSE 0 END) AS login_before_creation,
        SUM(CASE WHEN is_active = FALSE AND deactivated_at IS NULL THEN 1 ELSE 0 END) AS missing_deactivation_date
    FROM {{ ref('int_users__core') }}
),
duplicate_emails AS (
    -- Check for duplicate emails within same account
    SELECT 
        account_id,
        email,
        COUNT(*) AS occurrences
    FROM {{ ref('int_users__core') }}
    WHERE email IS NOT NULL
    GROUP BY account_id, email
    HAVING COUNT(*) > 1
),
role_validation AS (
    -- Validate user roles
    SELECT 
        COUNT(*) AS invalid_roles
    FROM {{ ref('int_users__core') }}
    WHERE role NOT IN ('admin', 'manager', 'operator', 'viewer', 'api_user')
),
invalid_data AS (
    SELECT 
        v.*,
        (SELECT COUNT(*) FROM duplicate_emails) AS duplicate_email_count,
        r.invalid_roles
    FROM user_validation v
    CROSS JOIN role_validation r
    WHERE v.missing_account_id > 0
       OR v.invalid_emails > 0
       OR v.future_created_dates > 0
       OR v.future_login_dates > 0
       OR v.login_before_creation > 0
       OR v.missing_deactivation_date > 0
       OR v.unique_users != v.total_users
       OR r.invalid_roles > 0
)
-- Test fails if user data is invalid
SELECT * FROM invalid_data