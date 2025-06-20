-- Sales Dashboard SQL Queries

-- 1. KPI Metrics (from metrics_sales view)
SELECT 
    total_revenue,
    pipeline_value,
    win_rate,
    avg_won_deal_size,
    total_deals,
    won_deals,
    open_deals,
    mqls_last_30d
FROM public.metrics_sales;

-- 2. Pipeline Funnel Analysis
SELECT 
    stage_name,
    stage_order,
    COUNT(DISTINCT deal_id) as deal_count,
    SUM(amount) as total_value,
    AVG(amount) as avg_deal_size,
    AVG(days_in_stage) as avg_days_in_stage
FROM mart.mart_sales__pipeline
WHERE is_active = true
GROUP BY stage_name, stage_order
ORDER BY stage_order;

-- 3. Revenue Trend (Daily)
SELECT 
    date as revenue_date,
    SUM(new_mrr + expansion_revenue - contraction_revenue - churned_revenue) as net_revenue,
    SUM(new_mrr) as new_revenue,
    SUM(expansion_revenue) as expansion_revenue,
    SUM(churned_revenue) as lost_revenue
FROM entity.entity_customers_daily
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date
ORDER BY date;

-- 4. Top Open Deals
SELECT 
    deal_id,
    deal_name,
    company_name,
    owner_name,
    stage_name,
    amount,
    close_date,
    probability,
    days_open,
    last_activity_date
FROM mart.mart_sales__pipeline
WHERE stage_name NOT IN ('Closed Won', 'Closed Lost')
ORDER BY amount DESC
LIMIT 10;

-- 5. Sales Rep Performance
SELECT 
    owner_name as sales_rep,
    COUNT(DISTINCT CASE WHEN stage_name = 'Closed Won' THEN deal_id END) as deals_won,
    COUNT(DISTINCT deal_id) as total_deals,
    SUM(CASE WHEN stage_name = 'Closed Won' THEN amount ELSE 0 END) as revenue,
    AVG(CASE WHEN stage_name = 'Closed Won' THEN days_to_close END) as avg_sales_cycle,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN stage_name = 'Closed Won' THEN deal_id END) / 
          NULLIF(COUNT(DISTINCT deal_id), 0), 1) as win_rate
FROM mart.mart_sales__pipeline
WHERE created_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY owner_name
ORDER BY revenue DESC;

-- 6. Deal Velocity by Stage
SELECT 
    stage_name,
    DATE_TRUNC('week', updated_date) as week,
    AVG(days_in_stage) as avg_days_in_stage,
    COUNT(DISTINCT deal_id) as deals_in_stage
FROM mart.mart_sales__pipeline
WHERE updated_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY stage_name, DATE_TRUNC('week', updated_date)
ORDER BY week DESC, stage_name;

-- 7. Lead Source Analysis
SELECT 
    lead_source,
    COUNT(DISTINCT mql_id) as lead_count,
    AVG(mql_score) as avg_score,
    SUM(CASE WHEN became_customer = true THEN 1 ELSE 0 END) as converted_count,
    ROUND(100.0 * SUM(CASE WHEN became_customer = true THEN 1 ELSE 0 END) / 
          NULLIF(COUNT(DISTINCT mql_id), 0), 1) as conversion_rate
FROM marketing.marketing_qualified_leads
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY lead_source
ORDER BY lead_count DESC;

-- 8. Monthly Sales Targets vs Actuals
SELECT 
    DATE_TRUNC('month', close_date) as month,
    SUM(amount) as actual_revenue,
    MAX(monthly_target) as target_revenue,
    ROUND(100.0 * SUM(amount) / NULLIF(MAX(monthly_target), 0), 1) as attainment_pct
FROM mart.mart_sales__pipeline
LEFT JOIN sales_targets USING (month)
WHERE stage_name = 'Closed Won'
  AND close_date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', close_date)
ORDER BY month DESC;

-- 9. Deal Age Distribution
SELECT 
    CASE 
        WHEN days_open < 30 THEN '0-30 days'
        WHEN days_open < 60 THEN '30-60 days'
        WHEN days_open < 90 THEN '60-90 days'
        ELSE '90+ days'
    END as age_bucket,
    COUNT(DISTINCT deal_id) as deal_count,
    SUM(amount) as total_value
FROM mart.mart_sales__pipeline
WHERE stage_name NOT IN ('Closed Won', 'Closed Lost')
GROUP BY age_bucket
ORDER BY age_bucket;

-- 10. Win/Loss Analysis
SELECT 
    DATE_TRUNC('month', close_date) as month,
    COUNT(DISTINCT CASE WHEN stage_name = 'Closed Won' THEN deal_id END) as won_deals,
    COUNT(DISTINCT CASE WHEN stage_name = 'Closed Lost' THEN deal_id END) as lost_deals,
    SUM(CASE WHEN stage_name = 'Closed Won' THEN amount ELSE 0 END) as won_revenue,
    SUM(CASE WHEN stage_name = 'Closed Lost' THEN amount ELSE 0 END) as lost_revenue
FROM mart.mart_sales__pipeline
WHERE close_date IS NOT NULL
  AND close_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', close_date)
ORDER BY month DESC;