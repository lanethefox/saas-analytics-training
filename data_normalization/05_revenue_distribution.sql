-- 05_revenue_distribution.sql
-- Phase 2: Distribute Revenue Realistically Across Customers
-- =========================================================
-- Fix the zero MRR issue and create realistic revenue distributions

-- Create revenue distribution functions
CREATE OR REPLACE FUNCTION normalized.generate_lognormal_random(log_mean NUMERIC, log_stddev NUMERIC) 
RETURNS NUMERIC AS $$
BEGIN
    RETURN exp(normalized.generate_normal_random(log_mean, log_stddev));
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- Step 1: Analyze Current State
-- ========================================

\echo 'CURRENT REVENUE STATE ANALYSIS'
\echo '=============================='
\echo ''
\echo 'Customer Tier Distribution:'

SELECT 
    customer_tier,
    COUNT(*) as customer_count,
    COUNT(CASE WHEN monthly_recurring_revenue > 0 THEN 1 END) as with_revenue,
    SUM(monthly_recurring_revenue) as total_mrr
FROM normalized.customers
GROUP BY customer_tier
ORDER BY customer_tier;

\echo ''
\echo 'Subscription Revenue by Status:'

SELECT 
    subscription_status,
    COUNT(*) as count,
    SUM(monthly_recurring_revenue) as total_mrr,
    AVG(monthly_recurring_revenue) as avg_mrr
FROM normalized.subscriptions
GROUP BY subscription_status
ORDER BY total_mrr DESC;

-- ========================================
-- Step 2: Create Tier-Based MRR Targets
-- ========================================

-- Create a temporary table with tier-based revenue parameters
DROP TABLE IF EXISTS normalized.tier_revenue_params;
CREATE TABLE normalized.tier_revenue_params (
    tier INTEGER PRIMARY KEY,
    min_mrr NUMERIC,
    max_mrr NUMERIC,
    log_mean NUMERIC,
    log_stddev NUMERIC,
    target_avg_mrr NUMERIC
);

INSERT INTO normalized.tier_revenue_params VALUES
    (1, 5000, 50000, 9.5, 0.8, 15000),  -- Enterprise
    (2, 1000, 5000, 7.8, 0.6, 2500),    -- Professional  
    (3, 200, 1000, 6.2, 0.5, 500),      -- Growth
    (4, 50, 200, 4.5, 0.4, 100);        -- Starter

-- ========================================
-- Step 3: Update Customer Tiers Based on Existing Subscriptions
-- ========================================

-- First, properly assign tiers based on subscription values
WITH customer_subscription_summary AS (
    SELECT 
        c.account_id,
        COUNT(s.subscription_id) as sub_count,
        SUM(CASE WHEN s.subscription_status IN ('Active', 'active') 
            THEN s.monthly_recurring_revenue ELSE 0 END) as active_mrr,
        MAX(CASE WHEN s.subscription_status IN ('Active', 'active') 
            THEN s.monthly_recurring_revenue ELSE 0 END) as max_sub_mrr
    FROM normalized.customers c
    LEFT JOIN normalized.subscriptions s ON c.account_id = s.account_id
    GROUP BY c.account_id
)
UPDATE normalized.customers c
SET customer_tier = CASE 
    WHEN css.active_mrr >= 5000 THEN 1
    WHEN css.active_mrr >= 1000 THEN 2
    WHEN css.active_mrr >= 200 THEN 3
    ELSE 4
END
FROM customer_subscription_summary css
WHERE c.account_id = css.account_id
  AND css.active_mrr > 0;

-- ========================================
-- Step 4: Generate MRR for Customers Without Subscriptions
-- ========================================

-- For customers without linked subscriptions, generate appropriate MRR
UPDATE normalized.customers c
SET 
    monthly_recurring_revenue = LEAST(
        p.max_mrr,
        GREATEST(
            p.min_mrr,
            normalized.generate_lognormal_random(p.log_mean, p.log_stddev)
        )
    )
FROM normalized.tier_revenue_params p
WHERE c.customer_tier = p.tier
  AND NOT EXISTS (
    SELECT 1 FROM normalized.subscriptions s 
    WHERE s.account_id = c.account_id 
    AND s.subscription_status IN ('Active', 'active')
  );

-- ========================================
-- Step 5: Update MRR from Actual Subscriptions
-- ========================================

-- For customers with subscriptions, use actual subscription MRR
UPDATE normalized.customers c
SET 
    monthly_recurring_revenue = sub_summary.total_active_mrr,
    annual_recurring_revenue = sub_summary.total_active_mrr * 12,
    active_subscriptions = sub_summary.active_count,
    total_subscriptions = sub_summary.total_count
FROM (
    SELECT 
        account_id,
        SUM(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN monthly_recurring_revenue ELSE 0 END) as total_active_mrr,
        COUNT(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN 1 END) as active_count,
        COUNT(*) as total_count
    FROM normalized.subscriptions
    GROUP BY account_id
) sub_summary
WHERE c.account_id = sub_summary.account_id
  AND sub_summary.total_active_mrr > 0;

-- ========================================
-- Step 6: Handle Orphaned Subscriptions
-- ========================================

-- Create customers for high-value orphaned subscriptions
INSERT INTO normalized.customers (
    account_id,
    company_name,
    industry,
    customer_tier,
    customer_status,
    created_at,
    monthly_recurring_revenue,
    annual_recurring_revenue,
    active_subscriptions,
    total_subscriptions,
    customer_health_score
)
SELECT 
    s.account_id,
    'Recovered Company - ' || s.account_id,
    CASE (random() * 5)::INT 
        WHEN 0 THEN 'Technology'
        WHEN 1 THEN 'Retail'
        WHEN 2 THEN 'Healthcare'
        WHEN 3 THEN 'Financial Services'
        ELSE 'Other'
    END,
    CASE 
        WHEN total_mrr >= 5000 THEN 1
        WHEN total_mrr >= 1000 THEN 2
        WHEN total_mrr >= 200 THEN 3
        ELSE 4
    END,
    'active',
    CURRENT_DATE - INTERVAL '180 days',
    total_mrr,
    total_mrr * 12,
    active_count,
    total_count,
    75 -- Default health score
FROM (
    SELECT 
        account_id,
        SUM(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN monthly_recurring_revenue ELSE 0 END) as total_mrr,
        COUNT(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN 1 END) as active_count,
        COUNT(*) as total_count
    FROM normalized.subscriptions
    WHERE account_id LIKE 'ACC_ORPHANED_%'
    GROUP BY account_id
    HAVING SUM(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN monthly_recurring_revenue ELSE 0 END) > 0
) orphaned_valuable;

-- ========================================
-- Step 7: Add Revenue Variance and Growth
-- ========================================

-- Add some realistic variance to revenue (±10%)
UPDATE normalized.customers
SET 
    monthly_recurring_revenue = monthly_recurring_revenue * 
        (1 + (random() - 0.5) * 0.2)
WHERE monthly_recurring_revenue > 0;

-- Ensure ARR = MRR * 12
UPDATE normalized.customers
SET annual_recurring_revenue = monthly_recurring_revenue * 12;

-- ========================================
-- Step 8: Update Related Financial Metrics
-- ========================================

UPDATE normalized.customers
SET 
    -- Customer health score based on revenue and tier
    customer_health_score = CASE 
        WHEN customer_tier = 1 THEN normalized.generate_normal_random(85, 10)
        WHEN customer_tier = 2 THEN normalized.generate_normal_random(75, 12)
        WHEN customer_tier = 3 THEN normalized.generate_normal_random(65, 15)
        ELSE normalized.generate_normal_random(55, 18)
    END,
    
    -- Growth trajectory
    growth_trajectory = CASE 
        WHEN customer_tier <= 2 THEN normalized.generate_normal_random(15, 10)
        ELSE normalized.generate_normal_random(5, 15)
    END,
    
    -- Expansion score
    expansion_score = CASE 
        WHEN customer_tier = 4 THEN normalized.generate_normal_random(70, 20)
        WHEN customer_tier = 3 THEN normalized.generate_normal_random(50, 20)
        ELSE normalized.generate_normal_random(30, 15)
    END,
    
    -- Retention score
    retention_score = CASE 
        WHEN customer_tier = 1 THEN normalized.generate_normal_random(90, 8)
        WHEN customer_tier = 2 THEN normalized.generate_normal_random(80, 12)
        WHEN customer_tier = 3 THEN normalized.generate_normal_random(70, 15)
        ELSE normalized.generate_normal_random(60, 20)
    END,
    
    -- Payment reliability
    payment_reliability_score = CASE 
        WHEN customer_tier <= 2 THEN normalized.generate_normal_random(95, 5)
        ELSE normalized.generate_normal_random(85, 15)
    END,
    
    -- Churn risk (inverse of tier)
    churn_risk_score = CASE 
        WHEN customer_tier = 1 THEN normalized.generate_normal_random(10, 8)
        WHEN customer_tier = 2 THEN normalized.generate_normal_random(20, 12)
        WHEN customer_tier = 3 THEN normalized.generate_normal_random(35, 15)
        ELSE normalized.generate_normal_random(50, 20)
    END,
    
    -- Lifetime value prediction
    lifetime_value_predicted = monthly_recurring_revenue * 
        CASE 
            WHEN customer_tier = 1 THEN normalized.generate_normal_random(48, 12) -- 4 years
            WHEN customer_tier = 2 THEN normalized.generate_normal_random(36, 12) -- 3 years
            WHEN customer_tier = 3 THEN normalized.generate_normal_random(24, 12) -- 2 years
            ELSE normalized.generate_normal_random(12, 8) -- 1 year
        END;

-- ========================================
-- Generate Revenue Summary Report
-- ========================================

\echo ''
\echo 'REVENUE DISTRIBUTION SUMMARY'
\echo '============================'
\echo ''
\echo 'Revenue by Customer Tier:'

SELECT 
    customer_tier,
    COUNT(*) as customer_count,
    COUNT(CASE WHEN monthly_recurring_revenue > 0 THEN 1 END) as revenue_customers,
    MIN(monthly_recurring_revenue) as min_mrr,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
    MAX(monthly_recurring_revenue) as max_mrr,
    ROUND(SUM(monthly_recurring_revenue), 2) as total_mrr
FROM normalized.customers
GROUP BY customer_tier
ORDER BY customer_tier;

\echo ''
\echo 'Overall Revenue Metrics:'

SELECT 
    COUNT(*) as total_customers,
    COUNT(CASE WHEN monthly_recurring_revenue > 0 THEN 1 END) as revenue_customers,
    ROUND(SUM(monthly_recurring_revenue), 2) as total_mrr,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_recurring_revenue), 2) as median_mrr
FROM normalized.customers;

\echo ''
\echo 'Customer Health by Tier:'

SELECT 
    customer_tier,
    ROUND(AVG(customer_health_score), 2) as avg_health,
    ROUND(AVG(churn_risk_score), 2) as avg_churn_risk,
    ROUND(AVG(retention_score), 2) as avg_retention,
    ROUND(AVG(expansion_score), 2) as avg_expansion
FROM normalized.customers
GROUP BY customer_tier
ORDER BY customer_tier;

-- Clean up
DROP TABLE IF EXISTS normalized.tier_revenue_params;
DROP FUNCTION IF EXISTS normalized.generate_lognormal_random(NUMERIC, NUMERIC);

\echo ''
\echo 'Revenue distribution completed successfully!'
