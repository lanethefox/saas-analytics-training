-- REVENUE INVESTIGATION: Deep Dive into Zero MRR Issue
-- =====================================================

\echo '====================================='
\echo 'REVENUE INVESTIGATION: ZERO MRR ISSUE'
\echo '====================================='
\echo ''

-- Check staging layer for subscription data
\echo 'CHECKING STAGING LAYER SUBSCRIPTIONS:'
\echo '------------------------------------'

SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT subscription_id) as unique_subscriptions,
    MIN(monthly_recurring_revenue) as min_mrr,
    MAX(monthly_recurring_revenue) as max_mrr,
    AVG(monthly_recurring_revenue) as avg_mrr,
    SUM(monthly_recurring_revenue) as total_mrr,
    COUNT(CASE WHEN monthly_recurring_revenue > 0 THEN 1 END) as positive_mrr_count
FROM staging.stg_stripe__subscriptions
LIMIT 10;

-- Check if there's a mismatch between staging and entity
\echo ''
\echo 'COMPARING STAGING VS ENTITY SUBSCRIPTIONS:'
\echo '-----------------------------------------'

WITH staging_summary AS (
    SELECT 
        'staging' as layer,
        COUNT(*) as record_count,
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(monthly_recurring_revenue) as avg_mrr
    FROM staging.stg_stripe__subscriptions
),
entity_summary AS (
    SELECT 
        'entity' as layer,
        COUNT(*) as record_count,
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(monthly_recurring_revenue) as avg_mrr
    FROM entity.entity_subscriptions
)
SELECT * FROM staging_summary
UNION ALL
SELECT * FROM entity_summary;

-- Check customer-subscription relationship
\echo ''
\echo 'CUSTOMER-SUBSCRIPTION RELATIONSHIP CHECK:'
\echo '----------------------------------------'

WITH customer_sub_check AS (
    SELECT 
        c.account_id,
        c.company_name,
        c.monthly_recurring_revenue as customer_mrr,
        COUNT(s.subscription_id) as subscription_count,
        SUM(s.monthly_recurring_revenue) as total_sub_mrr
    FROM entity.entity_customers c
    LEFT JOIN entity.entity_subscriptions s 
        ON c.account_id::varchar = s.account_id::varchar
    GROUP BY c.account_id, c.company_name, c.monthly_recurring_revenue
)
SELECT 
    COUNT(*) as total_customers,
    SUM(CASE WHEN subscription_count = 0 THEN 1 ELSE 0 END) as customers_no_subs,
    SUM(CASE WHEN subscription_count > 0 THEN 1 ELSE 0 END) as customers_with_subs,
    SUM(CASE WHEN customer_mrr = 0 AND total_sub_mrr > 0 THEN 1 ELSE 0 END) as mrr_mismatch_count
FROM customer_sub_check;

-- Sample of customers with their subscription details
\echo ''
\echo 'SAMPLE CUSTOMER-SUBSCRIPTION DETAILS:'
\echo '------------------------------------'

SELECT 
    c.account_id,
    c.company_name,
    c.customer_tier,
    c.monthly_recurring_revenue as customer_mrr,
    COUNT(s.subscription_id) as sub_count,
    STRING_AGG(s.subscription_status, ', ') as sub_statuses,
    SUM(s.monthly_recurring_revenue) as total_sub_mrr
FROM entity.entity_customers c
LEFT JOIN entity.entity_subscriptions s 
    ON c.account_id::varchar = s.account_id::varchar
GROUP BY c.account_id, c.company_name, c.customer_tier, c.monthly_recurring_revenue
ORDER BY c.account_id
LIMIT 20;

-- Check for data type issues
\echo ''
\echo 'DATA TYPE INVESTIGATION:'
\echo '-----------------------'

SELECT 
    'entity_customers.account_id' as column_name,
    pg_typeof(account_id) as data_type
FROM entity.entity_customers
LIMIT 1
UNION ALL
SELECT 
    'entity_subscriptions.account_id',
    pg_typeof(account_id)
FROM entity.entity_subscriptions
LIMIT 1;

-- Check subscription MRR distribution
\echo ''
\echo 'SUBSCRIPTION MRR DISTRIBUTION:'
\echo '-----------------------------'

SELECT 
    subscription_status,
    COUNT(*) as count,
    MIN(monthly_recurring_revenue) as min_mrr,
    MAX(monthly_recurring_revenue) as max_mrr,
    AVG(monthly_recurring_revenue) as avg_mrr,
    SUM(monthly_recurring_revenue) as total_mrr
FROM entity.entity_subscriptions
GROUP BY subscription_status
ORDER BY count DESC;

-- Check if intermediate layer has correct calculations
\echo ''
\echo 'CHECKING INTERMEDIATE LAYER:'
\echo '---------------------------'

SELECT 
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'intermediate'
    AND table_name LIKE '%customer%'
ORDER BY table_name
LIMIT 10;
