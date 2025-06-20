-- Create views for Superset dashboards
-- These views simplify access to metrics and provide pre-aggregated data

-- Sales Dashboard Views
CREATE OR REPLACE VIEW superset_sales_overview AS
SELECT 
    s.*,
    s.win_rate * 100 as win_rate_pct,
    CASE 
        WHEN s.pipeline_value > 0 AND s.total_revenue > 0 
        THEN ROUND(s.pipeline_value / (s.total_revenue / 3), 2)
        ELSE 0 
    END as pipeline_coverage_ratio
FROM public.metrics_sales s;

CREATE OR REPLACE VIEW superset_pipeline_analysis AS
SELECT 
    p.*,
    CASE 
        WHEN p.days_in_stage > 30 THEN 'Stalled'
        WHEN p.close_date < CURRENT_DATE AND p.stage_name NOT IN ('Closed Won', 'Closed Lost') THEN 'Overdue'
        WHEN p.probability >= 80 THEN 'Hot'
        WHEN p.probability >= 50 THEN 'Warm'
        ELSE 'Cold'
    END as deal_temperature,
    CASE 
        WHEN p.amount >= 50000 THEN 'Enterprise'
        WHEN p.amount >= 10000 THEN 'Mid-Market'
        ELSE 'SMB'
    END as deal_segment
FROM mart.mart_sales__pipeline p;

-- Customer Success Dashboard Views
CREATE OR REPLACE VIEW superset_customer_health AS
SELECT 
    c.*,
    c.churn_rate * 100 as churn_rate_pct,
    CASE 
        WHEN c.health_score >= 80 THEN 'Excellent'
        WHEN c.health_score >= 60 THEN 'Good'
        WHEN c.health_score >= 40 THEN 'Fair'
        ELSE 'Poor'
    END as health_grade
FROM public.metrics_customer_success c;

CREATE OR REPLACE VIEW superset_at_risk_customers AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.health_score,
    c.churn_risk_score,
    c.customer_mrr,
    c.customer_tier,
    c.days_since_last_login,
    c.support_tickets_30d,
    c.product_adoption_score,
    c.assigned_csm,
    CASE 
        WHEN c.churn_risk_score > 80 THEN 'Critical'
        WHEN c.churn_risk_score > 60 THEN 'High'
        WHEN c.churn_risk_score > 40 THEN 'Medium'
        ELSE 'Low'
    END as risk_level
FROM entity.entity_customers c
WHERE c.customer_status = 'active'
  AND (c.health_score < 50 OR c.churn_risk_score > 60)
ORDER BY c.churn_risk_score DESC, c.customer_mrr DESC;

-- Marketing Dashboard Views
CREATE OR REPLACE VIEW superset_campaign_performance AS
SELECT 
    c.*,
    c.click_through_rate * 100 as ctr_pct,
    c.conversion_rate * 100 as conversion_rate_pct,
    CASE 
        WHEN c.performance_score >= 80 THEN 'High Performer'
        WHEN c.performance_score >= 50 THEN 'Average'
        ELSE 'Underperforming'
    END as performance_category
FROM entity.entity_campaigns c
WHERE c.is_active = true;

CREATE OR REPLACE VIEW superset_marketing_roi AS
SELECT 
    m.*,
    ROUND((m.qualified_leads::numeric / NULLIF(m.total_leads, 0)) * 100, 1) as qualification_rate,
    ROUND(m.attributed_revenue / NULLIF(m.total_spend, 0), 2) as roi_ratio
FROM public.metrics_marketing m;

-- Product Analytics Dashboard Views
CREATE OR REPLACE VIEW superset_user_engagement AS
SELECT 
    p.*,
    ROUND(p.daily_active_users::numeric / NULLIF(p.monthly_active_users, 0) * 100, 1) as dau_mau_ratio,
    CASE 
        WHEN p.dau_mau_ratio >= 20 THEN 'High Stickiness'
        WHEN p.dau_mau_ratio >= 10 THEN 'Medium Stickiness'
        ELSE 'Low Stickiness'
    END as stickiness_category
FROM public.metrics_product_analytics p;

CREATE OR REPLACE VIEW superset_feature_adoption AS
SELECT 
    f.*,
    f.user_adoption_rate * 100 as user_adoption_pct,
    f.account_adoption_rate * 100 as account_adoption_pct,
    CASE 
        WHEN f.user_adoption_rate >= 0.7 THEN 'Well Adopted'
        WHEN f.user_adoption_rate >= 0.3 THEN 'Moderate Adoption'
        ELSE 'Low Adoption'
    END as adoption_status
FROM entity.entity_features f
WHERE f.is_active = true;

-- Executive Dashboard Views
CREATE OR REPLACE VIEW superset_company_metrics AS
SELECT 
    m.metric_name,
    m.metric_category,
    m.current_value,
    m.display_value,
    CASE m.metric_category
        WHEN 'revenue' THEN 1
        WHEN 'customers' THEN 2
        WHEN 'operations' THEN 3
        WHEN 'engagement' THEN 4
        WHEN 'sales' THEN 5
        ELSE 6
    END as sort_order
FROM public.metrics_company_overview m
ORDER BY sort_order, m.metric_name;

CREATE OR REPLACE VIEW superset_executive_summary AS
SELECT 
    u.metric_date,
    u.total_mrr,
    u.active_customers,
    u.avg_customer_health,
    u.pipeline_value,
    u.dau,
    u.mau,
    u.device_availability_pct,
    u.total_mqls,
    -- Calculate growth rates
    LAG(u.total_mrr, 30) OVER (ORDER BY u.metric_date) as mrr_30d_ago,
    ROUND(((u.total_mrr - LAG(u.total_mrr, 30) OVER (ORDER BY u.metric_date)) / 
           NULLIF(LAG(u.total_mrr, 30) OVER (ORDER BY u.metric_date), 0)) * 100, 1) as mrr_growth_30d
FROM public.metrics_unified u
WHERE u.metric_date = CURRENT_DATE;

-- Grant permissions to Superset (if using a specific user)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset_user;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO superset_user;

-- Verify views were created
SELECT 
    schemaname,
    viewname,
    definition IS NOT NULL as has_definition
FROM pg_views 
WHERE schemaname = 'public' 
  AND viewname LIKE 'superset_%'
ORDER BY viewname;