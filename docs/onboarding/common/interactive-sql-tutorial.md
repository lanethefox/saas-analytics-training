# Interactive SQL Tutorial for SaaS Analytics Platform

This hands-on tutorial will teach you SQL queries specific to our data platform. Copy and run these queries in your SQL client connected to `saas_platform_dev`.

## 🎯 Tutorial Overview

- **Level 1**: Basic SELECT queries
- **Level 2**: JOINs and relationships
- **Level 3**: Aggregations and grouping
- **Level 4**: Window functions
- **Level 5**: CTEs and complex queries

---

## 📚 Level 1: Basic SELECT Queries

### Exercise 1.1: Your First Query
```sql
-- TODO: Run this query to see all active customers
SELECT 
    customer_id,
    company_name,
    customer_tier,
    monthly_recurring_revenue
FROM entity.entity_customers
WHERE is_active = true
LIMIT 10;

-- ✅ Expected: 10 rows of customer data
-- 💡 Learning: Basic SELECT, WHERE, LIMIT
```

### Exercise 1.2: Filtering and Sorting
```sql
-- TODO: Find Enterprise customers with high MRR
SELECT 
    customer_id,
    company_name,
    monthly_recurring_revenue,
    customer_health_score
FROM entity.entity_customers
WHERE customer_tier = 'Enterprise'
  AND monthly_recurring_revenue > 5000
ORDER BY monthly_recurring_revenue DESC;

-- ✅ Expected: Enterprise customers sorted by MRR
-- 💡 Learning: Multiple WHERE conditions, ORDER BY
```

### Exercise 1.3: Working with Dates
```sql
-- TODO: Find customers who joined in the last 90 days
SELECT 
    customer_id,
    company_name,
    first_subscription_date,
    months_since_first_subscription
FROM entity.entity_customers
WHERE first_subscription_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY first_subscription_date DESC;

-- ✅ Expected: Recent customers
-- 💡 Learning: Date arithmetic, INTERVAL
```

### 🏆 Level 1 Challenge
```sql
-- TODO: Find at-risk SMB customers
-- Hint: Use customer_tier, churn_risk_score, and is_active
-- Your query here:




-- Solution (try first!):
-- SELECT customer_id, company_name, churn_risk_score
-- FROM entity.entity_customers
-- WHERE customer_tier = 'SMB'
--   AND churn_risk_score > 70
--   AND is_active = true
-- ORDER BY churn_risk_score DESC;
```

---

## 🔗 Level 2: JOINs and Relationships

### Exercise 2.1: Basic JOIN
```sql
-- TODO: Join customers with their users
SELECT 
    c.customer_id,
    c.company_name,
    u.user_id,
    u.email,
    u.engagement_score
FROM entity.entity_customers c
JOIN entity.entity_users u ON c.customer_id = u.customer_id
WHERE c.customer_tier = 'Enterprise'
  AND u.user_status = 'active'
LIMIT 20;

-- ✅ Expected: Customer-user pairs
-- 💡 Learning: INNER JOIN, table aliases
```

### Exercise 2.2: LEFT JOIN
```sql
-- TODO: Find customers with NO active users (potential churn risk)
SELECT 
    c.customer_id,
    c.company_name,
    c.customer_health_score,
    COUNT(u.user_id) as active_user_count
FROM entity.entity_customers c
LEFT JOIN entity.entity_users u 
    ON c.customer_id = u.customer_id
    AND u.user_status = 'active'
WHERE c.is_active = true
GROUP BY c.customer_id, c.company_name, c.customer_health_score
HAVING COUNT(u.user_id) = 0
ORDER BY c.customer_health_score ASC;

-- ✅ Expected: Customers without active users
-- 💡 Learning: LEFT JOIN, GROUP BY, HAVING
```

### Exercise 2.3: Multiple JOINs
```sql
-- TODO: Customer overview with devices and locations
SELECT 
    c.customer_id,
    c.company_name,
    COUNT(DISTINCT l.location_id) as location_count,
    COUNT(DISTINCT d.device_id) as device_count,
    AVG(d.overall_health_score) as avg_device_health
FROM entity.entity_customers c
LEFT JOIN entity.entity_locations l ON c.customer_id = l.customer_id
LEFT JOIN entity.entity_devices d ON l.location_id = d.location_id
WHERE c.is_active = true
GROUP BY c.customer_id, c.company_name
HAVING COUNT(DISTINCT d.device_id) > 0
ORDER BY device_count DESC;

-- ✅ Expected: Customer device summary
-- 💡 Learning: Multiple JOINs, COUNT DISTINCT
```

### 🏆 Level 2 Challenge
```sql
-- TODO: Find customers with high-value but low engagement
-- Join customers, users, and subscriptions
-- Filter for MRR > 5000 but avg engagement < 50
-- Your query here:




-- Hint: You'll need entity_customers, entity_users, and calculate AVG(engagement_score)
```

---

## 📊 Level 3: Aggregations and Analytics

### Exercise 3.1: Basic Aggregations
```sql
-- TODO: Customer tier summary
SELECT 
    customer_tier,
    COUNT(*) as customer_count,
    SUM(monthly_recurring_revenue) as total_mrr,
    AVG(monthly_recurring_revenue) as avg_mrr,
    AVG(customer_health_score) as avg_health_score,
    AVG(churn_risk_score) as avg_churn_risk
FROM entity.entity_customers
WHERE is_active = true
GROUP BY customer_tier
ORDER BY total_mrr DESC;

-- ✅ Expected: Summary by tier
-- 💡 Learning: GROUP BY, aggregate functions
```

### Exercise 3.2: Time-based Aggregations
```sql
-- TODO: Monthly cohort analysis
SELECT 
    DATE_TRUNC('month', first_subscription_date) as cohort_month,
    COUNT(DISTINCT customer_id) as customers_joined,
    SUM(monthly_recurring_revenue) as cohort_mrr,
    AVG(lifetime_value) as avg_ltv,
    AVG(months_since_first_subscription) as avg_tenure
FROM entity.entity_customers
WHERE first_subscription_date IS NOT NULL
GROUP BY DATE_TRUNC('month', first_subscription_date)
ORDER BY cohort_month DESC
LIMIT 12;

-- ✅ Expected: Last 12 monthly cohorts
-- 💡 Learning: DATE_TRUNC, time-based grouping
```

### Exercise 3.3: Conditional Aggregations
```sql
-- TODO: Health score distribution
SELECT 
    CASE 
        WHEN customer_health_score >= 80 THEN 'Healthy (80-100)'
        WHEN customer_health_score >= 60 THEN 'Neutral (60-79)'
        WHEN customer_health_score >= 40 THEN 'At Risk (40-59)'
        ELSE 'Critical (0-39)'
    END as health_segment,
    COUNT(*) as customer_count,
    SUM(monthly_recurring_revenue) as segment_mrr,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct_of_customers
FROM entity.entity_customers
WHERE is_active = true
GROUP BY health_segment
ORDER BY 
    CASE health_segment
        WHEN 'Healthy (80-100)' THEN 1
        WHEN 'Neutral (60-79)' THEN 2
        WHEN 'At Risk (40-59)' THEN 3
        ELSE 4
    END;

-- ✅ Expected: Customer distribution by health
-- 💡 Learning: CASE statements, window functions
```

### 🏆 Level 3 Challenge
```sql
-- TODO: Calculate month-over-month growth rate
-- Show customer count and MRR growth by month
-- Your query here:




-- Hint: Use LAG() window function
```

---

## 🚀 Level 4: Window Functions

### Exercise 4.1: Ranking Functions
```sql
-- TODO: Top customers by MRR with rankings
SELECT 
    customer_id,
    company_name,
    customer_tier,
    monthly_recurring_revenue,
    RANK() OVER (ORDER BY monthly_recurring_revenue DESC) as mrr_rank,
    DENSE_RANK() OVER (PARTITION BY customer_tier ORDER BY monthly_recurring_revenue DESC) as tier_rank,
    PERCENT_RANK() OVER (ORDER BY monthly_recurring_revenue DESC) as mrr_percentile
FROM entity.entity_customers
WHERE is_active = true
ORDER BY mrr_rank
LIMIT 20;

-- ✅ Expected: Ranked customers
-- 💡 Learning: RANK, DENSE_RANK, PERCENT_RANK
```

### Exercise 4.2: Moving Averages
```sql
-- TODO: 7-day moving average of daily active users
SELECT 
    date,
    customer_id,
    daily_active_users,
    AVG(daily_active_users) OVER (
        PARTITION BY customer_id 
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as dau_7day_avg,
    daily_active_users - LAG(daily_active_users, 7) OVER (
        PARTITION BY customer_id ORDER BY date
    ) as dau_week_over_week_change
FROM entity.entity_customers_daily
WHERE customer_id IN (
    SELECT customer_id 
    FROM entity.entity_customers 
    WHERE customer_tier = 'Enterprise' 
    LIMIT 5
)
  AND date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY customer_id, date DESC;

-- ✅ Expected: Smoothed metrics
-- 💡 Learning: Moving windows, LAG
```

### Exercise 4.3: Cumulative Calculations
```sql
-- TODO: Running total of new customers by month
WITH monthly_customers AS (
    SELECT 
        DATE_TRUNC('month', first_subscription_date) as month,
        COUNT(*) as new_customers,
        SUM(monthly_recurring_revenue) as new_mrr
    FROM entity.entity_customers
    WHERE first_subscription_date >= '2024-01-01'
    GROUP BY DATE_TRUNC('month', first_subscription_date)
)
SELECT 
    month,
    new_customers,
    new_mrr,
    SUM(new_customers) OVER (ORDER BY month) as cumulative_customers,
    SUM(new_mrr) OVER (ORDER BY month) as cumulative_mrr
FROM monthly_customers
ORDER BY month;

-- ✅ Expected: Running totals
-- 💡 Learning: Cumulative SUM
```

### 🏆 Level 4 Challenge
```sql
-- TODO: Find customers with improving health scores
-- Use window functions to calculate health score trend
-- Your query here:




-- Hint: Compare current health score to 30 days ago
```

---

## 🎨 Level 5: CTEs and Complex Queries

### Exercise 5.1: Multi-step Analysis with CTEs
```sql
-- TODO: Customer success score calculation
WITH user_metrics AS (
    -- Step 1: Aggregate user data
    SELECT 
        customer_id,
        COUNT(DISTINCT user_id) as total_users,
        COUNT(DISTINCT CASE WHEN days_since_last_login <= 7 THEN user_id END) as active_users,
        AVG(engagement_score) as avg_engagement
    FROM entity.entity_users
    WHERE user_status = 'active'
    GROUP BY customer_id
),
device_metrics AS (
    -- Step 2: Aggregate device data
    SELECT 
        customer_id,
        COUNT(DISTINCT device_id) as total_devices,
        AVG(overall_health_score) as avg_device_health,
        AVG(uptime_percentage_30d) as avg_uptime
    FROM entity.entity_devices
    WHERE device_status = 'active'
    GROUP BY customer_id
),
combined_metrics AS (
    -- Step 3: Combine all metrics
    SELECT 
        c.customer_id,
        c.company_name,
        c.customer_tier,
        c.monthly_recurring_revenue,
        c.customer_health_score,
        u.total_users,
        u.active_users,
        u.avg_engagement,
        d.total_devices,
        d.avg_device_health,
        d.avg_uptime,
        -- Calculate composite score
        (
            c.customer_health_score * 0.3 +
            COALESCE(u.avg_engagement, 0) * 0.3 +
            COALESCE(d.avg_device_health, 0) * 0.2 +
            COALESCE(d.avg_uptime, 0) * 0.2
        ) as composite_success_score
    FROM entity.entity_customers c
    LEFT JOIN user_metrics u ON c.customer_id = u.customer_id
    LEFT JOIN device_metrics d ON c.customer_id = d.customer_id
    WHERE c.is_active = true
)
-- Step 4: Final output with rankings
SELECT 
    *,
    RANK() OVER (ORDER BY composite_success_score DESC) as success_rank,
    CASE 
        WHEN composite_success_score >= 80 THEN 'Excellent'
        WHEN composite_success_score >= 60 THEN 'Good'
        WHEN composite_success_score >= 40 THEN 'Fair'
        ELSE 'Poor'
    END as success_category
FROM combined_metrics
ORDER BY success_rank
LIMIT 20;

-- ✅ Expected: Comprehensive success scoring
-- 💡 Learning: Multiple CTEs, complex calculations
```

### Exercise 5.2: Recursive CTE (Advanced)
```sql
-- TODO: Organization hierarchy (if applicable)
WITH RECURSIVE org_hierarchy AS (
    -- Base case: top-level customers
    SELECT 
        customer_id,
        company_name,
        parent_customer_id,
        1 as level,
        customer_id::text as path
    FROM entity.entity_customers
    WHERE parent_customer_id IS NULL
      AND is_active = true
    
    UNION ALL
    
    -- Recursive case: child customers
    SELECT 
        c.customer_id,
        c.company_name,
        c.parent_customer_id,
        oh.level + 1,
        oh.path || ' > ' || c.customer_id::text
    FROM entity.entity_customers c
    JOIN org_hierarchy oh ON c.parent_customer_id = oh.customer_id
    WHERE c.is_active = true
)
SELECT 
    level,
    customer_id,
    company_name,
    path
FROM org_hierarchy
ORDER BY path;

-- ✅ Expected: Hierarchical structure
-- 💡 Learning: Recursive CTEs
```

### 🏆 Level 5 Final Challenge
```sql
-- TODO: Build a complete customer 360 view
-- Include: customer info, user stats, device health, subscription details, and risk scores
-- Use at least 3 CTEs
-- Your query here:




-- This is your final test - combine everything you've learned!
```

---

## 🎓 Tutorial Completion

### Your Progress Checklist
- [ ] Completed Level 1: Basic queries
- [ ] Completed Level 2: JOINs
- [ ] Completed Level 3: Aggregations
- [ ] Completed Level 4: Window functions
- [ ] Completed Level 5: CTEs

### Next Steps
1. Save your solutions in a personal folder
2. Try modifying queries for different use cases
3. Create your own exercises
4. Share knowledge with teammates

### Quick Reference Card
```sql
-- Entity tables
entity.entity_customers      -- Customer master data
entity.entity_users         -- User engagement
entity.entity_devices       -- Device metrics
entity.entity_locations     -- Location data
entity.entity_subscriptions -- Billing info

-- Metrics tables
metrics.sales               -- Sales KPIs
metrics.customer_success    -- CS metrics
metrics.marketing          -- Marketing ROI
metrics.product_analytics  -- Product usage

-- Common patterns
WHERE is_active = true                          -- Active records only
WHERE date >= CURRENT_DATE - INTERVAL '30 days' -- Last 30 days
GROUP BY customer_tier                          -- Segment analysis
ORDER BY metric DESC LIMIT 10                   -- Top 10
JOIN table ON condition                         -- Combining data
```

### 🏆 Certificate of Completion
Once you complete all levels, you'll be ready to:
- Write production queries
- Create dashboards
- Analyze business metrics
- Train other analysts

Happy querying! 🚀