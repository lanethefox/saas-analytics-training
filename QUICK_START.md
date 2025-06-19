# Data Platform Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- PostgreSQL access to the analytics database
- Basic SQL knowledge
- Optional: dbt CLI for running transformations

### Step 1: Connect to the Database

```bash
# Using psql
psql -h localhost -U analytics_user -d analytics

# Set search path to entity schema
SET search_path TO entity, public;
```

### Step 2: Run Your First Query

```sql
-- See all your customers with key metrics
SELECT 
    company_name,
    customer_tier,
    monthly_recurring_revenue as mrr,
    customer_health_score,
    churn_risk_score,
    active_users_30d,
    device_events_30d
FROM entity_customers
WHERE customer_status = 'active'
ORDER BY monthly_recurring_revenue DESC
LIMIT 20;
```

### Step 3: Explore Available Entities

We have 7 core entities, each with 3 table types:

| Entity | Atomic Table | History Table | Grain Table |
|--------|--------------|---------------|-------------|
| Customers | entity_customers | entity_customers_history | entity_customers_daily |
| Devices | entity_devices | entity_devices_history | entity_devices_hourly |
| Locations | entity_locations | entity_locations_history | entity_locations_weekly |
| Users | entity_users | entity_users_history | entity_users_weekly |
| Subscriptions | entity_subscriptions | entity_subscriptions_history | entity_subscriptions_monthly |
| Campaigns | entity_campaigns | entity_campaigns_history | entity_campaigns_daily |
| Features | entity_features | entity_features_history | entity_features_monthly |

### Step 4: Try Common Business Queries

#### Find At-Risk Customers
```sql
SELECT company_name, mrr, churn_risk_score, customer_health_score
FROM entity_customers
WHERE churn_risk_score > 60
ORDER BY mrr DESC;
```

#### Identify Device Issues
```sql
SELECT device_name, location_name, overall_health_score, connectivity_status
FROM entity_devices
WHERE requires_immediate_attention = TRUE;
```

#### Analyze User Engagement
```sql
SELECT company_name, 
       active_users_30d::float / NULLIF(total_users, 0) * 100 as adoption_rate
FROM entity_customers
WHERE customer_status = 'active'
ORDER BY adoption_rate DESC;
```

### Step 5: Build Your First Dashboard

Create a simple executive dashboard:

```sql
-- Executive Summary Dashboard
WITH metrics AS (
    SELECT 
        -- Revenue
        SUM(monthly_recurring_revenue) as total_mrr,
        COUNT(*) as total_customers,
        
        -- Health
        AVG(customer_health_score) as avg_health,
        COUNT(CASE WHEN churn_risk_score > 60 THEN 1 END) as at_risk_count,
        
        -- Usage
        SUM(device_events_30d) as total_events,
        SUM(active_users_30d) as total_active_users
        
    FROM entity_customers
    WHERE customer_status = 'active'
)
SELECT 
    ROUND(total_mrr, 0) as "Total MRR",
    total_customers as "Active Customers",
    ROUND(avg_health, 1) as "Avg Health Score",
    at_risk_count as "At-Risk Customers",
    total_events as "Monthly Events",
    total_active_users as "Active Users"
FROM metrics;
```

## 📊 Common Patterns

### Pattern 1: Filtering by Status
Always filter by status first for better performance:
```sql
WHERE customer_status = 'active'  -- Do this first
  AND other_conditions...
```

### Pattern 2: Safe Division
Use NULLIF to avoid division by zero:
```sql
ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as adoption_rate
```

### Pattern 3: Time-Based Analysis
Use grain tables for time series:
```sql
SELECT snapshot_date, SUM(monthly_recurring_revenue) as mrr
FROM entity_customers_daily
WHERE snapshot_date >= CURRENT_DATE - 30
GROUP BY snapshot_date
ORDER BY snapshot_date;
```

## 🎯 Next Steps

1. **Explore Example Queries**: Check `/examples/` directory
2. **Read Full Documentation**: See [Entity Documentation](docs/entity_tables_documentation.md)
3. **Try Learning Modules**: Start with [Module 1](learning_modules/module_1_saas_fundamentals/)
4. **Build Custom Reports**: Use the entity tables to answer your specific questions

## 💡 Pro Tips

- **No Joins Needed**: 90% of questions can be answered with single-table queries
- **Pre-Calculated Metrics**: Health scores, risk scores, and aggregates are ready to use
- **Real-Time Data**: Atomic tables update every 15 minutes
- **Historical Analysis**: Use history tables for trend analysis and attribution

## 🆘 Getting Help

- **Schema Documentation**: Run `\d entity_customers` in psql
- **Column Descriptions**: Check `entity_models.yml` in dbt project
- **Business Logic**: See test files in `/tests/` directory
- **Support**: Create an issue in the project repository

---

Remember: The power of Entity-Centric Modeling is **simplicity**. Start with simple queries and build up!