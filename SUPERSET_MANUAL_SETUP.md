# 📋 Superset Manual Setup Guide

Since automated setup has limitations, here's a comprehensive guide to manually set up your dashboards.

## Step 1: Create Datasets (5 minutes)

1. Go to http://localhost:8088
2. Login with `admin` / `admin_password_2024`
3. Navigate to **Data → Datasets**
4. Click **+ Dataset**

For each table below:
- Database: **SaaS Platform Analytics**
- Schema: Select as specified
- Table: Select table name
- Click **Add**

### Priority Tables:

#### Customer Success
- `entity.entity_customers`
- `entity.entity_customers_daily`
- `entity.entity_customers_history`

#### Operations
- `entity.entity_devices`
- `entity.entity_devices_hourly`
- `entity.entity_locations`

#### Sales & Marketing
- `mart.mart_sales__pipeline`
- `mart.mart_marketing__attribution`

## Step 2: Create Your First Chart (3 minutes)

1. Go to **Charts → + Chart**
2. Select dataset: `entity_customers`
3. Choose visualization: **Pie Chart**
4. Configure:
   - Dimension: `customer_health_tier`
   - Metric: COUNT(*)
5. Click **Save**
   - Name: "Customer Health Distribution"

## Step 3: Create Your First Dashboard (2 minutes)

1. Go to **Dashboards → + Dashboard**
2. Title: "Customer Success Overview"
3. Drag your chart from the right panel
4. Add a Markdown tile:
   ```
   ## Customer Health Metrics
   Monitor customer health distribution and identify at-risk accounts.
   ```
5. Save and publish

## 🎯 Chart Templates

Copy these configurations for quick chart creation:

### Customer Health Score Gauge
- Dataset: `entity_customers`
- Viz Type: Big Number
- Metric: AVG(customer_health_score)
- Comparison: Previous period

### MRR Trend Line
- Dataset: `entity_customers_daily`
- Viz Type: Line Chart
- Time: `snapshot_date`
- Metric: SUM(total_mrr)
- Group by: `customer_segment`

### Device Status Sunburst
- Dataset: `entity_devices`
- Viz Type: Sunburst
- Hierarchy: `device_status` → `device_type`
- Metric: COUNT(*)

## 🔥 Pro Tips

1. **Use Grain Tables for Performance**
   - Daily/Weekly/Monthly aggregations are pre-calculated
   - Much faster than querying raw data

2. **Enable Cross-Filtering**
   - Dashboard Settings → Enable cross filters
   - Click any chart element to filter all charts

3. **SQL Lab for Complex Queries**
   - Test queries before creating charts
   - Save queries as virtual datasets

## 📊 Sample SQL Queries

```sql
-- Customer Health Overview
SELECT 
    customer_health_tier,
    COUNT(*) as customer_count,
    SUM(monthly_recurring_revenue) as total_mrr,
    AVG(customer_health_score) as avg_health_score
FROM entity.entity_customers
GROUP BY customer_health_tier
ORDER BY avg_health_score DESC;

-- Device Performance Summary
SELECT 
    DATE_TRUNC('hour', hour_timestamp) as hour,
    AVG(avg_response_time) as avg_response_time,
    SUM(total_events) as event_volume
FROM entity.entity_devices_hourly
WHERE hour_timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;
```

## 🚀 You're Ready!

With these steps, you can create powerful dashboards in minutes. The entity-centric model makes it easy to join data and create insights without complex SQL.

Start with one domain and expand from there. Each entity table has everything you need for that business domain!
