-- Test int_customers__core for data integrity
WITH customer_validation AS (
    SELECT 
        COUNT(*) AS total_customers,
        COUNT(DISTINCT account_id) AS unique_customers,
        SUM(CASE WHEN created_at > CURRENT_DATE THEN 1 ELSE 0 END) AS future_created_dates,
        SUM(CASE WHEN updated_at < created_at THEN 1 ELSE 0 END) AS invalid_update_dates,
        SUM(CASE WHEN company_name IS NULL OR TRIM(company_name) = '' THEN 1 ELSE 0 END) AS missing_company_names,
        SUM(CASE WHEN is_active = TRUE AND COALESCE(deactivated_at, CURRENT_DATE) < CURRENT_DATE THEN 1 ELSE 0 END) AS invalid_active_status
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
    WHERE future_created_dates > 0
       OR invalid_update_dates > 0
       OR missing_company_names > 0
       OR invalid_active_status > 0
       OR unique_customers != total_customers
)
-- Test fails if data integrity issues found
SELECT 
    (SELECT COUNT(*) FROM duplicate_check) AS duplicate_count,
    v.*
FROM invalid_data v
WHERE (SELECT COUNT(*) FROM duplicate_check) > 0
   OR v.future_created_dates > 0
   OR v.invalid_update_dates > 0
   OR v.missing_company_names > 0
   OR v.invalid_active_status > 0