-- Customer Success Dashboard SQL Queries

-- 1. Customer Health Overview
SELECT 
    active_customers,
    total_customers,
    avg_health_score,
    churn_rate * 100 as churn_rate_pct,
    nps_score,
    total_mrr,
    avg_customer_lifetime_months,
    total_users
FROM public.metrics_customer_success;

-- 2. Customer Health Distribution
SELECT 
    health_category,
    COUNT(DISTINCT customer_id) as customer_count,
    SUM(customer_mrr) as total_mrr,
    AVG(health_score) as avg_health_score,
    AVG(churn_risk_score) as avg_churn_risk
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY health_category
ORDER BY 
    CASE health_category
        WHEN 'Healthy' THEN 1
        WHEN 'Stable' THEN 2
        WHEN 'At Risk' THEN 3
        WHEN 'Critical' THEN 4
    END;

-- 3. MRR & Retention Trends
SELECT 
    date,
    SUM(total_mrr) as total_mrr,
    AVG(retention_rate) as avg_retention_rate,
    SUM(new_mrr) as new_mrr,
    SUM(expansion_revenue) as expansion_mrr,
    SUM(contraction_revenue) as contraction_mrr,
    SUM(churned_revenue) as churned_mrr,
    COUNT(DISTINCT CASE WHEN churned_revenue > 0 THEN customer_id END) as churned_customers
FROM entity.entity_customers_daily
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY date
ORDER BY date;

-- 4. At-Risk Accounts (Top 20)
SELECT 
    customer_id,
    customer_name,
    health_score,
    churn_risk_score,
    customer_mrr,
    customer_tier,
    days_since_last_login,
    product_adoption_score,
    support_tickets_30d,
    last_nps_score,
    account_age_months,
    assigned_csm
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND (health_score < 40 OR churn_risk_score > 70)
ORDER BY churn_risk_score DESC, customer_mrr DESC
LIMIT 20;

-- 5. Product Usage Analysis
SELECT 
    DATE_TRUNC('week', date) as week,
    SUM(active_users) as total_active_users,
    SUM(total_logins) as total_logins,
    AVG(avg_session_duration_minutes) as avg_session_duration,
    SUM(features_used) as features_used,
    COUNT(DISTINCT customer_id) as active_customers
FROM entity.entity_customers_daily
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('week', date)
ORDER BY week DESC;

-- 6. Customer Segmentation
SELECT 
    customer_tier,
    industry,
    health_category,
    COUNT(DISTINCT customer_id) as customer_count,
    SUM(customer_mrr) as total_mrr,
    AVG(health_score) as avg_health_score,
    AVG(customer_lifetime_value) as avg_ltv,
    AVG(product_adoption_score) as avg_adoption
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY customer_tier, industry, health_category
ORDER BY total_mrr DESC;

-- 7. Support Metrics by Tier
SELECT 
    customer_tier,
    COUNT(DISTINCT customer_id) as customer_count,
    AVG(support_tickets_30d) as avg_tickets_per_customer,
    AVG(avg_ticket_resolution_hours) as avg_resolution_hours,
    SUM(support_tickets_30d) as total_tickets,
    AVG(support_satisfaction_score) as avg_satisfaction
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY customer_tier
ORDER BY 
    CASE customer_tier
        WHEN 'Enterprise' THEN 1
        WHEN 'Mid-Market' THEN 2
        WHEN 'SMB' THEN 3
        ELSE 4
    END;

-- 8. User Engagement Metrics
SELECT 
    u.user_role,
    COUNT(DISTINCT u.user_id) as user_count,
    AVG(u.engagement_score) as avg_engagement_score,
    AVG(u.days_since_last_login) as avg_days_since_login,
    SUM(u.total_sessions_30d) as total_sessions,
    AVG(u.features_used_30d) as avg_features_used
FROM entity.entity_users u
JOIN entity.entity_customers c ON u.account_id = c.customer_id
WHERE c.customer_status = 'active'
  AND u.user_status = 'active'
GROUP BY u.user_role
ORDER BY user_count DESC;

-- 9. Churn Risk Factors
SELECT 
    CASE 
        WHEN days_since_last_login < 7 THEN 'Active (< 7 days)'
        WHEN days_since_last_login < 14 THEN 'Moderate (7-14 days)'
        WHEN days_since_last_login < 30 THEN 'Low Activity (14-30 days)'
        ELSE 'Inactive (30+ days)'
    END as login_activity,
    COUNT(DISTINCT customer_id) as customer_count,
    AVG(health_score) as avg_health_score,
    AVG(churn_risk_score) as avg_churn_risk,
    SUM(customer_mrr) as total_mrr
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY login_activity
ORDER BY avg_churn_risk DESC;

-- 10. Customer Lifecycle Stage
SELECT 
    lifecycle_stage,
    COUNT(DISTINCT customer_id) as customer_count,
    SUM(customer_mrr) as total_mrr,
    AVG(health_score) as avg_health_score,
    AVG(account_age_months) as avg_account_age,
    AVG(expansion_revenue_total) as avg_expansion_revenue
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY lifecycle_stage
ORDER BY 
    CASE lifecycle_stage
        WHEN 'New' THEN 1
        WHEN 'Growing' THEN 2
        WHEN 'Mature' THEN 3
        WHEN 'Declining' THEN 4
    END;

-- 11. NPS Trends
SELECT 
    DATE_TRUNC('month', last_nps_date) as month,
    AVG(last_nps_score) as avg_nps,
    COUNT(DISTINCT CASE WHEN last_nps_score >= 9 THEN customer_id END) as promoters,
    COUNT(DISTINCT CASE WHEN last_nps_score BETWEEN 7 AND 8 THEN customer_id END) as passives,
    COUNT(DISTINCT CASE WHEN last_nps_score <= 6 THEN customer_id END) as detractors,
    COUNT(DISTINCT customer_id) as total_responses
FROM entity.entity_customers
WHERE last_nps_date IS NOT NULL
  AND last_nps_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', last_nps_date)
ORDER BY month DESC;

-- 12. Feature Adoption Analysis
SELECT 
    f.feature_name,
    f.feature_category,
    f.user_adoption_rate * 100 as adoption_rate_pct,
    f.account_adoption_rate * 100 as account_adoption_rate_pct,
    f.avg_usage_frequency,
    f.impact_on_retention
FROM entity.entity_features f
WHERE f.is_active = true
ORDER BY f.user_adoption_rate DESC
LIMIT 20;