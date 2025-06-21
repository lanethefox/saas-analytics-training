-- Module 1: SaaS Fundamentals - Practice Exercises
-- Work through these exercises to master Entity-Centric Modeling

-- ============================================
-- EXERCISE 1: Customer Health Dashboard
-- ============================================
-- Build a comprehensive dashboard for Customer Success teams
-- Requirements:
-- 1. Show all active customers
-- 2. Include health score, churn risk, and MRR
-- 3. Calculate user adoption rate
-- 4. Identify customers needing intervention
-- 5. Sort by priority (highest risk first)

-- YOUR QUERY HERE:
-- Hint: Start with SELECT from entity_customers
-- Add calculated fields for adoption rates
-- Use CASE statements for risk categorization




-- ============================================
-- EXERCISE 2: MRR Growth Analysis
-- ============================================
-- Analyze MRR growth patterns
-- Requirements:
-- 1. Calculate MRR by customer tier
-- 2. Show new vs expansion vs churned MRR
-- 3. Include customer counts
-- 4. Calculate average MRR per tier

-- YOUR QUERY HERE:
-- Hint: Use GROUP BY customer_tier
-- Consider using FILTER or CASE for MRR categories




-- ============================================
-- EXERCISE 3: Engagement Segmentation
-- ============================================
-- Segment customers by engagement level
-- Requirements:
-- 1. Define engagement tiers based on active users %
-- 2. Calculate average health score per tier
-- 3. Show revenue distribution
-- 4. Identify upsell opportunities

-- YOUR QUERY HERE:
-- Hint: Use CASE to create engagement tiers
-- Join with benchmarks using CTEs




-- ============================================
-- EXERCISE 4: Churn Risk Identification
-- ============================================
-- Identify customers at risk of churning
-- Requirements:
-- 1. Find customers with declining usage
-- 2. Include those with low engagement
-- 3. Calculate potential revenue loss
-- 4. Suggest intervention strategies

-- YOUR QUERY HERE:
-- Hint: Look for zero usage, low adoption
-- Use multiple conditions in WHERE




-- ============================================
-- EXERCISE 5: Expansion Opportunity Finder
-- ============================================
-- Find customers ready for tier upgrades
-- Requirements:
-- 1. Compare usage to tier benchmarks
-- 2. Only include healthy customers
-- 3. Calculate potential revenue increase
-- 4. Rank by opportunity size

-- YOUR QUERY HERE:
-- Hint: Use percentiles to find benchmarks
-- Filter for health_score > 70




-- ============================================
-- SOLUTIONS BELOW (Try exercises first!)
-- ============================================

-- SOLUTION 1: Customer Health Dashboard
SELECT 
    -- Customer Identity
    company_name,
    customer_tier,
    industry,
    
    -- Financial Metrics
    monthly_recurring_revenue as mrr,
    annual_recurring_revenue as arr,
    
    -- Health Indicators
    customer_health_score,
    churn_risk_score,
    CASE 
        WHEN churn_risk_score >= 70 THEN '🔴 Critical Risk'
        WHEN churn_risk_score >= 50 THEN '🟡 Warning'
        ELSE '🟢 Healthy'
    END as risk_level,
    
    -- Usage Metrics
    total_users,
    active_users_30d,
    ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as user_adoption_rate,
    device_events_30d,
    
    -- Engagement Signals
    DATE_PART('day', CURRENT_DATE - last_user_activity) as days_since_login,
    DATE_PART('day', CURRENT_DATE - last_device_activity) as days_since_usage,
    
    -- Intervention Priority
    CASE 
        WHEN device_events_30d = 0 THEN 'Immediate: No usage detected'
        WHEN churn_risk_score >= 70 THEN 'Urgent: High churn risk'
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) < 0.3 THEN 'High: Low adoption'
        WHEN customer_health_score < 60 THEN 'Medium: Poor health'
        ELSE 'Monitor'
    END as intervention_needed
    
FROM entity.entity_customers
WHERE customer_status = 'active'
ORDER BY 
    CASE 
        WHEN device_events_30d = 0 THEN 1
        WHEN churn_risk_score >= 70 THEN 2
        WHEN churn_risk_score >= 50 THEN 3
        ELSE 4
    END,
    monthly_recurring_revenue DESC;

-- SOLUTION 2: MRR Growth Analysis  
WITH tier_metrics AS (
    SELECT 
        customer_tier,
        CASE customer_tier
            WHEN 1 THEN 'Starter'
            WHEN 2 THEN 'Business'  
            WHEN 3 THEN 'Enterprise'
        END as tier_name,
        
        -- Customer counts
        COUNT(*) as total_customers,
        COUNT(CASE WHEN days_since_creation <= 30 THEN 1 END) as new_customers,
        
        -- MRR metrics
        SUM(monthly_recurring_revenue) as total_mrr,
        SUM(CASE WHEN days_since_creation <= 30 THEN monthly_recurring_revenue END) as new_mrr,
        SUM(CASE 
            WHEN previous_mrr IS NOT NULL AND monthly_recurring_revenue > previous_mrr 
            THEN monthly_recurring_revenue - previous_mrr 
        END) as expansion_mrr,
        
        -- Averages
        ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
        ROUND(AVG(customer_health_score), 1) as avg_health_score,
        ROUND(AVG(churn_risk_score), 1) as avg_churn_risk
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
    GROUP BY customer_tier
)
SELECT 
    tier_name,
    total_customers,
    new_customers,
    total_mrr,
    new_mrr,
    expansion_mrr,
    avg_mrr,
    avg_health_score,
    avg_churn_risk,
    ROUND(total_mrr::numeric / SUM(total_mrr) OVER () * 100, 1) as mrr_percentage
FROM tier_metrics
ORDER BY customer_tier;

-- SOLUTION 3: Engagement Segmentation
WITH engagement_segments AS (
    SELECT 
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        
        -- Engagement calculation
        total_users,
        active_users_30d,
        ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as user_adoption_pct,
        
        -- Engagement tier
        CASE 
            WHEN active_users_30d::numeric / NULLIF(total_users, 0) >= 0.8 THEN 'Power Users'
            WHEN active_users_30d::numeric / NULLIF(total_users, 0) >= 0.6 THEN 'Engaged'
            WHEN active_users_30d::numeric / NULLIF(total_users, 0) >= 0.4 THEN 'Moderate'
            WHEN active_users_30d::numeric / NULLIF(total_users, 0) >= 0.2 THEN 'Low'
            ELSE 'Disengaged'
        END as engagement_tier,
        
        -- Health metrics
        customer_health_score,
        churn_risk_score,
        
        -- Opportunity sizing
        CASE 
            WHEN customer_tier < 3 AND active_users_30d::numeric / NULLIF(total_users, 0) >= 0.8 
                THEN 'High Usage → Upsell'
            WHEN active_users_30d::numeric / NULLIF(total_users, 0) < 0.4 
                THEN 'Low Usage → Activation'
            ELSE 'Maintain'
        END as opportunity_type
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
        AND total_users > 0
)
SELECT 
    engagement_tier,
    COUNT(*) as customer_count,
    SUM(monthly_recurring_revenue) as total_mrr,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
    ROUND(AVG(user_adoption_pct), 1) as avg_adoption_pct,
    ROUND(AVG(customer_health_score), 1) as avg_health_score,
    ROUND(AVG(churn_risk_score), 1) as avg_churn_risk,
    COUNT(CASE WHEN opportunity_type = 'High Usage → Upsell' THEN 1 END) as upsell_opportunities,
    COUNT(CASE WHEN opportunity_type = 'Low Usage → Activation' THEN 1 END) as activation_opportunities
FROM engagement_segments
GROUP BY engagement_tier
ORDER BY 
    CASE engagement_tier
        WHEN 'Power Users' THEN 1
        WHEN 'Engaged' THEN 2
        WHEN 'Moderate' THEN 3
        WHEN 'Low' THEN 4
        ELSE 5
    END;

-- SOLUTION 4: Churn Risk Identification
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue,
    annual_recurring_revenue,
    
    -- Risk scores
    customer_health_score,
    churn_risk_score,
    
    -- Usage decline indicators
    device_events_30d,
    device_events_7d,
    CASE 
        WHEN device_events_30d = 0 THEN 'Zero Usage'
        WHEN device_events_7d = 0 THEN 'Recent Drop-off'
        ELSE 'Active'
    END as usage_status,
    
    -- Engagement metrics
    total_users,
    active_users_30d,
    ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as adoption_rate,
    
    -- Time-based risks
    DATE_PART('day', CURRENT_DATE - last_user_activity) as days_inactive,
    DATE_PART('day', CURRENT_DATE - created_at) as customer_age_days,
    
    -- Risk categorization
    CASE 
        WHEN device_events_30d = 0 THEN 'No Usage - Immediate Risk'
        WHEN DATE_PART('day', CURRENT_DATE - last_user_activity) > 14 THEN 'User Abandonment'
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) < 0.2 THEN 'Low Adoption'
        WHEN churn_risk_score >= 70 THEN 'High Risk Score'
        ELSE 'Moderate Risk'
    END as primary_risk_factor,
    
    -- Intervention strategy
    CASE 
        WHEN device_events_30d = 0 THEN 'Executive call + technical audit'
        WHEN DATE_PART('day', CURRENT_DATE - last_user_activity) > 14 THEN 'Re-engagement campaign + training'
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) < 0.2 THEN 'User adoption workshop'
        WHEN churn_risk_score >= 70 THEN 'Proactive success manager outreach'
        ELSE 'Regular check-in'
    END as recommended_action,
    
    -- Financial impact
    monthly_recurring_revenue as mrr_at_risk,
    monthly_recurring_revenue * 12 as arr_at_risk
    
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND (
    churn_risk_score >= 50
    OR device_events_30d = 0
    OR active_users_30d::numeric / NULLIF(total_users, 0) < 0.3
    OR DATE_PART('day', CURRENT_DATE - last_user_activity) > 7
  )
ORDER BY 
    CASE 
        WHEN device_events_30d = 0 THEN 1
        ELSE 2
    END,
    monthly_recurring_revenue DESC
LIMIT 50;

-- SOLUTION 5: Expansion Opportunity Finder
WITH usage_benchmarks AS (
    -- Calculate P75 usage by tier as upgrade threshold
    SELECT 
        customer_tier,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_devices) as tier_p75_devices,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_users) as tier_p75_users,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY device_events_30d) as tier_p75_events,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_locations) as tier_p75_locations
    FROM entity.entity_customers
    WHERE customer_status = 'active'
    GROUP BY customer_tier
),
expansion_candidates AS (
    SELECT 
        c.company_name,
        c.customer_tier,
        c.monthly_recurring_revenue as current_mrr,
        
        -- Current usage
        c.total_devices,
        c.total_users,
        c.total_locations,
        c.device_events_30d,
        
        -- Usage vs benchmarks
        ROUND(c.total_devices::numeric / NULLIF(b.tier_p75_devices, 0), 2) as device_usage_ratio,
        ROUND(c.total_users::numeric / NULLIF(b.tier_p75_users, 0), 2) as user_usage_ratio,
        
        -- Health check
        c.customer_health_score,
        c.churn_risk_score,
        c.days_since_creation,
        
        -- Expansion potential
        CASE 
            WHEN c.customer_tier = 1 AND (
                c.total_devices > b.tier_p75_devices OR 
                c.total_users > b.tier_p75_users OR
                c.device_events_30d > b.tier_p75_events
            ) THEN 999 - c.monthly_recurring_revenue
            WHEN c.customer_tier = 2 AND (
                c.total_devices > b.tier_p75_devices OR 
                c.total_users > b.tier_p75_users OR
                c.device_events_30d > b.tier_p75_events
            ) THEN 4999 - c.monthly_recurring_revenue
            ELSE 0
        END as potential_mrr_increase,
        
        -- Expansion signals
        CASE 
            WHEN c.total_devices > b.tier_p75_devices THEN 'High Device Usage'
            WHEN c.total_users > b.tier_p75_users THEN 'High User Count'
            WHEN c.device_events_30d > b.tier_p75_events THEN 'High Activity Volume'
            WHEN c.total_locations > b.tier_p75_locations THEN 'Multi-Location Growth'
            ELSE 'Within Tier Norms'
        END as primary_growth_driver,
        
        -- Next tier name
        CASE c.customer_tier
            WHEN 1 THEN 'Business'
            WHEN 2 THEN 'Enterprise'
            ELSE 'Max Tier'
        END as recommended_tier
        
    FROM entity.entity_customers c
    JOIN usage_benchmarks b ON c.customer_tier = b.customer_tier
    WHERE c.customer_status = 'active'
      AND c.customer_health_score > 70  -- Healthy customers only
      AND c.churn_risk_score < 40       -- Low churn risk
      AND c.days_since_creation > 90    -- Established relationship
      AND c.customer_tier < 3           -- Not already Enterprise
)
SELECT 
    company_name,
    customer_tier as current_tier,
    recommended_tier,
    current_mrr,
    potential_mrr_increase,
    current_mrr + potential_mrr_increase as potential_new_mrr,
    
    -- Usage metrics
    total_devices,
    total_users,
    device_events_30d,
    
    -- Usage ratios (>1 means above tier average)
    device_usage_ratio,
    user_usage_ratio,
    
    -- Growth driver
    primary_growth_driver,
    
    -- Health check
    customer_health_score,
    churn_risk_score,
    
    -- Sales talking points
    CASE primary_growth_driver
        WHEN 'High Device Usage' THEN 'Unlock unlimited devices with ' || recommended_tier
        WHEN 'High User Count' THEN 'Add unlimited users with ' || recommended_tier  
        WHEN 'High Activity Volume' THEN 'Handle any volume with ' || recommended_tier
        WHEN 'Multi-Location Growth' THEN 'Manage all locations centrally with ' || recommended_tier
    END as sales_message
    
FROM expansion_candidates
WHERE potential_mrr_increase > 0
ORDER BY potential_mrr_increase DESC
LIMIT 25;