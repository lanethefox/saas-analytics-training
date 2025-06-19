-- Test Stripe staging models for payment data integrity
WITH stripe_validation AS (
    -- Check stripe customers
    SELECT 
        'customers' AS entity_type,
        COUNT(*) AS total_records,
        SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN email IS NULL OR email NOT LIKE '%@%' THEN 1 ELSE 0 END) AS invalid_emails,
        SUM(CASE WHEN created > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_dates
    FROM {{ ref('stg_stripe__customers') }}
    
    UNION ALL
    
    -- Check stripe subscriptions
    SELECT 
        'subscriptions' AS entity_type,
        COUNT(*) AS total_records,
        SUM(CASE WHEN subscription_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN status NOT IN ('active', 'canceled', 'incomplete', 'incomplete_expired', 'past_due', 'trialing', 'unpaid') THEN 1 ELSE 0 END) AS invalid_emails,
        SUM(CASE WHEN created > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_dates
    FROM {{ ref('stg_stripe__subscriptions') }}
    
    UNION ALL
    
    -- Check stripe charges  
    SELECT 
        'charges' AS entity_type,
        COUNT(*) AS total_records,
        SUM(CASE WHEN charge_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END) AS invalid_emails,
        SUM(CASE WHEN created > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_dates
    FROM {{ ref('stg_stripe__charges') }}
),
stripe_issues AS (
    SELECT *
    FROM stripe_validation
    WHERE null_ids > 0
       OR invalid_emails > 0
       OR future_dates > 0
)
-- Test fails if Stripe data has quality issues
SELECT * FROM stripe_issues