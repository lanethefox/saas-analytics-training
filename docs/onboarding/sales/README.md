# Sales Analytics Guide

Welcome to the Sales Analytics guide for the SaaS Analytics Platform. This guide will help you leverage our data platform to drive sales performance, optimize pipeline management, and accelerate revenue growth.

## 🎯 Overview

As a Sales Analyst, you have access to comprehensive sales metrics across the entire customer lifecycle, from lead generation through deal closure and expansion. Our platform provides real-time visibility into:

- Pipeline health and velocity
- Sales team performance
- Lead quality and conversion
- Territory and segment analysis
- Revenue forecasting

## 📊 Key Tables & Metrics

### Primary Sales Tables

1. **`metrics.sales`** - Your main analytics table
   - Pre-calculated sales KPIs updated daily
   - Includes pipeline, performance, and activity metrics
   - Optimized for dashboard queries

2. **`entity.entity_customers`** - Customer master data
   - Current state of all customers
   - Revenue metrics (MRR, ARR, LTV)
   - Customer segmentation fields

3. **`entity.entity_campaigns`** - Marketing attribution
   - Lead source tracking
   - Campaign performance
   - Multi-touch attribution

### Essential Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| `total_pipeline_value` | Sum of all open opportunities | Pipeline coverage |
| `qualified_pipeline_value` | Stage 3+ opportunities | Forecast accuracy |
| `pipeline_coverage_ratio` | Pipeline / Quota | Risk assessment |
| `avg_deal_size` | Average opportunity value | Pricing strategy |
| `avg_sales_cycle_days` | Time from opp to close | Process efficiency |
| `win_rate` | Closed Won / Total Closed | Team effectiveness |
| `deals_won_mtd` | Closed deals this month | Monthly performance |
| `revenue_closed_mtd` | Revenue closed this month | Quota tracking |

## 🚀 Common Reports & Queries

### 1. Sales Performance Dashboard
```sql
-- Monthly sales performance by rep
SELECT 
    sales_rep_name,
    deals_won_mtd,
    revenue_closed_mtd,
    win_rate,
    avg_deal_size,
    quota_attainment,
    calls_made_30d,
    meetings_held_30d
FROM metrics.sales
WHERE date = CURRENT_DATE
ORDER BY revenue_closed_mtd DESC;
```

### 2. Pipeline Health Analysis
```sql
-- Pipeline by stage and age
WITH pipeline_aging AS (
    SELECT 
        opportunity_stage,
        COUNT(DISTINCT opportunity_id) as opp_count,
        SUM(opportunity_value) as total_value,
        AVG(days_in_current_stage) as avg_stage_age,
        AVG(total_age_days) as avg_total_age
    FROM metrics.sales
    WHERE is_open = true
      AND date = CURRENT_DATE
    GROUP BY opportunity_stage
)
SELECT 
    opportunity_stage,
    opp_count,
    total_value,
    ROUND(total_value / SUM(total_value) OVER () * 100, 1) as pct_of_pipeline,
    avg_stage_age,
    avg_total_age,
    CASE 
        WHEN avg_stage_age > 30 THEN 'Stale'
        WHEN avg_stage_age > 14 THEN 'Aging'
        ELSE 'Healthy'
    END as stage_health
FROM pipeline_aging
ORDER BY 
    CASE opportunity_stage
        WHEN 'Prospecting' THEN 1
        WHEN 'Qualification' THEN 2
        WHEN 'Proposal' THEN 3
        WHEN 'Negotiation' THEN 4
        WHEN 'Closing' THEN 5
    END;
```

### 3. Lead Conversion Funnel
```sql
-- Lead to opportunity conversion rates
WITH lead_funnel AS (
    SELECT 
        DATE_TRUNC('month', created_date) as cohort_month,
        COUNT(DISTINCT lead_id) as total_leads,
        COUNT(DISTINCT CASE WHEN became_mql THEN lead_id END) as mqls,
        COUNT(DISTINCT CASE WHEN became_sql THEN lead_id END) as sqls,
        COUNT(DISTINCT CASE WHEN became_opportunity THEN lead_id END) as opportunities,
        COUNT(DISTINCT CASE WHEN became_customer THEN lead_id END) as customers
    FROM metrics.sales
    WHERE created_date >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('month', created_date)
)
SELECT 
    cohort_month,
    total_leads,
    mqls,
    ROUND(100.0 * mqls / NULLIF(total_leads, 0), 1) as lead_to_mql_rate,
    sqls,
    ROUND(100.0 * sqls / NULLIF(mqls, 0), 1) as mql_to_sql_rate,
    opportunities,
    ROUND(100.0 * opportunities / NULLIF(sqls, 0), 1) as sql_to_opp_rate,
    customers,
    ROUND(100.0 * customers / NULLIF(opportunities, 0), 1) as opp_to_customer_rate
FROM lead_funnel
ORDER BY cohort_month DESC;
```

### 4. Territory Performance
```sql
-- Territory analysis with penetration rates
SELECT 
    territory_name,
    territory_region,
    COUNT(DISTINCT customer_id) as customer_count,
    SUM(annual_recurring_revenue) as total_arr,
    AVG(customer_health_score) as avg_health_score,
    COUNT(DISTINCT CASE WHEN customer_tier = 'Enterprise' THEN customer_id END) as enterprise_customers,
    SUM(total_addressable_market) as tam,
    ROUND(100.0 * SUM(annual_recurring_revenue) / NULLIF(SUM(total_addressable_market), 0), 2) as market_penetration
FROM entity.entity_customers c
LEFT JOIN territory_mapping tm ON c.customer_id = tm.customer_id
WHERE c.is_active = true
GROUP BY territory_name, territory_region
ORDER BY total_arr DESC;
```

### 5. Sales Velocity Metrics
```sql
-- Calculate sales velocity components
WITH velocity_metrics AS (
    SELECT 
        DATE_TRUNC('month', close_date) as month,
        COUNT(DISTINCT opportunity_id) as opportunities,
        AVG(opportunity_value) as avg_deal_value,
        AVG(win_rate) as avg_win_rate,
        AVG(sales_cycle_days) as avg_cycle_length
    FROM metrics.sales
    WHERE close_date >= CURRENT_DATE - INTERVAL '12 months'
      AND is_closed = true
    GROUP BY DATE_TRUNC('month', close_date)
)
SELECT 
    month,
    opportunities,
    avg_deal_value,
    avg_win_rate,
    avg_cycle_length,
    -- Sales Velocity = (Opportunities × Deal Value × Win Rate) / Cycle Length
    ROUND((opportunities * avg_deal_value * avg_win_rate / 100) / NULLIF(avg_cycle_length, 0), 0) as sales_velocity
FROM velocity_metrics
ORDER BY month DESC;
```

## 📈 Advanced Analytics

### Predictive Deal Scoring
```sql
-- Score open opportunities based on historical patterns
WITH deal_features AS (
    SELECT 
        s.opportunity_id,
        s.opportunity_name,
        s.opportunity_value,
        s.days_since_last_activity,
        s.total_activities,
        s.days_in_current_stage,
        c.customer_health_score,
        c.product_adoption_score,
        CASE 
            WHEN s.days_since_last_activity > 14 THEN -20
            WHEN s.days_since_last_activity > 7 THEN -10
            ELSE 0
        END as activity_score,
        CASE 
            WHEN s.days_in_current_stage > 30 THEN -15
            WHEN s.days_in_current_stage > 14 THEN -5
            ELSE 5
        END as velocity_score,
        CASE 
            WHEN c.customer_health_score > 80 THEN 20
            WHEN c.customer_health_score > 60 THEN 10
            ELSE -10
        END as health_score
    FROM metrics.sales s
    LEFT JOIN entity.entity_customers c ON s.customer_id = c.customer_id
    WHERE s.is_open = true
      AND s.date = CURRENT_DATE
)
SELECT 
    opportunity_id,
    opportunity_name,
    opportunity_value,
    days_since_last_activity,
    days_in_current_stage,
    -- Composite deal score
    50 + activity_score + velocity_score + health_score as deal_score,
    CASE 
        WHEN 50 + activity_score + velocity_score + health_score >= 70 THEN 'Hot'
        WHEN 50 + activity_score + velocity_score + health_score >= 50 THEN 'Warm'
        ELSE 'At Risk'
    END as deal_temperature
FROM deal_features
ORDER BY deal_score DESC;
```

### Sales Rep Productivity Analysis
```sql
-- Analyze rep productivity and efficiency
WITH rep_metrics AS (
    SELECT 
        sales_rep_name,
        COUNT(DISTINCT CASE WHEN is_closed_won THEN opportunity_id END) as deals_won,
        SUM(CASE WHEN is_closed_won THEN opportunity_value END) as revenue_closed,
        AVG(CASE WHEN is_closed THEN sales_cycle_days END) as avg_cycle_time,
        SUM(calls_made_30d + emails_sent_30d + meetings_held_30d) as total_activities,
        COUNT(DISTINCT opportunity_id) as total_opportunities
    FROM metrics.sales
    WHERE date = CURRENT_DATE
    GROUP BY sales_rep_name
)
SELECT 
    sales_rep_name,
    deals_won,
    revenue_closed,
    avg_cycle_time,
    total_activities,
    ROUND(revenue_closed / NULLIF(deals_won, 0), 0) as avg_deal_size,
    ROUND(total_activities::NUMERIC / NULLIF(deals_won, 0), 1) as activities_per_deal,
    ROUND(deals_won::NUMERIC / NULLIF(total_opportunities, 0) * 100, 1) as personal_win_rate
FROM rep_metrics
WHERE deals_won > 0
ORDER BY revenue_closed DESC;
```

## 🎯 Best Practices

### 1. **Use Pre-Calculated Metrics**
Always start with `metrics.sales` table for standard KPIs. Only join to raw tables when you need additional detail.

### 2. **Time Period Consistency**
- Use `date = CURRENT_DATE` for point-in-time metrics
- Use date ranges for trend analysis
- Be consistent with fiscal calendar if applicable

### 3. **Segmentation Strategy**
Common segments to analyze:
- Customer tier (SMB, Mid-Market, Enterprise)
- Industry vertical
- Geographic region
- Product line
- Lead source

### 4. **Performance Benchmarking**
Compare metrics against:
- Historical performance (YoY, QoQ, MoM)
- Team/peer averages
- Industry benchmarks
- Company targets

## 🔗 Integration Points

### CRM Data (HubSpot)
- Companies → `entity.entity_customers`
- Contacts → Lead and contact analysis
- Deals → Pipeline and opportunity metrics
- Activities → Sales activity tracking

### Billing Data (Stripe)
- Subscriptions → Revenue metrics
- Invoices → Payment and collection analysis
- Customers → Billing relationship mapping

### Product Usage
- Feature adoption → Deal scoring
- User engagement → Expansion opportunities
- Device metrics → Customer success indicators

## 📚 Additional Resources

- [Metrics Catalog](../common/metrics-catalog.md) - Complete list of available metrics
- [Query Patterns](../common/query-patterns.md) - Reusable SQL patterns
- [Data Dictionary](../common/data-dictionary.md) - Field definitions
- [Sales Dashboards](./dashboards.md) - Pre-built Superset dashboards
- [Quarterly Goals](./quarterly-goals.md) - 2025 SMART goals and roadmap

## 🚦 Getting Started Checklist

- [ ] Set up database access credentials
- [ ] Run your first query from this guide
- [ ] Explore the `metrics.sales` table
- [ ] Create a simple pipeline report
- [ ] Join #sales-analytics Slack channel
- [ ] Schedule 1:1 with Sales Operations lead

Welcome to the Sales Analytics team! 🎉