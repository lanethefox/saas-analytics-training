-- Advanced Business Scenarios: Strategic Analytics
-- These queries answer complex cross-functional business questions

-- ============================================
-- SCENARIO 4: "What's our path to $100M ARR?"
-- ============================================
-- Strategic growth planning with multiple paths to target

WITH current_state AS (
    SELECT 
        -- Current metrics
        SUM(annual_recurring_revenue) as current_arr,
        COUNT(*) as total_customers,
        COUNT(CASE WHEN customer_tier = 1 THEN 1 END) as starter_customers,
        COUNT(CASE WHEN customer_tier = 2 THEN 1 END) as business_customers,
        COUNT(CASE WHEN customer_tier = 3 THEN 1 END) as enterprise_customers,
        
        -- Average values by tier
        AVG(CASE WHEN customer_tier = 1 THEN annual_recurring_revenue END) as avg_starter_arr,
        AVG(CASE WHEN customer_tier = 2 THEN annual_recurring_revenue END) as avg_business_arr,
        AVG(CASE WHEN customer_tier = 3 THEN annual_recurring_revenue END) as avg_enterprise_arr,
        
        -- Growth rates (simplified - would use history table in production)
        COUNT(CASE WHEN days_since_creation <= 30 THEN 1 END) as new_customers_monthly,
        SUM(CASE WHEN days_since_creation <= 30 THEN annual_recurring_revenue END) as new_arr_monthly
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
),
growth_scenarios AS (
    SELECT 
        current_arr,
        100000000 - current_arr as arr_gap,
        
        -- Scenario 1: Maintain current mix
        ROUND((100000000 - current_arr) / (new_arr_monthly * 12), 1) as years_at_current_rate,
        
        -- Scenario 2: Focus on Enterprise (3x ARR per customer)
        ROUND((100000000 - current_arr) / avg_enterprise_arr) as enterprise_customers_needed,
        
        -- Scenario 3: Expand existing base
        ROUND((100000000 - current_arr) / total_customers) as arr_increase_per_customer,
        
        -- Current distribution
        starter_customers,
        business_customers,
        enterprise_customers,
        total_customers
        
    FROM current_state
)
SELECT 
    -- Current state
    ROUND(current_arr / 1000000, 1) as current_arr_millions,
    ROUND(arr_gap / 1000000, 1) as gap_to_100m,
    
    -- Growth paths
    years_at_current_rate as path1_years_at_current_growth,
    
    enterprise_customers_needed as path2_new_enterprise_needed,
    ROUND(enterprise_customers_needed / 12.0, 1) as path2_enterprise_per_month,
    
    ROUND(arr_increase_per_customer / 12, 0) as path3_mrr_increase_per_customer,
    ROUND(arr_increase_per_customer / current_arr * 100, 1) as path3_percent_increase_needed,
    
    -- Blended approach recommendation
    'Recommended Strategy:' as strategy,
    '1. Increase Enterprise acquisitions to ' || ROUND(enterprise_customers_needed / 36.0, 1) || ' per month' as recommendation_1,
    '2. Expand existing Enterprise customers by 20% ($' || ROUND(arr_gap * 0.3 / enterprise_customers, 0) || ' ARR each)' as recommendation_2,
    '3. Convert top 10% of Business tier to Enterprise' as recommendation_3,
    '4. Reduce churn by 2% to retain $' || ROUND(current_arr * 0.02 / 1000000, 1) || 'M ARR' as recommendation_4
    
FROM growth_scenarios;

-- Detailed growth lever analysis
WITH growth_levers AS (
    SELECT 
        -- New customer acquisition
        COUNT(CASE WHEN days_since_creation <= 365 AND customer_tier = 3 THEN 1 END) as enterprise_acquired_yearly,
        AVG(CASE WHEN customer_tier = 3 THEN annual_recurring_revenue END) as avg_enterprise_arr,
        
        -- Expansion candidates
        COUNT(CASE 
            WHEN customer_tier = 2 
            AND customer_health_score > 70 
            AND (total_devices > 30 OR total_users > 75) 
            THEN 1 
        END) as business_to_enterprise_candidates,
        
        COUNT(CASE 
            WHEN customer_tier = 1 
            AND customer_health_score > 70 
            AND (total_devices > 10 OR total_users > 25) 
            THEN 1 
        END) as starter_to_business_candidates,
        
        -- Churn impact
        COUNT(CASE WHEN churn_risk_score > 60 THEN 1 END) as at_risk_customers,
        SUM(CASE WHEN churn_risk_score > 60 THEN annual_recurring_revenue END) as arr_at_risk,
        
        -- Usage-based expansion
        COUNT(CASE 
            WHEN device_events_30d > 50000 AND customer_tier < 3 
            THEN 1 
        END) as usage_based_expansion_candidates
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
)
SELECT 
    'Growth Lever Analysis' as analysis_type,
    
    -- Acquisition impact
    enterprise_acquired_yearly as current_enterprise_acquisition_rate,
    ROUND(enterprise_acquired_yearly * 2.5 * avg_enterprise_arr / 1000000, 1) as acquisition_acceleration_impact_millions,
    
    -- Tier upgrade impact  
    business_to_enterprise_candidates as b2e_upgrade_pipeline,
    ROUND(business_to_enterprise_candidates * 40000 / 1000000, 1) as b2e_upgrade_impact_millions,
    
    starter_to_business_candidates as s2b_upgrade_pipeline,
    ROUND(starter_to_business_candidates * 8000 / 1000000, 1) as s2b_upgrade_impact_millions,
    
    -- Retention impact
    at_risk_customers as customers_at_risk,
    ROUND(arr_at_risk / 1000000, 1) as arr_at_risk_millions,
    ROUND(arr_at_risk * 0.5 / 1000000, 1) as retention_improvement_impact_millions,
    
    -- Total achievable growth
    ROUND(
        (enterprise_acquired_yearly * 2.5 * avg_enterprise_arr +
         business_to_enterprise_candidates * 40000 +
         starter_to_business_candidates * 8000 +
         arr_at_risk * 0.5) / 1000000
    , 1) as total_achievable_growth_millions
    
FROM growth_levers;

-- ============================================
-- SCENARIO 5: "How do we optimize unit economics?"
-- ============================================
-- Deep dive into profitability drivers by segment

WITH unit_economics AS (
    SELECT 
        company_name,
        customer_tier,
        industry,
        
        -- Revenue metrics
        monthly_recurring_revenue as mrr,
        annual_recurring_revenue as arr,
        
        -- Usage intensity
        total_users,
        active_users_30d,
        total_devices,
        total_locations,
        device_events_30d,
        
        -- Efficiency scores
        ROUND(device_events_30d::numeric / NULLIF(monthly_recurring_revenue, 0), 2) as events_per_dollar,
        ROUND(monthly_recurring_revenue::numeric / NULLIF(total_devices, 0), 2) as mrr_per_device,
        ROUND(monthly_recurring_revenue::numeric / NULLIF(active_users_30d, 0), 2) as mrr_per_active_user,
        ROUND(device_events_30d::numeric / NULLIF(total_devices, 0), 1) as events_per_device,
        
        -- Support burden (proxy for cost)
        support_tickets_30d,
        ROUND(support_tickets_30d::numeric / NULLIF(monthly_recurring_revenue, 0) * 100, 2) as support_cost_ratio,
        
        -- Estimated margins (simplified model)
        CASE 
            WHEN device_events_30d / NULLIF(monthly_recurring_revenue, 0) > 100 THEN 'Low Margin - High Usage'
            WHEN support_tickets_30d / NULLIF(monthly_recurring_revenue, 0) > 0.05 THEN 'Low Margin - High Support'
            WHEN total_devices / NULLIF(monthly_recurring_revenue, 0) > 0.1 THEN 'Low Margin - Over-provisioned'
            WHEN monthly_recurring_revenue > 5000 AND support_tickets_30d < 5 THEN 'High Margin - Efficient'
            ELSE 'Standard Margin'
        END as margin_category,
        
        -- Health and retention
        customer_health_score,
        churn_risk_score,
        customer_lifetime_days
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
)
SELECT 
    margin_category,
    customer_tier,
    COUNT(*) as customer_count,
    
    -- Revenue metrics
    ROUND(AVG(mrr), 2) as avg_mrr,
    SUM(mrr) as total_mrr,
    
    -- Usage efficiency
    ROUND(AVG(events_per_dollar), 2) as avg_events_per_dollar,
    ROUND(AVG(mrr_per_device), 2) as avg_mrr_per_device,
    ROUND(AVG(mrr_per_active_user), 2) as avg_mrr_per_active_user,
    
    -- Support efficiency
    ROUND(AVG(support_tickets_30d), 1) as avg_support_tickets,
    ROUND(AVG(support_cost_ratio), 2) as avg_support_cost_ratio,
    
    -- Retention metrics
    ROUND(AVG(customer_health_score), 1) as avg_health_score,
    ROUND(AVG(churn_risk_score), 1) as avg_churn_risk,
    ROUND(AVG(customer_lifetime_days), 0) as avg_lifetime_days,
    
    -- Optimization recommendations
    CASE margin_category
        WHEN 'Low Margin - High Usage' THEN 'Implement usage-based pricing tiers'
        WHEN 'Low Margin - High Support' THEN 'Invest in self-service and automation'
        WHEN 'Low Margin - Over-provisioned' THEN 'Right-size infrastructure per customer'
        WHEN 'High Margin - Efficient' THEN 'Use as model for other segments'
        ELSE 'Analyze individual outliers'
    END as optimization_strategy,
    
    -- Financial impact
    CASE margin_category
        WHEN 'Low Margin - High Usage' THEN ROUND(SUM(mrr) * 0.15, 0)
        WHEN 'Low Margin - High Support' THEN ROUND(SUM(mrr) * 0.10, 0)
        WHEN 'Low Margin - Over-provisioned' THEN ROUND(SUM(mrr) * 0.08, 0)
        ELSE 0
    END as potential_margin_improvement
    
FROM unit_economics
GROUP BY margin_category, customer_tier
ORDER BY total_mrr DESC;

-- ============================================
-- SCENARIO 6: "Which integration partners drive the most value?"
-- ============================================
-- Analyze customer value by integration usage patterns

WITH integration_analysis AS (
    SELECT 
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        
        -- Integration indicators (using available proxy metrics)
        CASE 
            WHEN device_events_30d > 50000 THEN 'API Heavy User'
            WHEN total_locations > 10 THEN 'Multi-Location Integration'
            WHEN total_users > 50 THEN 'SSO/Directory Integration'
            WHEN avg_user_engagement_score > 85 THEN 'Deep Platform Integration'
            ELSE 'Basic Integration'
        END as integration_profile,
        
        -- Value metrics
        customer_lifetime_days,
        customer_health_score,
        churn_risk_score,
        device_events_30d,
        
        -- Calculate integration value score
        (CASE WHEN device_events_30d > 50000 THEN 25 ELSE 0 END +
         CASE WHEN total_locations > 10 THEN 25 ELSE 0 END +
         CASE WHEN total_users > 50 THEN 25 ELSE 0 END +
         CASE WHEN avg_user_engagement_score > 85 THEN 25 ELSE 0 END) as integration_depth_score
         
    FROM entity.entity_customers
    WHERE customer_status = 'active'
),
integration_value AS (
    SELECT 
        integration_profile,
        COUNT(*) as customer_count,
        
        -- Revenue impact
        SUM(monthly_recurring_revenue) as total_mrr,
        ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
        
        -- Retention impact
        ROUND(AVG(customer_lifetime_days), 0) as avg_lifetime_days,
        ROUND(AVG(customer_health_score), 1) as avg_health_score,
        ROUND(AVG(churn_risk_score), 1) as avg_churn_risk,
        
        -- Usage patterns
        ROUND(AVG(device_events_30d), 0) as avg_monthly_events,
        SUM(device_events_30d) as total_platform_events,
        
        -- Strategic value
        ROUND(AVG(integration_depth_score), 1) as avg_integration_score
        
    FROM integration_analysis
    GROUP BY integration_profile
)
SELECT 
    integration_profile,
    customer_count,
    total_mrr,
    avg_mrr,
    avg_lifetime_days,
    avg_health_score,
    avg_churn_risk,
    avg_monthly_events,
    
    -- Calculate relative value
    ROUND(avg_mrr / (SELECT AVG(monthly_recurring_revenue) FROM entity.entity_customers WHERE customer_status = 'active'), 2) as mrr_index,
    ROUND(avg_lifetime_days / (SELECT AVG(customer_lifetime_days) FROM entity.entity_customers WHERE customer_status = 'active'), 2) as retention_index,
    
    -- Strategic recommendations
    CASE integration_profile
        WHEN 'API Heavy User' THEN 'Develop advanced API features, usage-based pricing'
        WHEN 'Multi-Location Integration' THEN 'Build centralized management console'
        WHEN 'SSO/Directory Integration' THEN 'Expand enterprise security features'
        WHEN 'Deep Platform Integration' THEN 'Create integration marketplace'
        ELSE 'Improve onboarding to increase integration adoption'
    END as product_strategy,
    
    -- Partnership opportunities
    CASE integration_profile
        WHEN 'API Heavy User' THEN 'Partner with workflow automation platforms'
        WHEN 'Multi-Location Integration' THEN 'Partner with franchise management systems'
        WHEN 'SSO/Directory Integration' THEN 'Partner with identity providers'
        WHEN 'Deep Platform Integration' THEN 'Become platform partner for POS systems'
        ELSE 'Focus on basic integration templates'
    END as partnership_strategy
    
FROM integration_value
ORDER BY total_mrr DESC;

-- ============================================
-- SCENARIO 7: "How do we reduce customer acquisition cost?"
-- ============================================
-- Analyze characteristics of efficient customer acquisition

WITH customer_acquisition AS (
    SELECT 
        company_name,
        customer_tier,
        industry,
        
        -- Time to value metrics
        days_since_creation,
        CASE 
            WHEN device_events_30d > 1000 AND days_since_creation < 30 THEN 'Fast Activation'
            WHEN device_events_30d > 1000 AND days_since_creation < 90 THEN 'Normal Activation'
            WHEN device_events_30d > 1000 THEN 'Slow Activation'
            ELSE 'Not Activated'
        END as activation_speed,
        
        -- Early engagement indicators
        total_users,
        active_users_30d,
        total_devices,
        device_events_30d,
        
        -- Value metrics
        monthly_recurring_revenue,
        customer_health_score,
        
        -- Calculate acquisition efficiency score
        CASE 
            WHEN days_since_creation < 30 AND device_events_30d > 5000 THEN 'Highly Efficient'
            WHEN days_since_creation < 60 AND device_events_30d > 2500 THEN 'Efficient'
            WHEN days_since_creation < 90 AND device_events_30d > 1000 THEN 'Standard'
            ELSE 'Inefficient'
        END as acquisition_efficiency,
        
        -- Referral potential (high engagement + multi-location)
        CASE 
            WHEN avg_user_engagement_score > 80 AND total_locations > 1 THEN 'High Referral Potential'
            WHEN customer_health_score > 80 THEN 'Medium Referral Potential'
            ELSE 'Low Referral Potential'
        END as referral_potential
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
),
acquisition_insights AS (
    SELECT 
        acquisition_efficiency,
        activation_speed,
        COUNT(*) as customer_count,
        
        -- Revenue metrics
        ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
        SUM(monthly_recurring_revenue) as total_mrr,
        
        -- Activation metrics
        ROUND(AVG(CASE WHEN activation_speed = 'Fast Activation' THEN 1 ELSE 0 END) * 100, 1) as fast_activation_rate,
        ROUND(AVG(device_events_30d), 0) as avg_first_month_events,
        
        -- Quality metrics
        ROUND(AVG(customer_health_score), 1) as avg_health_score,
        COUNT(CASE WHEN referral_potential = 'High Referral Potential' THEN 1 END) as high_referral_count
        
    FROM customer_acquisition
    GROUP BY acquisition_efficiency, activation_speed
)
SELECT 
    acquisition_efficiency,
    SUM(customer_count) as total_customers,
    ROUND(SUM(total_mrr) / NULLIF(SUM(customer_count), 0), 2) as avg_mrr_per_customer,
    
    -- Efficiency metrics
    ROUND(AVG(fast_activation_rate), 1) as fast_activation_pct,
    ROUND(AVG(avg_health_score), 1) as avg_health_score,
    SUM(high_referral_count) as referral_candidates,
    
    -- CAC reduction strategies
    CASE acquisition_efficiency
        WHEN 'Highly Efficient' THEN 'Analyze and replicate acquisition channel'
        WHEN 'Efficient' THEN 'Increase investment in this segment'
        WHEN 'Standard' THEN 'Optimize onboarding process'
        WHEN 'Inefficient' THEN 'Redesign acquisition funnel'
    END as primary_strategy,
    
    -- Specific tactics
    CASE acquisition_efficiency
        WHEN 'Highly Efficient' THEN 
            'Create case studies, implement referral program, clone ideal customer profile'
        WHEN 'Efficient' THEN 
            'Develop channel partnerships, automate onboarding, increase marketing spend'
        WHEN 'Standard' THEN 
            'A/B test onboarding, provide implementation services, improve documentation'
        WHEN 'Inefficient' THEN 
            'Revisit pricing, qualify leads better, reduce sales cycle'
    END as tactical_recommendations,
    
    -- Expected impact
    CASE acquisition_efficiency
        WHEN 'Inefficient' THEN 'Could reduce CAC by 40% with improved activation'
        WHEN 'Standard' THEN 'Could reduce CAC by 25% with faster time-to-value'
        WHEN 'Efficient' THEN 'Could reduce CAC by 15% through referrals'
        ELSE 'Model for other segments - maintain approach'
    END as expected_impact
    
FROM acquisition_insights
GROUP BY acquisition_efficiency
ORDER BY 
    CASE acquisition_efficiency
        WHEN 'Highly Efficient' THEN 1
        WHEN 'Efficient' THEN 2
        WHEN 'Standard' THEN 3
        ELSE 4
    END;

-- Top performing customer profiles for ICP development
SELECT 
    'Ideal Customer Profile Analysis' as analysis_type,
    industry,
    customer_tier,
    COUNT(*) as customer_count,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
    ROUND(AVG(customer_lifetime_days), 0) as avg_lifetime_days,
    ROUND(AVG(customer_health_score), 1) as avg_health_score,
    ROUND(AVG(device_events_30d / NULLIF(days_since_creation, 0) * 30), 0) as avg_daily_events_since_start,
    
    -- ICP score
    (CASE WHEN AVG(monthly_recurring_revenue) > 2000 THEN 25 ELSE 0 END +
     CASE WHEN AVG(customer_lifetime_days) > 365 THEN 25 ELSE 0 END +
     CASE WHEN AVG(customer_health_score) > 80 THEN 25 ELSE 0 END +
     CASE WHEN AVG(device_events_30d) > 10000 THEN 25 ELSE 0 END) as icp_score
     
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND days_since_creation > 90
GROUP BY industry, customer_tier
HAVING COUNT(*) >= 5  -- Meaningful sample size
ORDER BY icp_score DESC, avg_mrr DESC
LIMIT 10;

-- ============================================
-- KEY INSIGHTS FROM STRATEGIC SCENARIOS
-- ============================================
/*
These strategic queries demonstrate:

1. PATH TO GROWTH - Multiple routes to revenue targets with specific numbers
2. UNIT ECONOMICS - Identify and fix margin leaks by segment  
3. INTEGRATION VALUE - Quantify platform stickiness and expansion
4. ACQUISITION EFFICIENCY - Reduce CAC through better targeting

All insights are:
- QUANTIFIED with specific dollar impacts
- ACTIONABLE with clear next steps
- PRIORITIZED by business value
- MEASURABLE with defined success metrics

The Entity-Centric Model enables C-suite strategic planning with simple queries!
*/