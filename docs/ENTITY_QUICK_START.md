# Entity-Centric Modeling Quick Start Guide

## 🎯 When to Query Which Entity Table

### The Three-Table Pattern
Each entity has three tables optimized for different use cases:

| Table Type | When to Use | Query Speed | Best For |
|------------|-------------|-------------|----------|
| **Atomic** (entity_customers) | Current state analysis | <3 seconds | Dashboards, operational reports, real-time monitoring |
| **History** (entity_customers_history) | Change analysis, auditing | <10 seconds | Trend analysis, attribution, lifecycle tracking |
| **Grain** (entity_customers_daily) | Time-series analysis | <1 second | Executive reports, cohort analysis, forecasting |

### Decision Tree
```
Need current customer status? → entity_customers
Need to track changes over time? → entity_customers_history  
Need daily/weekly/monthly trends? → entity_customers_daily
```

## 📊 Top 10 Most Useful Columns

### entity_customers (Customer 360)
1. **customer_health_score** - Overall health (0-100)
2. **churn_risk_score** - Churn probability (0-100) 
3. **monthly_recurring_revenue** - Current MRR
4. **active_users_30d** - Monthly active users
5. **device_events_30d** - Monthly device activity
6. **days_since_creation** - Customer age
7. **total_devices** - Infrastructure size
8. **last_user_activity** - Engagement recency
9. **customer_tier** - Subscription level (1,2,3)
10. **avg_user_engagement_score** - User satisfaction

### entity_devices (Device Operations)
1. **overall_health_score** - Device health (0-100)
2. **uptime_percentage_30d** - Reliability metric
3. **maintenance_status** - Maintenance needs
4. **connectivity_status** - Online/offline
5. **total_events_30d** - Usage volume
6. **quality_issue_rate_30d** - Error percentage
7. **days_since_maintenance** - Maintenance recency
8. **performance_score** - Performance rating
9. **device_lifecycle_stage** - Age classification
10. **requires_immediate_attention** - Alert flag

### entity_locations (Location Analytics)
1. **operational_health_score** - Location health
2. **total_devices** - Device count
3. **active_devices** - Active device count
4. **tap_events_30d** - Monthly activity
5. **revenue_per_location** - Location revenue
6. **support_tickets_open** - Support burden
7. **quality_issue_rate_30d** - Quality metric
8. **device_connectivity_rate** - Online percentage
9. **active_users** - User count
10. **risk_level** - Risk classification

## 🔍 Common Filter Patterns

### Find At-Risk Customers
```sql
WHERE churn_risk_score > 60 
  OR customer_health_score < 50
  OR device_events_30d = 0
```

### Identify Growth Opportunities
```sql
WHERE customer_health_score > 80
  AND churn_risk_score < 30
  AND customer_tier < 3
```

### Operational Issues
```sql
WHERE operational_health_score < 60
  OR support_tickets_open > 5
  OR device_connectivity_rate < 0.8
```

### High-Value Accounts
```sql
WHERE monthly_recurring_revenue > 5000
  OR total_devices > 50
  OR total_users > 100
```

## ⚡ Performance Tips

### 1. Use Date Filters First
```sql
-- Good: Filter reduces data early
WHERE created_at >= CURRENT_DATE - 30
  AND customer_health_score < 70

-- Bad: Scans all data first
WHERE customer_health_score < 70
  AND created_at >= CURRENT_DATE - 30
```

### 2. Leverage Indexes
Most common filters have indexes:
- customer_tier
- customer_status  
- operational_health_score
- device_status
- location_status

### 3. Avoid Calculated Filters
```sql
-- Good: Use pre-calculated columns
WHERE user_activation_rate_30d < 50

-- Bad: Calculate on the fly
WHERE active_users_30d::numeric / total_users * 100 < 50
```

### 4. Use Appropriate Grain Tables
```sql
-- For trends: Use daily grain (fastest)
SELECT * FROM entity_customers_daily
WHERE snapshot_date >= CURRENT_DATE - 90

-- For current state: Use atomic (most complete)
SELECT * FROM entity_customers
WHERE customer_status = 'active'
```

## 🚀 Quick Examples

### Customer Health Dashboard
```sql
SELECT 
    company_name,
    customer_tier,
    customer_health_score,
    churn_risk_score,
    monthly_recurring_revenue,
    active_users_30d,
    device_events_30d
FROM entity.entity_customers
WHERE customer_status = 'active'
ORDER BY monthly_recurring_revenue DESC;
```

### Location Performance Map
```sql
SELECT 
    location_name,
    city,
    state_code,
    operational_health_score,
    revenue_per_location,
    device_connectivity_rate,
    support_tickets_open
FROM entity.entity_locations
WHERE location_status = 'active'
ORDER BY operational_health_score ASC;
```

### Device Fleet Status
```sql
SELECT 
    device_type,
    COUNT(*) as device_count,
    AVG(overall_health_score) as avg_health,
    AVG(uptime_percentage_30d) as avg_uptime,
    SUM(CASE WHEN requires_immediate_attention THEN 1 ELSE 0 END) as critical_devices
FROM entity.entity_devices
WHERE device_status = 'active'
GROUP BY device_type;
```

## 📚 Learn More

- **Full Documentation**: See `/docs/entity_tables_documentation.md`
- **Example Queries**: See `/examples/` directory
- **Business Scenarios**: See `/examples/02_business_scenarios.sql`
- **Data Model**: See `/dbt_project/models/entity/`

## 💡 Remember

**The power of Entity-Centric Modeling**: Complex business questions answered with simple, single-table queries. No joins required!