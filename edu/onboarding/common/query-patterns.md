# Common Query Patterns

This guide provides SQL query patterns commonly used across all analytics teams. These patterns leverage the pre-calculated metrics and entity-centric model design.

## 🎯 Basic Patterns

### 1. Current State Analysis
```sql
-- Get current state of any entity
SELECT *
FROM entity.entity_customers
WHERE customer_tier = 'Enterprise'
  AND churn_risk_score > 70
ORDER BY monthly_recurring_revenue DESC;
```

### 2. Time Series Analysis
```sql
-- Analyze trends over time
SELECT 
    date,
    customer_id,
    monthly_recurring_revenue,
    customer_health_score,
    daily_active_users
FROM entity.entity_customers_daily
WHERE customer_id = 'cust_123'
  AND date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date DESC;
```

### 3. Historical Changes
```sql
-- Track changes to an entity over time
SELECT 
    customer_id,
    valid_from,
    valid_to,
    monthly_recurring_revenue,
    customer_health_score,
    change_type
FROM entity.entity_customers_history
WHERE customer_id = 'cust_123'
ORDER BY valid_from DESC;
```

## 📊 Aggregation Patterns

### 1. Cohort Analysis
```sql
-- Monthly cohort retention
WITH cohorts AS (
    SELECT 
        DATE_TRUNC('month', first_subscription_date) as cohort_month,
        customer_id
    FROM entity.entity_customers
    WHERE first_subscription_date IS NOT NULL
)
SELECT 
    c.cohort_month,
    COUNT(DISTINCT c.customer_id) as cohort_size,
    COUNT(DISTINCT CASE 
        WHEN cd.date >= c.cohort_month + INTERVAL '1 month' 
        THEN cd.customer_id 
    END) as month_1_retained,
    COUNT(DISTINCT CASE 
        WHEN cd.date >= c.cohort_month + INTERVAL '2 months' 
        THEN cd.customer_id 
    END) as month_2_retained
FROM cohorts c
LEFT JOIN entity.entity_customers_daily cd
    ON c.customer_id = cd.customer_id
    AND cd.date = DATE_TRUNC('month', cd.date)
GROUP BY c.cohort_month
ORDER BY c.cohort_month DESC;
```

### 2. Period-over-Period Comparison
```sql
-- Compare metrics across time periods
WITH current_period AS (
    SELECT 
        SUM(monthly_recurring_revenue) as current_mrr,
        AVG(customer_health_score) as current_health,
        COUNT(DISTINCT customer_id) as current_customers
    FROM entity.entity_customers
    WHERE is_active = true
),
previous_period AS (
    SELECT 
        SUM(monthly_recurring_revenue) as previous_mrr,
        AVG(customer_health_score) as previous_health,
        COUNT(DISTINCT customer_id) as previous_customers
    FROM entity.entity_customers_daily
    WHERE date = CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    current_mrr,
    previous_mrr,
    (current_mrr - previous_mrr) / NULLIF(previous_mrr, 0) * 100 as mrr_growth_pct,
    current_health,
    previous_health,
    current_health - previous_health as health_change,
    current_customers,
    previous_customers,
    current_customers - previous_customers as customer_change
FROM current_period
CROSS JOIN previous_period;
```

### 3. Segment Analysis
```sql
-- Analyze metrics by customer segment
SELECT 
    customer_tier,
    customer_industry,
    COUNT(DISTINCT customer_id) as customer_count,
    AVG(monthly_recurring_revenue) as avg_mrr,
    AVG(customer_health_score) as avg_health_score,
    AVG(churn_risk_score) as avg_churn_risk,
    SUM(total_active_users) as total_users
FROM entity.entity_customers
WHERE is_active = true
GROUP BY customer_tier, customer_industry
ORDER BY avg_mrr DESC;
```

## 🔄 Join Patterns

### 1. Entity to Metrics Join
```sql
-- Join entity data with domain metrics
SELECT 
    c.customer_id,
    c.company_name,
    c.monthly_recurring_revenue,
    cs.composite_success_score,
    cs.support_tickets_30d,
    cs.ticket_resolution_rate
FROM entity.entity_customers c
LEFT JOIN metrics.customer_success cs
    ON c.customer_id = cs.customer_id
WHERE c.churn_risk_score > 60
ORDER BY cs.composite_success_score ASC;
```

### 2. Cross-Entity Analysis
```sql
-- Analyze relationships between entities
SELECT 
    c.customer_id,
    c.company_name,
    COUNT(DISTINCT d.device_id) as device_count,
    AVG(d.overall_health_score) as avg_device_health,
    SUM(d.total_volume_liters_30d) as total_volume,
    COUNT(DISTINCT l.location_id) as location_count
FROM entity.entity_customers c
LEFT JOIN entity.entity_devices d
    ON c.customer_id = d.customer_id
LEFT JOIN entity.entity_locations l
    ON c.customer_id = l.customer_id
WHERE c.is_active = true
GROUP BY c.customer_id, c.company_name
HAVING COUNT(DISTINCT d.device_id) > 5
ORDER BY total_volume DESC;
```

### 3. Time-Aligned Joins
```sql
-- Join time series data across entities
SELECT 
    cd.date,
    cd.customer_id,
    cd.monthly_recurring_revenue,
    dd.active_device_count,
    dd.avg_device_uptime,
    ud.active_user_count,
    ud.avg_engagement_score
FROM entity.entity_customers_daily cd
LEFT JOIN (
    SELECT 
        date,
        customer_id,
        COUNT(DISTINCT device_id) as active_device_count,
        AVG(uptime_percentage) as avg_device_uptime
    FROM entity.entity_devices_hourly
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY date, customer_id
) dd ON cd.date = dd.date AND cd.customer_id = dd.customer_id
LEFT JOIN (
    SELECT 
        date,
        customer_id,
        COUNT(DISTINCT user_id) as active_user_count,
        AVG(engagement_score) as avg_engagement_score
    FROM entity.entity_users_weekly
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY date, customer_id
) ud ON cd.date = ud.date AND cd.customer_id = ud.customer_id
WHERE cd.date >= CURRENT_DATE - INTERVAL '30 days'
  AND cd.customer_id IN (
    SELECT customer_id 
    FROM entity.entity_customers 
    WHERE customer_tier = 'Enterprise'
  )
ORDER BY cd.date DESC, cd.customer_id;
```

## 🎨 Advanced Patterns

### 1. Moving Averages
```sql
-- Calculate moving averages for smoothing
SELECT 
    date,
    customer_id,
    monthly_recurring_revenue,
    AVG(monthly_recurring_revenue) OVER (
        PARTITION BY customer_id 
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as mrr_7day_avg,
    AVG(monthly_recurring_revenue) OVER (
        PARTITION BY customer_id 
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as mrr_30day_avg
FROM entity.entity_customers_daily
WHERE customer_id = 'cust_123'
  AND date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date DESC;
```

### 2. Ranking and Percentiles
```sql
-- Rank customers by various metrics
SELECT 
    customer_id,
    company_name,
    monthly_recurring_revenue,
    customer_health_score,
    RANK() OVER (ORDER BY monthly_recurring_revenue DESC) as mrr_rank,
    PERCENT_RANK() OVER (ORDER BY monthly_recurring_revenue DESC) as mrr_percentile,
    NTILE(10) OVER (ORDER BY customer_health_score DESC) as health_decile
FROM entity.entity_customers
WHERE is_active = true
ORDER BY mrr_rank;
```

### 3. Funnel Analysis
```sql
-- Analyze conversion funnel
WITH funnel_stages AS (
    SELECT 
        mql.lead_id,
        mql.created_at as mql_date,
        sql.created_at as sql_date,
        opp.created_at as opportunity_date,
        deal.close_date as deal_close_date
    FROM marketing_qualified_leads mql
    LEFT JOIN sales_qualified_leads sql
        ON mql.lead_id = sql.lead_id
    LEFT JOIN opportunities opp
        ON sql.lead_id = opp.lead_id
    LEFT JOIN deals deal
        ON opp.opportunity_id = deal.opportunity_id
    WHERE mql.created_at >= CURRENT_DATE - INTERVAL '90 days'
)
SELECT 
    COUNT(DISTINCT lead_id) as total_mqls,
    COUNT(DISTINCT CASE WHEN sql_date IS NOT NULL THEN lead_id END) as converted_to_sql,
    COUNT(DISTINCT CASE WHEN opportunity_date IS NOT NULL THEN lead_id END) as converted_to_opp,
    COUNT(DISTINCT CASE WHEN deal_close_date IS NOT NULL THEN lead_id END) as converted_to_deal,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN sql_date IS NOT NULL THEN lead_id END) / 
          NULLIF(COUNT(DISTINCT lead_id), 0), 2) as mql_to_sql_rate,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN opportunity_date IS NOT NULL THEN lead_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN sql_date IS NOT NULL THEN lead_id END), 0), 2) as sql_to_opp_rate,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN deal_close_date IS NOT NULL THEN lead_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN opportunity_date IS NOT NULL THEN lead_id END), 0), 2) as opp_to_deal_rate
FROM funnel_stages;
```

## 💡 Performance Tips

### 1. Use Pre-Calculated Metrics
```sql
-- ❌ Avoid calculating metrics on the fly
SELECT 
    customer_id,
    SUM(subscription_amount) / COUNT(DISTINCT DATE_TRUNC('month', date)) as calculated_mrr
FROM subscriptions
GROUP BY customer_id;

-- ✅ Use pre-calculated metrics
SELECT 
    customer_id,
    monthly_recurring_revenue
FROM entity.entity_customers;
```

### 2. Filter Early
```sql
-- ❌ Filter after joining
SELECT *
FROM entity.entity_customers c
JOIN entity.entity_devices d ON c.customer_id = d.customer_id
WHERE c.customer_tier = 'Enterprise';

-- ✅ Filter before joining
SELECT *
FROM (
    SELECT * FROM entity.entity_customers 
    WHERE customer_tier = 'Enterprise'
) c
JOIN entity.entity_devices d ON c.customer_id = d.customer_id;
```

### 3. Use Appropriate Time Grains
```sql
-- For daily analysis, use daily tables
SELECT * FROM entity.entity_customers_daily WHERE date >= CURRENT_DATE - 7;

-- For monthly trends, use monthly tables
SELECT * FROM entity.entity_subscriptions_monthly WHERE date >= CURRENT_DATE - INTERVAL '12 months';
```