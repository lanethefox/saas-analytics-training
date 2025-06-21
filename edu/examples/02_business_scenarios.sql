-- Business Scenario Queries: Real-World Analytics
-- These queries answer complex business questions that would typically require data scientists

-- ============================================
-- SCENARIO 1: "Why are Enterprise customers churning?"
-- ============================================
-- Deep dive into enterprise customer churn patterns and root causes

WITH enterprise_churn_analysis AS (
    SELECT 
        company_name,
        customer_tier,
        monthly_recurring_revenue,
        customer_lifetime_days,
        
        -- Core health metrics
        customer_health_score,
        churn_risk_score,
        
        -- Usage patterns
        total_users,
        active_users_30d,
        ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as user_adoption_rate,
        
        -- Device health
        total_devices,
        healthy_devices,
        device_events_30d,
        avg_device_uptime_30d,
        ROUND(healthy_devices::numeric / NULLIF(total_devices, 0) * 100, 1) as device_health_rate,
        
        -- Engagement decay
        EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_user_activity)) as days_inactive,
        EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_device_activity)) as days_without_device_activity,
        
        -- Identify churn patterns
        CASE 
            WHEN device_events_30d = 0 THEN 'Complete Disengagement'
            WHEN active_users_30d::numeric / NULLIF(total_users, 0) < 0.2 THEN 'User Adoption Failure'
            WHEN healthy_devices::numeric / NULLIF(total_devices, 0) < 0.5 THEN 'Infrastructure Problems'
            WHEN avg_device_uptime_30d < 80 THEN 'Reliability Issues'
            WHEN EXTRACT(DAYS FROM (CURRENT_TIMESTAMP - last_user_activity)) > 30 THEN 'Abandoned Platform'
            WHEN churn_risk_score > 70 THEN 'Multiple Risk Factors'
            ELSE 'Other'
        END as churn_category,
        
        -- Business impact
        CASE 
            WHEN customer_lifetime_days < 180 THEN 'Early Churn (<6 months)'
            WHEN customer_lifetime_days < 365 THEN 'First Year Churn'
            WHEN customer_lifetime_days < 730 THEN 'Second Year Churn'
            ELSE 'Long-term Customer Loss'
        END as churn_timing
        
    FROM entity.entity_customers
    WHERE customer_tier = 3  -- Enterprise only
      AND (churn_risk_score > 60 OR customer_status != 'active')
)
SELECT 
    churn_category,
    churn_timing,
    COUNT(*) as customer_count,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr_at_risk,
    SUM(monthly_recurring_revenue) as total_mrr_at_risk,
    ROUND(AVG(customer_lifetime_days), 0) as avg_customer_age_days,
    ROUND(AVG(churn_risk_score), 1) as avg_churn_risk,
    ROUND(AVG(user_adoption_rate), 1) as avg_user_adoption,
    ROUND(AVG(device_health_rate), 1) as avg_device_health,
    
    -- Prescriptive insights
    CASE churn_category
        WHEN 'Complete Disengagement' THEN 'Immediate intervention: Schedule executive business review'
        WHEN 'User Adoption Failure' THEN 'Deploy customer success team for training program'
        WHEN 'Infrastructure Problems' THEN 'Send technical team for device audit and repair'
        WHEN 'Reliability Issues' THEN 'Escalate to engineering for root cause analysis'
        WHEN 'Abandoned Platform' THEN 'Executive outreach to understand business changes'
        ELSE 'Conduct comprehensive account review'
    END as recommended_action
    
FROM enterprise_churn_analysis
GROUP BY churn_category, churn_timing
ORDER BY total_mrr_at_risk DESC;

-- ============================================
-- SCENARIO 2: "Which locations need operational intervention?"
-- ============================================
-- Identify locations with operational issues requiring immediate attention

WITH location_health_analysis AS (
    SELECT 
        l.location_id,
        l.location_name,
        l.city,
        l.state_code,
        c.company_name,
        c.customer_tier,
        
        -- Operational metrics
        l.operational_health_score,
        l.total_devices,
        l.active_devices,
        l.online_devices,
        ROUND(l.online_devices::numeric / NULLIF(l.total_devices, 0) * 100, 1) as device_connectivity_rate,
        
        -- Activity metrics
        l.tap_events_30d,
        l.active_devices_30d,
        ROUND(l.active_devices_30d::numeric / NULLIF(l.total_devices, 0) * 100, 1) as device_utilization_rate,
        
        -- Quality metrics
        l.quality_issues_30d,
        l.quality_issue_rate_30d,
        
        -- Support burden
        l.support_tickets_open,
        
        -- Revenue impact
        l.revenue_per_location,
        c.monthly_recurring_revenue as customer_mrr,
        
        -- Calculate intervention priority
        CASE 
            WHEN l.operational_health_score < 40 THEN 5  -- Critical
            WHEN l.online_devices::numeric / NULLIF(l.total_devices, 0) < 0.5 THEN 4  -- Major connectivity issues
            WHEN l.quality_issue_rate_30d > 10 THEN 4  -- Quality problems
            WHEN l.support_tickets_open > 5 THEN 3  -- High support burden
            WHEN l.active_devices_30d::numeric / NULLIF(l.total_devices, 0) < 0.3 THEN 3  -- Low utilization
            WHEN l.operational_health_score < 60 THEN 2  -- Needs improvement
            ELSE 1  -- Monitor
        END as intervention_priority,
        
        -- Root cause analysis
        CASE 
            WHEN l.online_devices::numeric / NULLIF(l.total_devices, 0) < 0.5 THEN 'Network/Connectivity Issues'
            WHEN l.quality_issue_rate_30d > 10 THEN 'Device Quality/Maintenance Issues'
            WHEN l.active_devices_30d = 0 THEN 'Complete Location Shutdown'
            WHEN l.support_tickets_open > 5 THEN 'High Support Needs'
            WHEN l.active_devices_30d::numeric / NULLIF(l.total_devices, 0) < 0.3 THEN 'Low Device Utilization'
            WHEN l.tap_events_30d = 0 THEN 'No Activity - Possible Closure'
            ELSE 'General Performance Issues'
        END as primary_issue
        
    FROM entity.entity_locations l
    JOIN entity.entity_customers c ON l.account_id = c.account_id
    WHERE l.location_status = 'active'
)
SELECT 
    location_id,
    location_name,
    city,
    state_code,
    company_name,
    customer_tier,
    operational_health_score,
    device_connectivity_rate,
    device_utilization_rate,
    quality_issue_rate_30d,
    support_tickets_open,
    revenue_per_location,
    primary_issue,
    
    -- Intervention recommendations
    CASE intervention_priority
        WHEN 5 THEN '🚨 CRITICAL: Dispatch technician within 24 hours'
        WHEN 4 THEN '⚠️ URGENT: Schedule on-site visit within 48 hours'  
        WHEN 3 THEN '🔧 HIGH: Remote diagnosis and support needed'
        WHEN 2 THEN '📋 MEDIUM: Add to next maintenance cycle'
        ELSE '✅ LOW: Continue monitoring'
    END as intervention_required,
    
    -- Estimated business impact
    CASE 
        WHEN tap_events_30d = 0 THEN revenue_per_location  -- Complete revenue at risk
        WHEN device_utilization_rate < 30 THEN revenue_per_location * 0.7  -- High risk
        WHEN quality_issue_rate_30d > 10 THEN revenue_per_location * 0.5  -- Medium risk
        ELSE revenue_per_location * 0.2  -- Low risk
    END as revenue_at_risk,
    
    -- Specific action items
    CASE primary_issue
        WHEN 'Network/Connectivity Issues' THEN 
            'Check internet connection, router configuration, and firewall settings'
        WHEN 'Device Quality/Maintenance Issues' THEN 
            'Perform device diagnostics, check calibration, replace faulty units'
        WHEN 'Complete Location Shutdown' THEN 
            'Contact location manager immediately to understand closure/issues'
        WHEN 'High Support Needs' THEN 
            'Review tickets for patterns, schedule training session'
        WHEN 'Low Device Utilization' THEN 
            'Analyze usage patterns, optimize device placement, user training'
        WHEN 'No Activity - Possible Closure' THEN 
            'Verify location operational status with customer'
        ELSE 
            'Conduct comprehensive location audit'
    END as specific_actions
    
FROM location_health_analysis
WHERE intervention_priority >= 3  -- Only show locations needing intervention
ORDER BY 
    intervention_priority DESC,
    revenue_at_risk DESC,
    operational_health_score ASC
LIMIT 50;

-- ============================================  
-- SCENARIO 3: "What features drive expansion revenue?"
-- ============================================
-- Analyze which product features correlate with customer expansion and higher revenue

WITH customer_feature_analysis AS (
    SELECT 
        c.company_name,
        c.customer_tier,
        c.monthly_recurring_revenue,
        c.days_since_creation,
        c.customer_health_score,
        
        -- Calculate MRR growth (would need historical data in real scenario)
        -- For demo, we'll use tier and usage as proxy
        CASE 
            WHEN c.customer_tier = 3 AND c.days_since_creation > 365 THEN c.monthly_recurring_revenue * 0.3
            WHEN c.customer_tier = 2 AND c.days_since_creation > 180 THEN c.monthly_recurring_revenue * 0.2
            ELSE 0
        END as estimated_expansion_revenue,
        
        -- Feature adoption indicators (using available metrics as proxy)
        CASE WHEN c.total_users > 50 THEN 1 ELSE 0 END as advanced_user_management,
        CASE WHEN c.total_locations > 5 THEN 1 ELSE 0 END as multi_location_feature,
        CASE WHEN c.device_events_30d > 10000 THEN 1 ELSE 0 END as high_volume_analytics,
        CASE WHEN c.total_devices > 20 THEN 1 ELSE 0 END as enterprise_device_management,
        CASE WHEN c.avg_user_engagement_score > 80 THEN 1 ELSE 0 END as advanced_engagement_features,
        
        -- Customer segments
        CASE 
            WHEN c.monthly_recurring_revenue > 5000 THEN 'Enterprise'
            WHEN c.monthly_recurring_revenue > 1000 THEN 'Mid-Market'
            ELSE 'SMB'
        END as revenue_segment
    FROM entity.entity_customers c
    WHERE c.customer_status = 'active'
      AND c.days_since_creation > 90  -- Established customers only
)
SELECT 
    'Advanced User Management (>50 users)' as feature_name,
    COUNT(CASE WHEN advanced_user_management = 1 THEN 1 END) as customers_using_feature,
    COUNT(*) as total_customers,
    ROUND(COUNT(CASE WHEN advanced_user_management = 1 THEN 1 END)::numeric / COUNT(*) * 100, 1) as adoption_rate,
    ROUND(AVG(CASE WHEN advanced_user_management = 1 THEN monthly_recurring_revenue END), 2) as avg_mrr_with_feature,
    ROUND(AVG(CASE WHEN advanced_user_management = 0 THEN monthly_recurring_revenue END), 2) as avg_mrr_without_feature,
    ROUND(AVG(CASE WHEN advanced_user_management = 1 THEN customer_health_score END), 1) as avg_health_with_feature,
    ROUND(AVG(CASE WHEN advanced_user_management = 0 THEN customer_health_score END), 1) as avg_health_without_feature,
    ROUND(
        AVG(CASE WHEN advanced_user_management = 1 THEN monthly_recurring_revenue END) - 
        AVG(CASE WHEN advanced_user_management = 0 THEN monthly_recurring_revenue END), 2
    ) as mrr_lift,
    'User-based pricing tier, SSO integration, role management' as expansion_strategy
FROM customer_feature_analysis

UNION ALL

SELECT 
    'Multi-Location Management (>5 locations)' as feature_name,
    COUNT(CASE WHEN multi_location_feature = 1 THEN 1 END) as customers_using_feature,
    COUNT(*) as total_customers,
    ROUND(COUNT(CASE WHEN multi_location_feature = 1 THEN 1 END)::numeric / COUNT(*) * 100, 1) as adoption_rate,
    ROUND(AVG(CASE WHEN multi_location_feature = 1 THEN monthly_recurring_revenue END), 2) as avg_mrr_with_feature,
    ROUND(AVG(CASE WHEN multi_location_feature = 0 THEN monthly_recurring_revenue END), 2) as avg_mrr_without_feature,
    ROUND(AVG(CASE WHEN multi_location_feature = 1 THEN customer_health_score END), 1) as avg_health_with_feature,
    ROUND(AVG(CASE WHEN multi_location_feature = 0 THEN customer_health_score END), 1) as avg_health_without_feature,
    ROUND(
        AVG(CASE WHEN multi_location_feature = 1 THEN monthly_recurring_revenue END) - 
        AVG(CASE WHEN multi_location_feature = 0 THEN monthly_recurring_revenue END), 2
    ) as mrr_lift,
    'Location-based pricing, regional analytics, centralized management' as expansion_strategy
FROM customer_feature_analysis

UNION ALL

SELECT 
    'High Volume Analytics (>10K events/month)' as feature_name,
    COUNT(CASE WHEN high_volume_analytics = 1 THEN 1 END) as customers_using_feature,
    COUNT(*) as total_customers,
    ROUND(COUNT(CASE WHEN high_volume_analytics = 1 THEN 1 END)::numeric / COUNT(*) * 100, 1) as adoption_rate,
    ROUND(AVG(CASE WHEN high_volume_analytics = 1 THEN monthly_recurring_revenue END), 2) as avg_mrr_with_feature,
    ROUND(AVG(CASE WHEN high_volume_analytics = 0 THEN monthly_recurring_revenue END), 2) as avg_mrr_without_feature,
    ROUND(AVG(CASE WHEN high_volume_analytics = 1 THEN customer_health_score END), 1) as avg_health_with_feature,
    ROUND(AVG(CASE WHEN high_volume_analytics = 0 THEN customer_health_score END), 1) as avg_health_without_feature,
    ROUND(
        AVG(CASE WHEN high_volume_analytics = 1 THEN monthly_recurring_revenue END) - 
        AVG(CASE WHEN high_volume_analytics = 0 THEN monthly_recurring_revenue END), 2
    ) as mrr_lift,
    'Usage-based pricing tiers, advanced analytics package, API access' as expansion_strategy
FROM customer_feature_analysis

UNION ALL

SELECT 
    'Enterprise Device Management (>20 devices)' as feature_name,
    COUNT(CASE WHEN enterprise_device_management = 1 THEN 1 END) as customers_using_feature,
    COUNT(*) as total_customers,
    ROUND(COUNT(CASE WHEN enterprise_device_management = 1 THEN 1 END)::numeric / COUNT(*) * 100, 1) as adoption_rate,
    ROUND(AVG(CASE WHEN enterprise_device_management = 1 THEN monthly_recurring_revenue END), 2) as avg_mrr_with_feature,
    ROUND(AVG(CASE WHEN enterprise_device_management = 0 THEN monthly_recurring_revenue END), 2) as avg_mrr_without_feature,
    ROUND(AVG(CASE WHEN enterprise_device_management = 1 THEN customer_health_score END), 1) as avg_health_with_feature,
    ROUND(AVG(CASE WHEN enterprise_device_management = 0 THEN customer_health_score END), 1) as avg_health_without_feature,
    ROUND(
        AVG(CASE WHEN enterprise_device_management = 1 THEN monthly_recurring_revenue END) - 
        AVG(CASE WHEN enterprise_device_management = 0 THEN monthly_recurring_revenue END), 2
    ) as mrr_lift,
    'Device-based pricing, premium support, predictive maintenance' as expansion_strategy
FROM customer_feature_analysis

ORDER BY mrr_lift DESC;

-- Additional analysis: Feature combination impact
WITH feature_combinations AS (
    SELECT 
        c.company_name,
        c.monthly_recurring_revenue,
        c.customer_health_score,
        
        -- Count features adopted
        (CASE WHEN c.total_users > 50 THEN 1 ELSE 0 END +
         CASE WHEN c.total_locations > 5 THEN 1 ELSE 0 END +
         CASE WHEN c.device_events_30d > 10000 THEN 1 ELSE 0 END +
         CASE WHEN c.total_devices > 20 THEN 1 ELSE 0 END) as features_adopted_count
         
    FROM entity.entity_customers c
    WHERE c.customer_status = 'active'
)
SELECT 
    features_adopted_count,
    COUNT(*) as customer_count,
    ROUND(AVG(monthly_recurring_revenue), 2) as avg_mrr,
    ROUND(AVG(customer_health_score), 1) as avg_health_score,
    ROUND(SUM(monthly_recurring_revenue), 2) as total_mrr,
    
    -- Insights
    CASE features_adopted_count
        WHEN 0 THEN 'Basic tier - Focus on first feature adoption'
        WHEN 1 THEN 'Growing - Introduce complementary features'
        WHEN 2 THEN 'Expanding - Push for platform adoption'
        WHEN 3 THEN 'Advanced - Consider enterprise package'
        WHEN 4 THEN 'Power user - Maximize value extraction'
    END as expansion_recommendation
    
FROM feature_combinations
GROUP BY features_adopted_count
ORDER BY features_adopted_count DESC;

-- ============================================
-- KEY INSIGHTS FROM THESE QUERIES
-- ============================================
/*
These business scenario queries demonstrate:

1. ROOT CAUSE ANALYSIS - Identify specific reasons for business problems
2. PRESCRIPTIVE ACTIONS - Provide clear next steps, not just data
3. REVENUE IMPACT - Quantify the business impact of issues
4. PRIORITIZATION - Focus on what matters most
5. SEGMENTATION - Different strategies for different customer types

All accomplished with simple, readable SQL on single entity tables!
*/