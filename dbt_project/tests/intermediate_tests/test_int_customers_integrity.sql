-- Test int_customers__core for data integrity
WITH customer_validation AS (
    SELECT 
        COUNT(*) AS total_customers,
        COUNT(DISTINCT account_id) AS unique_customers,
        SUM(CASE WHEN account_name IS NULL OR TRIM(account_name) = '' THEN 1 ELSE 0 END) AS missing_company_names,
        SUM(CASE WHEN subscription_status = 'active' AND account_status != 'active' THEN 1 ELSE 0 END) AS invalid_active_status
    FROM {{ ref('int_customers__core') }}
),
duplicate_check AS (
    SELECT 
        account_id,
        COUNT(*) AS occurrences
    FROM {{ ref('int_customers__core') }}
    GROUP BY account_id
    HAVING COUNT(*) > 1
),
invalid_data AS (
    SELECT *
    FROM customer_validation
    WHERE missing_company_names > 0
       OR invalid_active_status > 0
       OR unique_customers != total_customers
)
-- Test fails if data integrity issues found
SELECT 
    (SELECT COUNT(*) FROM duplicate_check) AS duplicate_count,
    v.*
FROM invalid_data v
WHERE (SELECT COUNT(*) FROM duplicate_check) > 0
   OR v.missing_company_names > 0
   OR v.invalid_active_status > 0