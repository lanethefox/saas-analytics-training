-- Sales Dashboard Setup for Superset
-- Run these queries to create virtual datasets for the Sales dashboard

-- 1. Sales KPIs Dataset
CREATE OR REPLACE VIEW superset_sales_kpis AS
SELECT 
    CURRENT_DATE as metric_date,
    total_revenue,
    pipeline_value,
    win_rate * 100 as win_rate_pct,
    avg_won_deal_size,
    total_deals,
    won_deals,
    open_deals,
    mqls_last_30d as monthly_leads,
    total_mqls as total_leads
FROM public.metrics_sales;

-- 2. Pipeline Stages Dataset
CREATE OR REPLACE VIEW superset_sales_pipeline_stages AS
SELECT 
    stage_name,
    CASE stage_name
        WHEN 'Lead' THEN 1
        WHEN 'Qualified' THEN 2  
        WHEN 'Proposal' THEN 3
        WHEN 'Negotiation' THEN 4
        WHEN 'Closed Won' THEN 5
        WHEN 'Closed Lost' THEN 6
        ELSE 7
    END as stage_order,
    COUNT(DISTINCT deal_id) as deal_count,
    SUM(amount) as stage_value,
    AVG(amount) as avg_deal_size,
    AVG(days_in_stage) as avg_days_in_stage,
    SUM(CASE WHEN days_in_stage > 30 THEN 1 ELSE 0 END) as stalled_deals
FROM mart.mart_sales__pipeline
WHERE is_active = true
  OR stage_name IN ('Closed Won', 'Closed Lost')
GROUP BY stage_name;

-- 3. Daily Revenue Trend Dataset
CREATE OR REPLACE VIEW superset_sales_daily_revenue AS
SELECT 
    date,
    SUM(new_mrr) as new_revenue,
    SUM(expansion_revenue) as expansion_revenue,
    SUM(churned_revenue) as lost_revenue,
    SUM(new_mrr + expansion_revenue - churned_revenue) as net_revenue,
    COUNT(DISTINCT CASE WHEN new_mrr > 0 THEN customer_id END) as new_customers,
    COUNT(DISTINCT CASE WHEN churned_revenue > 0 THEN customer_id END) as churned_customers
FROM entity.entity_customers_daily
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY date;

-- 4. Sales Rep Performance Dataset
CREATE OR REPLACE VIEW superset_sales_rep_performance AS
SELECT 
    owner_name as sales_rep,
    COUNT(DISTINCT deal_id) as total_opportunities,
    COUNT(DISTINCT CASE WHEN stage_name = 'Closed Won' THEN deal_id END) as won_deals,
    COUNT(DISTINCT CASE WHEN stage_name = 'Closed Lost' THEN deal_id END) as lost_deals,
    SUM(CASE WHEN stage_name = 'Closed Won' THEN amount ELSE 0 END) as closed_revenue,
    SUM(CASE WHEN stage_name NOT IN ('Closed Won', 'Closed Lost') THEN amount ELSE 0 END) as pipeline_value,
    AVG(CASE WHEN stage_name = 'Closed Won' THEN days_to_close END) as avg_sales_cycle_days,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN stage_name = 'Closed Won' THEN deal_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN stage_name IN ('Closed Won', 'Closed Lost') THEN deal_id END), 0), 1) as win_rate_pct,
    MAX(CASE WHEN stage_name = 'Closed Won' THEN close_date END) as last_won_date
FROM mart.mart_sales__pipeline
GROUP BY owner_name;

-- 5. Deal Details Dataset  
CREATE OR REPLACE VIEW superset_sales_deals AS
SELECT 
    deal_id,
    deal_name,
    company_name,
    owner_name,
    stage_name,
    amount,
    close_date,
    created_date,
    days_open,
    days_in_stage,
    probability,
    is_active,
    last_activity_date,
    CASE 
        WHEN days_in_stage > 30 THEN 'Stalled'
        WHEN close_date < CURRENT_DATE AND stage_name NOT IN ('Closed Won', 'Closed Lost') THEN 'Overdue'
        WHEN probability >= 80 THEN 'Hot'
        WHEN probability >= 50 THEN 'Warm'
        ELSE 'Cold'
    END as deal_temperature,
    CASE 
        WHEN amount >= 50000 THEN 'Enterprise'
        WHEN amount >= 10000 THEN 'Mid-Market'
        ELSE 'SMB'
    END as deal_size_segment
FROM mart.mart_sales__pipeline;

-- 6. Lead Source Performance Dataset
CREATE OR REPLACE VIEW superset_sales_lead_sources AS
SELECT 
    mql.lead_source,
    COUNT(DISTINCT mql.mql_id) as lead_count,
    AVG(mql.mql_score) as avg_lead_score,
    COUNT(DISTINCT CASE WHEN mql.became_customer = true THEN mql.mql_id END) as converted_leads,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN mql.became_customer = true THEN mql.mql_id END) / 
          NULLIF(COUNT(DISTINCT mql.mql_id), 0), 1) as conversion_rate_pct,
    SUM(d.amount) as attributed_revenue,
    AVG(CASE WHEN mql.became_customer = true THEN 
        EXTRACT(EPOCH FROM (c.created_at - mql.created_at)) / 86400 
    END) as avg_days_to_convert
FROM marketing.marketing_qualified_leads mql
LEFT JOIN raw.accounts c ON mql.account_id = c.account_id
LEFT JOIN mart.mart_sales__pipeline d ON c.account_id = d.account_id 
    AND d.stage_name = 'Closed Won'
WHERE mql.created_at >= CURRENT_DATE - INTERVAL '180 days'
GROUP BY mql.lead_source;

-- 7. Monthly Sales Metrics Dataset
CREATE OR REPLACE VIEW superset_sales_monthly_metrics AS
SELECT 
    DATE_TRUNC('month', close_date) as month,
    COUNT(DISTINCT CASE WHEN stage_name = 'Closed Won' THEN deal_id END) as won_deals,
    COUNT(DISTINCT CASE WHEN stage_name = 'Closed Lost' THEN deal_id END) as lost_deals,
    SUM(CASE WHEN stage_name = 'Closed Won' THEN amount ELSE 0 END) as won_revenue,
    SUM(CASE WHEN stage_name = 'Closed Lost' THEN amount ELSE 0 END) as lost_revenue,
    AVG(CASE WHEN stage_name = 'Closed Won' THEN amount END) as avg_won_deal_size,
    AVG(CASE WHEN stage_name = 'Closed Won' THEN days_to_close END) as avg_sales_cycle,
    COUNT(DISTINCT owner_name) as active_reps
FROM mart.mart_sales__pipeline
WHERE close_date IS NOT NULL
GROUP BY DATE_TRUNC('month', close_date);

-- 8. Deal Aging Analysis Dataset
CREATE OR REPLACE VIEW superset_sales_deal_aging AS
SELECT 
    CASE 
        WHEN days_open <= 30 THEN '0-30 days'
        WHEN days_open <= 60 THEN '31-60 days'
        WHEN days_open <= 90 THEN '61-90 days'
        WHEN days_open <= 120 THEN '91-120 days'
        ELSE '120+ days'
    END as age_bucket,
    CASE 
        WHEN days_open <= 30 THEN 1
        WHEN days_open <= 60 THEN 2
        WHEN days_open <= 90 THEN 3
        WHEN days_open <= 120 THEN 4
        ELSE 5
    END as age_order,
    stage_name,
    COUNT(DISTINCT deal_id) as deal_count,
    SUM(amount) as total_value,
    AVG(amount) as avg_deal_size,
    AVG(probability) as avg_probability
FROM mart.mart_sales__pipeline
WHERE is_active = true
GROUP BY age_bucket, age_order, stage_name;

-- Grant permissions to Superset user (if needed)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO superset_user;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO superset_user;
GRANT SELECT ON ALL TABLES IN SCHEMA entity TO superset_user;
GRANT SELECT ON ALL TABLES IN SCHEMA marketing TO superset_user;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_pipeline_stage_date ON mart.mart_sales__pipeline(stage_name, close_date);
CREATE INDEX IF NOT EXISTS idx_pipeline_owner ON mart.mart_sales__pipeline(owner_name);
CREATE INDEX IF NOT EXISTS idx_customers_daily_date ON entity.entity_customers_daily(date);
CREATE INDEX IF NOT EXISTS idx_mqls_source_date ON marketing.marketing_qualified_leads(lead_source, created_at);