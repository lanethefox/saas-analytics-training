#!/bin/bash

# Create Superset views in PostgreSQL
export PGPASSWORD='saas_secure_password_2024'

echo "Creating Superset views for Sales dashboard..."

docker exec -i saas_platform_postgres psql -U saas_user -d saas_platform_dev << 'EOF'
-- Sales Dashboard Views for Superset

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

-- 6. Monthly Sales Metrics Dataset
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

-- Check that views were created
SELECT 'Created ' || COUNT(*) || ' views' FROM information_schema.views 
WHERE table_schema = 'public' AND table_name LIKE 'superset_sales_%';

EOF

echo "✓ Sales dashboard views created successfully!"