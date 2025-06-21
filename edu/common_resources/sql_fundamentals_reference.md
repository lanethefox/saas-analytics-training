# SQL Fundamentals Reference Sheet

## Quick Reference Guide

This reference sheet provides essential SQL commands and patterns used throughout the analytics curriculum. Keep this handy as you work through projects and exercises.

## Basic SELECT Statements

### Simple Selection
```sql
-- Select all columns
SELECT * FROM customers;

-- Select specific columns
SELECT customer_id, customer_name, monthly_recurring_revenue
FROM customers;

-- Select with column aliases
SELECT 
    customer_id AS id,
    customer_name AS name,
    monthly_recurring_revenue AS mrr
FROM customers;
```

### Filtering with WHERE
```sql
-- Single condition
SELECT * FROM customers
WHERE customer_status = 'active';

-- Multiple conditions with AND
SELECT * FROM customers
WHERE customer_status = 'active' 
  AND monthly_recurring_revenue > 1000;

-- Multiple conditions with OR
SELECT * FROM customers
WHERE customer_tier = 1 
   OR customer_tier = 2;

-- Using IN for multiple values
SELECT * FROM customers
WHERE customer_tier IN (1, 2, 3);

-- Pattern matching with LIKE
SELECT * FROM customers
WHERE customer_name LIKE 'Acme%';

-- NULL handling
SELECT * FROM customers
WHERE churned_at IS NULL;
```

## Aggregation Functions

### Basic Aggregations
```sql
-- Count records
SELECT COUNT(*) as total_customers
FROM customers;

-- Count distinct values
SELECT COUNT(DISTINCT customer_tier) as tier_count
FROM customers;

-- Sum values
SELECT SUM(monthly_recurring_revenue) as total_mrr
FROM customers
WHERE customer_status = 'active';

-- Average calculation
SELECT AVG(customer_health_score) as avg_health_score
FROM customers;

-- Min and Max
SELECT 
    MIN(created_at) as first_customer,
    MAX(created_at) as latest_customer
FROM customers;
```

### GROUP BY Operations
```sql
-- Group by single column
SELECT 
    customer_tier,
    COUNT(*) as customer_count,
    SUM(monthly_recurring_revenue) as tier_mrr
FROM customers
GROUP BY customer_tier;

-- Group by multiple columns
SELECT 
    customer_status,
    customer_tier,
    COUNT(*) as count
FROM customers
GROUP BY customer_status, customer_tier;

-- GROUP BY with HAVING
SELECT 
    customer_tier,
    COUNT(*) as customer_count
FROM customers
GROUP BY customer_tier
HAVING COUNT(*) > 100;
```

## JOIN Operations

### INNER JOIN
```sql
-- Basic inner join
SELECT 
    c.customer_name,
    s.subscription_status,
    s.monthly_amount
FROM customers c
INNER JOIN subscriptions s ON c.customer_id = s.customer_id;

-- Multiple joins
SELECT 
    c.customer_name,
    l.location_name,
    d.device_serial_number
FROM customers c
INNER JOIN locations l ON c.customer_id = l.customer_id
INNER JOIN devices d ON l.location_id = d.location_id;
```

### LEFT JOIN
```sql
-- Include all customers, even without subscriptions
SELECT 
    c.customer_name,
    COALESCE(s.monthly_amount, 0) as monthly_amount
FROM customers c
LEFT JOIN subscriptions s ON c.customer_id = s.customer_id;
```

### Joining with Aggregations
```sql
-- Customer with total devices
SELECT 
    c.customer_id,
    c.customer_name,
    COUNT(d.device_id) as device_count
FROM customers c
LEFT JOIN locations l ON c.customer_id = l.customer_id
LEFT JOIN devices d ON l.location_id = d.location_id
GROUP BY c.customer_id, c.customer_name;
```

## Date and Time Functions

### Date Extraction
```sql
-- Extract date parts
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as customers_added
FROM customers
GROUP BY DATE_TRUNC('month', created_at);

-- Date arithmetic
SELECT 
    customer_name,
    created_at,
    CURRENT_DATE - created_at::date as days_since_signup
FROM customers;

-- Date filtering
SELECT * FROM customers
WHERE created_at >= '2024-01-01'
  AND created_at < '2024-02-01';

-- Dynamic date ranges
SELECT * FROM customers
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
```

## Window Functions

### Ranking Functions
```sql
-- Row number
SELECT 
    customer_name,
    monthly_recurring_revenue,
    ROW_NUMBER() OVER (ORDER BY monthly_recurring_revenue DESC) as revenue_rank
FROM customers;

-- Rank with ties
SELECT 
    customer_name,
    customer_tier,
    RANK() OVER (ORDER BY customer_tier) as tier_rank
FROM customers;

-- Rank within groups
SELECT 
    customer_tier,
    customer_name,
    monthly_recurring_revenue,
    ROW_NUMBER() OVER (PARTITION BY customer_tier ORDER BY monthly_recurring_revenue DESC) as tier_rank
FROM customers;
```

### Running Calculations
```sql
-- Running total
SELECT 
    created_at::date as signup_date,
    COUNT(*) as daily_signups,
    SUM(COUNT(*)) OVER (ORDER BY created_at::date) as running_total
FROM customers
GROUP BY created_at::date;

-- Moving average
SELECT 
    date,
    daily_revenue,
    AVG(daily_revenue) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as revenue_7day_avg
FROM daily_metrics;
```

## Common Table Expressions (CTEs)

### Basic CTE
```sql
-- Single CTE
WITH active_customers AS (
    SELECT customer_id, customer_name, monthly_recurring_revenue
    FROM customers
    WHERE customer_status = 'active'
)
SELECT 
    customer_tier,
    COUNT(*) as count,
    AVG(monthly_recurring_revenue) as avg_mrr
FROM active_customers
GROUP BY customer_tier;

-- Multiple CTEs
WITH tier_metrics AS (
    SELECT 
        customer_tier,
        COUNT(*) as customer_count,
        SUM(monthly_recurring_revenue) as total_mrr
    FROM customers
    WHERE customer_status = 'active'
    GROUP BY customer_tier
),
tier_percentages AS (
    SELECT 
        customer_tier,
        customer_count,
        total_mrr,
        total_mrr / SUM(total_mrr) OVER () * 100 as mrr_percentage
    FROM tier_metrics
)
SELECT * FROM tier_percentages
ORDER BY customer_tier;
```

## CASE Statements

### Simple CASE
```sql
-- Categorization
SELECT 
    customer_name,
    monthly_recurring_revenue,
    CASE 
        WHEN monthly_recurring_revenue >= 10000 THEN 'Enterprise'
        WHEN monthly_recurring_revenue >= 1000 THEN 'Mid-Market'
        ELSE 'SMB'
    END as customer_segment
FROM customers;

-- Conditional aggregation
SELECT 
    COUNT(CASE WHEN customer_status = 'active' THEN 1 END) as active_count,
    COUNT(CASE WHEN customer_status = 'churned' THEN 1 END) as churned_count,
    COUNT(*) as total_count
FROM customers;
```

## Data Type Conversions

### Common Conversions
```sql
-- String to number
SELECT 
    customer_id,
    CAST(postal_code AS INTEGER) as zip_numeric
FROM locations
WHERE postal_code ~ '^\d+$';

-- Number to string
SELECT 
    customer_id || '-' || location_id as composite_id
FROM locations;

-- Date conversions
SELECT 
    created_at::date as created_date,
    TO_CHAR(created_at, 'YYYY-MM') as created_month,
    EXTRACT(year FROM created_at) as created_year
FROM customers;
```

## Performance Tips

### Indexing Hints
```sql
-- Check if using index (EXPLAIN)
EXPLAIN SELECT * FROM customers WHERE customer_id = 'cus_123';

-- Force index usage with proper WHERE clause
SELECT * FROM customers 
WHERE created_at >= '2024-01-01' 
  AND created_at < '2024-02-01'
  AND customer_status = 'active';
```

### Query Optimization
```sql
-- Use EXISTS instead of IN for large datasets
SELECT * FROM customers c
WHERE EXISTS (
    SELECT 1 FROM subscriptions s 
    WHERE s.customer_id = c.customer_id 
      AND s.status = 'active'
);

-- Limit results during development
SELECT * FROM large_table
LIMIT 100;
```

## Common Patterns for Analytics

### Cohort Analysis
```sql
SELECT 
    DATE_TRUNC('month', c.created_at) as cohort_month,
    DATE_TRUNC('month', a.activity_date) as activity_month,
    COUNT(DISTINCT c.customer_id) as active_customers
FROM customers c
JOIN activities a ON c.customer_id = a.customer_id
GROUP BY 1, 2;
```

### Period-over-Period Comparison
```sql
WITH current_period AS (
    SELECT SUM(revenue) as revenue
    FROM daily_revenue
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
),
previous_period AS (
    SELECT SUM(revenue) as revenue
    FROM daily_revenue
    WHERE date >= CURRENT_DATE - INTERVAL '60 days'
      AND date < CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    c.revenue as current_revenue,
    p.revenue as previous_revenue,
    ((c.revenue - p.revenue) / p.revenue * 100)::numeric(10,2) as growth_rate
FROM current_period c, previous_period p;
```

### Retention Calculation
```sql
SELECT 
    DATE_TRUNC('month', first_order_date) as cohort,
    months_since_first_order,
    COUNT(DISTINCT CASE WHEN made_purchase THEN customer_id END) * 100.0 / 
    COUNT(DISTINCT customer_id) as retention_rate
FROM customer_cohorts
GROUP BY 1, 2;
```

## Debugging Tips

### Check for NULLs
```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(column_name) as non_null_count,
    COUNT(*) - COUNT(column_name) as null_count
FROM table_name;
```

### Validate Joins
```sql
-- Check for join multiplication
SELECT 
    COUNT(*) as row_count,
    COUNT(DISTINCT customer_id) as unique_customers
FROM customers c
JOIN subscriptions s ON c.customer_id = s.customer_id;
```

### Data Quality Checks
```sql
-- Find duplicates
SELECT 
    customer_id,
    COUNT(*) as occurrences
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- Check for outliers
SELECT *
FROM customers
WHERE monthly_recurring_revenue > (
    SELECT AVG(monthly_recurring_revenue) + 3 * STDDEV(monthly_recurring_revenue)
    FROM customers
);
```

## Best Practices

1. **Always use meaningful aliases** for tables and calculated columns
2. **Format queries consistently** with proper indentation
3. **Comment complex logic** to explain business rules
4. **Test with LIMIT** before running on full dataset
5. **Use CTEs** to break complex queries into readable steps
6. **Validate results** with known totals or sample checks
7. **Consider performance** with proper indexing and filtering
8. **Handle NULLs explicitly** with COALESCE or filters

Remember: SQL is a tool for asking questions of your data. Start simple, validate results, and gradually build complexity as needed.