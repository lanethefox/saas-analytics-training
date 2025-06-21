# Analytics Best Practices

This guide outlines best practices for working with the SaaS Analytics Platform to ensure accurate, efficient, and maintainable analyses.

## 🎯 Query Best Practices

### 1. Use Pre-Calculated Metrics First
```sql
-- ❌ Don't recalculate existing metrics
SELECT 
    customer_id,
    SUM(subscription_amount) / COUNT(DISTINCT month) as calculated_mrr,
    COUNT(DISTINCT user_id) as user_count
FROM raw_subscriptions
GROUP BY customer_id;

-- ✅ Use pre-calculated metrics
SELECT 
    customer_id,
    monthly_recurring_revenue,
    total_users
FROM entity.entity_customers;
```

### 2. Filter Early and Specifically
```sql
-- ❌ Filter after expensive operations
SELECT *
FROM (
    SELECT 
        c.*,
        COUNT(d.device_id) as device_count
    FROM entity.entity_customers c
    LEFT JOIN entity.entity_devices d ON c.customer_id = d.customer_id
    GROUP BY c.customer_id
) t
WHERE customer_tier = 'Enterprise';

-- ✅ Filter before joins and aggregations
WITH enterprise_customers AS (
    SELECT *
    FROM entity.entity_customers
    WHERE customer_tier = 'Enterprise'
      AND is_active = true
)
SELECT 
    c.*,
    COUNT(d.device_id) as device_count
FROM enterprise_customers c
LEFT JOIN entity.entity_devices d ON c.customer_id = d.customer_id
GROUP BY c.customer_id;
```

### 3. Use Appropriate Time Grains
```sql
-- For different analysis periods, use the right table:
-- Daily analysis → entity_*_daily
-- Weekly trends → entity_*_weekly  
-- Monthly reporting → entity_*_monthly

-- ❌ Don't aggregate daily data for monthly reports
SELECT 
    DATE_TRUNC('month', date) as month,
    AVG(metric_value) as avg_metric
FROM entity.entity_customers_daily
GROUP BY DATE_TRUNC('month', date);

-- ✅ Use monthly grain tables
SELECT 
    date as month,
    metric_value as avg_metric
FROM entity.entity_customers_monthly;
```

### 4. Leverage Indexes
```sql
-- Common indexed columns:
-- - customer_id (all tables)
-- - date (time-series tables)
-- - is_active (entity tables)
-- - customer_tier (customer tables)

-- ✅ Query uses indexed columns
SELECT *
FROM entity.entity_customers
WHERE customer_id = 'cust_123'
  AND date = '2024-01-20';
```

## 📊 Dashboard Best Practices

### 1. Performance Optimization
- **Limit time ranges**: Default to last 30-90 days
- **Use materialized views**: For complex calculations
- **Aggregate appropriately**: Don't show raw records
- **Cache when possible**: For slowly changing data

### 2. Design Principles
- **Clear titles**: Describe what the metric shows
- **Consistent colors**: Use standard palette
- **Appropriate charts**: 
  - Time series → Line charts
  - Comparisons → Bar charts
  - Proportions → Pie/donut charts
  - Relationships → Scatter plots
- **Interactive filters**: Customer tier, date range, etc.

### 3. Dashboard Structure
```
Executive Dashboard
├── KPI Summary (top metrics)
├── Trend Analysis (time series)
├── Segment Breakdown (comparisons)
└── Drill-down Tables (details)
```

## 🔍 Analysis Best Practices

### 1. Start with Questions
Before writing queries, define:
- What business question are you answering?
- Who is the audience?
- What decisions will this inform?
- What's the required accuracy/precision?

### 2. Validate Your Data
```sql
-- Always check data quality
WITH data_quality_check AS (
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(CASE WHEN customer_id IS NULL THEN 1 END) as null_customers,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(CASE WHEN monthly_recurring_revenue < 0 THEN 1 END) as negative_mrr
    FROM entity.entity_customers
)
SELECT * FROM data_quality_check;
```

### 3. Document Your Work
```sql
/*
Purpose: Identify high-value customers at risk of churn
Author: Jane Smith
Date: 2024-01-20
Stakeholder: Customer Success Team
Notes: 
- High value = top 20% by MRR
- At risk = churn score > 60
*/

WITH high_value_customers AS (
    -- Query implementation
)
```

### 4. Consider Statistical Significance
- Don't report on small sample sizes
- Include confidence intervals when appropriate
- Account for seasonality and trends
- Validate findings with multiple approaches

## 🚀 Performance Tips

### 1. Query Optimization Checklist
- [ ] Use SELECT only needed columns (avoid SELECT *)
- [ ] Filter on indexed columns
- [ ] Use appropriate JOIN types
- [ ] Limit result sets with LIMIT
- [ ] Use CTEs instead of subqueries
- [ ] Avoid DISTINCT when possible

### 2. Common Performance Patterns
```sql
-- Use EXISTS instead of IN for large lists
-- ❌ Slow
WHERE customer_id IN (SELECT customer_id FROM large_table)

-- ✅ Fast
WHERE EXISTS (SELECT 1 FROM large_table lt WHERE lt.customer_id = t.customer_id)

-- Pre-aggregate before joining
-- ✅ Aggregate first, then join
WITH customer_metrics AS (
    SELECT customer_id, SUM(amount) as total
    FROM transactions
    GROUP BY customer_id
)
SELECT c.*, cm.total
FROM customers c
JOIN customer_metrics cm ON c.customer_id = cm.customer_id;
```

## 🔐 Data Governance

### 1. Access Control
- Only query data you're authorized to access
- Respect customer privacy
- Don't share sensitive data
- Use aggregated data when possible

### 2. PII Handling
- Customer names → Use customer_id
- Email addresses → Already hashed
- Phone numbers → Not stored
- Financial data → Aggregate only

### 3. Audit Trail
```sql
-- Include metadata in exports
SELECT 
    '2024-01-20' as export_date,
    'jane.smith@company.com' as exported_by,
    'Monthly customer health report' as purpose,
    COUNT(*) as record_count,
    * 
FROM entity.entity_customers
WHERE criteria;
```

## 💡 Common Pitfalls to Avoid

### 1. Time Zone Issues
```sql
-- ❌ Don't assume local time
WHERE created_at >= '2024-01-20'

-- ✅ Be explicit about time zones
WHERE created_at >= '2024-01-20 00:00:00 UTC'
```

### 2. Null Handling
```sql
-- ❌ Nulls in arithmetic
SELECT revenue / users as revenue_per_user  -- Returns NULL if users is 0

-- ✅ Handle nulls explicitly
SELECT revenue / NULLIF(users, 0) as revenue_per_user
```

### 3. Duplicates
```sql
-- ❌ Assuming unique records
SELECT COUNT(*) FROM users

-- ✅ Ensure uniqueness
SELECT COUNT(DISTINCT user_id) FROM users
```

### 4. Date Math
```sql
-- ❌ Simple date subtraction
WHERE date >= CURRENT_DATE - 30  -- Wrong!

-- ✅ Use interval arithmetic
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
```

## 📈 Reporting Standards

### 1. Metric Definitions
- Always use standard metric definitions
- Document any custom calculations
- Include metric source in reports
- Version control metric changes

### 2. Report Structure
```
1. Executive Summary (1 page)
   - Key findings
   - Recommendations
   - Impact assessment

2. Detailed Analysis
   - Methodology
   - Data sources
   - Findings with visuals
   - Statistical significance

3. Appendix
   - Query code
   - Data quality notes
   - Assumptions
   - Limitations
```

### 3. Visualization Standards
- **Colors**: 
  - Good = Green (#28a745)
  - Warning = Yellow (#ffc107)
  - Bad = Red (#dc3545)
  - Neutral = Blue (#007bff)
- **Fonts**: Arial or Helvetica
- **Sizing**: Minimum 10pt
- **Labels**: Always label axes

## 🤝 Collaboration Guidelines

### 1. Code Sharing
```sql
-- Save reusable queries in team repository
-- Path: /queries/team_name/analysis_name.sql
-- Include:
-- - Purpose
-- - Parameters
-- - Example usage
-- - Performance notes
```

### 2. Peer Review
Before publishing analysis:
- [ ] Have a peer review queries
- [ ] Validate business logic
- [ ] Check calculations
- [ ] Verify data sources
- [ ] Test edge cases

### 3. Knowledge Sharing
- Document learnings in team wiki
- Share interesting findings in Slack
- Create reusable query templates
- Mentor junior analysts

## 🚦 Quick Reference

### Do's ✅
- Use entity tables for current state
- Query appropriate time grains
- Filter early in queries
- Document your analysis
- Validate results
- Consider performance

### Don'ts ❌
- Recalculate existing metrics
- Query raw tables directly
- Use SELECT * in production
- Ignore time zones
- Assume data quality
- Share sensitive data

Remember: Good analysis starts with understanding the business question and ends with actionable insights!