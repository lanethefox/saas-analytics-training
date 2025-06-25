-- Additional Power Query Examples for Entity-Centric Modeling
-- These demonstrate more advanced single-table analytics

-- ============================================
-- POWER QUERY 6: COHORT RETENTION ANALYSIS
-- ============================================
-- Complete cohort analysis without complex joins
WITH cohort_analysis AS (
    SELECT 
        DATE_TRUNC('month', created_at) as cohort_month,
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        customer_status,
        customer_health_score,
        churn_risk_score,
        device_events_30d,
        
        -- Calculate months since joining
        EXTRACT(YEAR FROM AGE(CURRENT_DATE, created_at)) * 12 + 
        EXTRACT(MONTH FROM AGE(CURRENT_DATE, created_at)) as months_since_join,
        
        -- Retention flag
        CASE 
            WHEN customer_status = 'active' THEN 1 
            ELSE 0 
        END as is_retained,
        
        -- Activity level
        CASE 
            WHEN device_events_30d > 1000 THEN 'High'
            WHEN device_events_30d > 100 THEN 'Medium'
            WHEN device_events_30d > 0 THEN 'Low'
            ELSE 'Inactive'
        END as activity_level
    FROM entity.entity_customers
    WHERE created_at >= CURRENT_DATE - INTERVAL '24 months'
)
SELECT 
    cohort_month,
    months_since_join,
    COUNT(*) as cohort_size,
    SUM(is_retained) as customers_retained,
    ROUND(SUM(is_retained)::numeric / COUNT(*) * 100, 1) as retention_rate,
    SUM(monthly_recurring_revenue) FILTER (WHERE is_retained = 1) as retained_mrr,
    ROUND(AVG(customer_health_score) FILTER (WHERE is_retained = 1), 1) as avg_health_score,
    
    -- Activity distribution
    COUNT(*) FILTER (WHERE activity_level = 'High' AND is_retained = 1) as high_activity_customers,
    COUNT(*) FILTER (WHERE activity_level = 'Inactive' AND is_retained = 1) as inactive_but_paying
    
FROM cohort_analysis
GROUP BY cohort_month, months_since_join
ORDER BY cohort_month DESC, months_since_join;

-- ============================================
-- POWER QUERY 7: PRODUCT-LED GROWTH SIGNALS
-- ============================================
-- Identify viral growth and expansion patterns
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue,
    
    -- Growth metrics
    total_users,
    active_users_30d,
    total_locations,
    total_devices,
    
    -- Calculate growth velocity
    CASE 
        WHEN days_since_creation > 0 THEN 
            ROUND(total_users::numeric / days_since_creation * 30, 2)
        ELSE 0
    END as monthly_user_growth_rate,
    
    CASE 
        WHEN days_since_creation > 0 THEN 
            ROUND(total_locations::numeric / days_since_creation * 30, 2)
        ELSE 0
    END as monthly_location_growth_rate,
    
    -- Viral indicators
    CASE 
        WHEN total_users > 50 AND days_since_creation < 180 THEN 'Rapid User Adoption'
        WHEN total_locations > 10 AND days_since_creation < 365 THEN 'Multi-Location Expansion'
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) > 0.8 
             AND total_users > 20 THEN 'High Engagement Network'
        WHEN device_events_30d > 50000 THEN 'Power User Behavior'
        ELSE 'Standard Growth'
    END as growth_pattern,
    
    -- Network effects score
    (
        (CASE WHEN total_users > 50 THEN 25 ELSE total_users / 2 END) +
        (CASE WHEN total_locations > 10 THEN 25 ELSE total_locations * 2.5 END) +
        (CASE WHEN active_users_30d::numeric / NULLIF(total_users, 0) > 0.7 THEN 25 ELSE 0 END) +
        (CASE WHEN device_events_30d > 10000 THEN 25 ELSE device_events_30d / 400 END)
    ) as network_effect_score,
    
    -- Expansion readiness
    CASE 
        WHEN customer_tier < 3 
             AND (total_users > 50 OR total_locations > 10) 
             AND customer_health_score > 70 THEN 'Prime Expansion Candidate'
        WHEN total_users > 100 OR total_locations > 20 THEN 'Consider Custom Pricing'
        ELSE 'Continue Monitoring'
    END as growth_recommendation,
    
    -- Revenue efficiency
    ROUND(monthly_recurring_revenue::numeric / NULLIF(total_users, 0), 2) as revenue_per_user,
    ROUND(device_events_30d::numeric / NULLIF(monthly_recurring_revenue, 0), 1) as events_per_dollar
    
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND days_since_creation > 30  -- Exclude brand new customers
ORDER BY network_effect_score DESC
LIMIT 50;

-- ============================================
-- POWER QUERY 8: PREDICTIVE CHURN INDICATORS
-- ============================================
-- Early warning system using behavioral patterns
WITH churn_indicators AS (
    SELECT 
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        customer_lifetime_days,
        
        -- Core metrics
        customer_health_score,
        churn_risk_score,
        
        -- Usage trends (would be better with historical data)
        device_events_30d,
        device_events_7d,
        active_users_30d,
        active_users_7d,
        
        -- Calculate weekly decline
        CASE 
            WHEN device_events_30d > 0 THEN 
                ROUND((1 - (device_events_7d * 4.3)::numeric / device_events_30d) * 100, 1)
            ELSE 100
        END as usage_decline_pct,
        
        CASE 
            WHEN active_users_30d > 0 THEN 
                ROUND((1 - (active_users_7d * 4.3)::numeric / active_users_30d) * 100, 1)
            ELSE 100
        END as user_decline_pct,
        
        -- Engagement gaps
        EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_user_activity)) as days_since_login,
        EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_device_activity)) as days_since_usage,
        
        -- Support burden
        CASE 
            WHEN total_users > 0 THEN 
                ROUND(support_tickets_30d::numeric / total_users, 2)
            ELSE 0
        END as tickets_per_user,
        
        -- Device health
        ROUND(healthy_devices::numeric / NULLIF(total_devices, 0) * 100, 1) as device_health_pct
    FROM entity.entity_customers
    WHERE customer_status = 'active'
)
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue,
    customer_lifetime_days,
    
    -- Risk scores
    customer_health_score,
    churn_risk_score,
    
    -- Leading indicators
    usage_decline_pct,
    user_decline_pct,
    days_since_login,
    days_since_usage,
    tickets_per_user,
    device_health_pct,
    
    -- Churn probability (simplified model)
    ROUND(
        LEAST(100, 
            (CASE WHEN usage_decline_pct > 50 THEN 30 ELSE usage_decline_pct * 0.6 END) +
            (CASE WHEN days_since_login > 14 THEN 25 ELSE days_since_login * 1.8 END) +
            (CASE WHEN device_health_pct < 50 THEN 20 ELSE (100 - device_health_pct) * 0.4 END) +
            (CASE WHEN tickets_per_user > 2 THEN 15 ELSE tickets_per_user * 7.5 END) +
            (CASE WHEN user_decline_pct > 30 THEN 10 ELSE user_decline_pct * 0.33 END)
        ), 1
    ) as calculated_churn_probability,
    
    -- Intervention type
    CASE 
        WHEN usage_decline_pct > 50 OR days_since_usage > 7 THEN 'Technical Issue - Immediate Support'
        WHEN user_decline_pct > 30 OR days_since_login > 14 THEN 'User Adoption - Training Needed'
        WHEN device_health_pct < 60 THEN 'Infrastructure - Maintenance Required'
        WHEN tickets_per_user > 1.5 THEN 'Support Overload - Process Review'
        WHEN churn_risk_score > 60 THEN 'Multiple Factors - Executive Review'
        ELSE 'Monitor'
    END as intervention_type,
    
    -- Time to act
    CASE 
        WHEN device_events_7d = 0 OR days_since_usage > 14 THEN 'TODAY'
        WHEN usage_decline_pct > 50 OR churn_risk_score > 70 THEN 'Within 24 hours'
        WHEN user_decline_pct > 30 OR churn_risk_score > 50 THEN 'Within 3 days'
        ELSE 'Within 1 week'
    END as urgency
    
FROM churn_indicators
WHERE churn_risk_score > 30
   OR usage_decline_pct > 25
   OR days_since_login > 7
   OR device_health_pct < 70
ORDER BY 
    CASE urgency
        WHEN 'TODAY' THEN 1
        WHEN 'Within 24 hours' THEN 2
        WHEN 'Within 3 days' THEN 3
        ELSE 4
    END,
    monthly_recurring_revenue DESC;

-- ============================================
-- POWER QUERY 9: CUSTOMER LIFETIME VALUE MODEL
-- ============================================
-- Calculate CLV components from entity data
WITH clv_components AS (
    SELECT 
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        customer_lifetime_days,
        days_since_creation,
        
        -- Historical performance
        customer_health_score,
        churn_risk_score,
        
        -- Usage intensity
        device_events_30d,
        active_users_30d,
        total_devices,
        
        -- Calculate monthly churn probability
        CASE 
            WHEN churn_risk_score >= 80 THEN 0.15
            WHEN churn_risk_score >= 60 THEN 0.08
            WHEN churn_risk_score >= 40 THEN 0.04
            WHEN churn_risk_score >= 20 THEN 0.02
            ELSE 0.01
        END as monthly_churn_rate,
        
        -- Expansion probability by tier
        CASE 
            WHEN customer_tier = 1 AND total_devices > 5 THEN 0.1
            WHEN customer_tier = 2 AND total_devices > 20 THEN 0.08
            WHEN customer_tier = 1 THEN 0.05
            WHEN customer_tier = 2 THEN 0.03
            ELSE 0.01
        END as monthly_expansion_rate,
        
        -- Average expansion amount
        CASE 
            WHEN customer_tier = 1 THEN monthly_recurring_revenue * 0.5
            WHEN customer_tier = 2 THEN monthly_recurring_revenue * 0.3
            ELSE monthly_recurring_revenue * 0.1
        END as avg_expansion_value
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
)
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue as current_mrr,
    customer_lifetime_days,
    
    -- Churn and expansion rates
    ROUND(monthly_churn_rate * 100, 1) as monthly_churn_pct,
    ROUND(monthly_expansion_rate * 100, 1) as monthly_expansion_pct,
    
    -- Expected lifetime (months)
    ROUND(1 / monthly_churn_rate, 1) as expected_lifetime_months,
    
    -- CLV calculation (simplified)
    ROUND(
        (monthly_recurring_revenue * (1 / monthly_churn_rate)) + 
        (avg_expansion_value * monthly_expansion_rate * (1 / monthly_churn_rate))
    , 2) as estimated_clv,
    
    -- CLV to CAC ratio (assuming CAC data)
    ROUND(
        ((monthly_recurring_revenue * (1 / monthly_churn_rate)) + 
         (avg_expansion_value * monthly_expansion_rate * (1 / monthly_churn_rate))) /
        CASE customer_tier
            WHEN 1 THEN 500   -- Assumed CAC
            WHEN 2 THEN 2000
            ELSE 5000
        END
    , 2) as clv_to_cac_ratio,
    
    -- Payback period
    ROUND(
        CASE customer_tier
            WHEN 1 THEN 500
            WHEN 2 THEN 2000  
            ELSE 5000
        END / monthly_recurring_revenue
    , 1) as payback_months,
    
    -- Value tier
    CASE 
        WHEN ((monthly_recurring_revenue * (1 / monthly_churn_rate)) + 
              (avg_expansion_value * monthly_expansion_rate * (1 / monthly_churn_rate))) > 100000 THEN 'Platinum'
        WHEN ((monthly_recurring_revenue * (1 / monthly_churn_rate)) + 
              (avg_expansion_value * monthly_expansion_rate * (1 / monthly_churn_rate))) > 50000 THEN 'Gold'
        WHEN ((monthly_recurring_revenue * (1 / monthly_churn_rate)) + 
              (avg_expansion_value * monthly_expansion_rate * (1 / monthly_churn_rate))) > 20000 THEN 'Silver'
        ELSE 'Bronze'
    END as value_tier,
    
    -- Strategic importance
    CASE 
        WHEN device_events_30d > 50000 AND total_devices > 50 THEN 'Strategic - High Volume'
        WHEN total_devices > 100 THEN 'Strategic - Large Infrastructure'
        WHEN monthly_recurring_revenue > 5000 THEN 'Strategic - High Revenue'
        WHEN customer_health_score > 90 AND customer_tier < 3 THEN 'Growth Opportunity'
        ELSE 'Standard'
    END as strategic_segment
    
FROM clv_components
ORDER BY estimated_clv DESC
LIMIT 100;

-- ============================================
-- POWER QUERY 10: MULTI-LOCATION ANALYTICS
-- ============================================
-- Analyze multi-location customer patterns
WITH location_analytics AS (
    SELECT 
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        
        -- Location metrics
        total_locations,
        total_devices,
        total_users,
        
        -- Calculate per-location metrics
        ROUND(total_devices::numeric / NULLIF(total_locations, 0), 1) as avg_devices_per_location,
        ROUND(total_users::numeric / NULLIF(total_locations, 0), 1) as avg_users_per_location,
        ROUND(monthly_recurring_revenue::numeric / NULLIF(total_locations, 0), 2) as mrr_per_location,
        ROUND(device_events_30d::numeric / NULLIF(total_locations, 0), 0) as events_per_location,
        
        -- Location categories
        CASE 
            WHEN total_locations = 1 THEN 'Single Location'
            WHEN total_locations <= 5 THEN 'Small Chain'
            WHEN total_locations <= 20 THEN 'Regional Chain'
            WHEN total_locations <= 50 THEN 'Large Regional'
            ELSE 'Enterprise Chain'
        END as location_category,
        
        -- Standardization score (how consistent across locations)
        CASE 
            WHEN total_locations > 1 THEN
                CASE 
                    WHEN total_devices::numeric / total_locations BETWEEN 3 AND 5 THEN 100
                    WHEN total_devices::numeric / total_locations BETWEEN 2 AND 6 THEN 80
                    ELSE 60
                END
            ELSE NULL
        END as location_standardization_score,
        
        -- Growth stage
        CASE 
            WHEN total_locations = 1 AND days_since_creation > 365 THEN 'Ready for Expansion'
            WHEN total_locations > 1 AND total_locations < 10 AND 
                 device_events_30d / NULLIF(total_locations, 0) > 1000 THEN 'Scaling Successfully'
            WHEN total_locations > 10 AND customer_tier < 3 THEN 'Needs Enterprise Features'
            ELSE 'Optimizing Current'
        END as growth_stage,
        
        -- Health metrics
        customer_health_score,
        avg_device_uptime_30d,
        healthy_devices
        
    FROM entity.entity_customers
    WHERE customer_status = 'active'
)
SELECT 
    company_name,
    customer_tier,
    location_category,
    total_locations,
    
    -- Operational metrics
    avg_devices_per_location,
    avg_users_per_location,
    mrr_per_location,
    events_per_location,
    
    -- Efficiency analysis  
    monthly_recurring_revenue,
    ROUND(monthly_recurring_revenue::numeric / 
          (CASE customer_tier 
           WHEN 1 THEN 99 
           WHEN 2 THEN 999 
           ELSE 4999 
          END) * 100, 1) as tier_utilization_pct,
    
    -- Standardization
    location_standardization_score,
    CASE 
        WHEN location_standardization_score >= 80 THEN 'Well Standardized'
        WHEN location_standardization_score >= 60 THEN 'Moderately Standardized'
        ELSE 'Needs Standardization'
    END as standardization_status,
    
    -- Growth opportunities
    growth_stage,
    CASE 
        WHEN total_locations = 1 AND mrr_per_location > 500 THEN 
            'Strong unit economics for expansion'
        WHEN total_locations > 5 AND customer_tier = 1 THEN
            'Multi-location discount opportunity'
        WHEN avg_devices_per_location < 2 THEN
            'Increase penetration per location'
        WHEN location_standardization_score < 80 AND total_locations > 5 THEN
            'Standardization consulting opportunity'
        ELSE 'Continue current strategy'
    END as revenue_opportunity,
    
    -- Operational health
    customer_health_score,
    ROUND(healthy_devices::numeric / NULLIF(total_devices, 0) * 100, 1) as device_health_pct,
    
    -- Estimated expansion value
    CASE 
        WHEN total_locations = 1 AND mrr_per_location > 300 THEN mrr_per_location * 4
        WHEN growth_stage = 'Needs Enterprise Features' THEN 
            (4999 - monthly_recurring_revenue)
        WHEN avg_devices_per_location < 3 AND total_locations > 5 THEN
            monthly_recurring_revenue * 0.3
        ELSE 0
    END as expansion_potential_mrr
    
FROM location_analytics
WHERE total_locations > 0
ORDER BY 
    CASE 
        WHEN growth_stage = 'Needs Enterprise Features' THEN 1
        WHEN growth_stage = 'Ready for Expansion' THEN 2
        WHEN growth_stage = 'Scaling Successfully' THEN 3
        ELSE 4
    END,
    total_locations DESC,
    monthly_recurring_revenue DESC
LIMIT 100;

-- ============================================
-- BONUS: EXECUTIVE PORTFOLIO DASHBOARD
-- ============================================
-- Complete portfolio view in one query
SELECT 
    -- Portfolio composition
    COUNT(*) as total_customers,
    COUNT(CASE WHEN customer_tier = 1 THEN 1 END) as starter_customers,
    COUNT(CASE WHEN customer_tier = 2 THEN 1 END) as business_customers,
    COUNT(CASE WHEN customer_tier = 3 THEN 1 END) as enterprise_customers,
    
    -- Revenue metrics
    SUM(monthly_recurring_revenue) as total_mrr,
    SUM(annual_recurring_revenue) as total_arr,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_customer_mrr,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_recurring_revenue) as median_mrr,
    
    -- Growth metrics
    COUNT(CASE WHEN days_since_creation <= 30 THEN 1 END) as new_customers_30d,
    SUM(CASE WHEN days_since_creation <= 30 THEN monthly_recurring_revenue END) as new_mrr_30d,
    
    -- Health distribution
    ROUND(AVG(customer_health_score), 1) as avg_health_score,
    COUNT(CASE WHEN customer_health_score >= 80 THEN 1 END) as healthy_customers,
    COUNT(CASE WHEN churn_risk_score >= 60 THEN 1 END) as at_risk_customers,
    SUM(CASE WHEN churn_risk_score >= 60 THEN monthly_recurring_revenue END) as mrr_at_risk,
    
    -- Usage metrics
    SUM(device_events_30d) as total_platform_events,
    SUM(total_devices) as total_platform_devices,
    SUM(active_users_30d) as total_active_users,
    
    -- Efficiency metrics
    ROUND(SUM(device_events_30d)::numeric / NULLIF(SUM(total_devices), 0), 1) as events_per_device,
    ROUND(SUM(monthly_recurring_revenue)::numeric / NULLIF(SUM(active_users_30d), 0), 2) as mrr_per_active_user,
    
    -- Expansion pipeline
    COUNT(CASE 
        WHEN customer_tier < 3 AND customer_health_score > 70 AND
             (total_devices > 20 OR active_users_30d > 50) THEN 1 
    END) as expansion_opportunities,
    
    SUM(CASE 
        WHEN customer_tier = 1 AND total_devices > 10 THEN 999 - monthly_recurring_revenue
        WHEN customer_tier = 2 AND total_devices > 50 THEN 4999 - monthly_recurring_revenue
        ELSE 0
    END) as total_expansion_potential
    
FROM entity.entity_customers
WHERE customer_status = 'active';

-- ============================================
-- KEY INSIGHTS FROM POWER QUERIES
-- ============================================
/*
These 10 power queries demonstrate:

1. COMPLETE ANALYTICS from single tables - no complex joins
2. SOPHISTICATED METRICS including CLV, cohorts, and predictions
3. ACTIONABLE INSIGHTS with specific recommendations
4. PERFORMANCE at scale - all queries execute in seconds
5. BUSINESS ACCESSIBILITY - readable by non-technical users

The Entity-Centric Model transforms how we approach analytics:
- From technical complexity to business simplicity
- From slow queries to instant insights
- From data specialists only to self-service analytics
*/