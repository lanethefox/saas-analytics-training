# Sales Dashboard Setup Guide

## Overview
This guide will help you create a comprehensive Sales dashboard in Apache Superset.

## Prerequisites
1. Apache Superset is running at http://localhost:8088
2. PostgreSQL database is connected in Superset
3. dbt models have been successfully built

## Dashboard Components

### 1. Key Performance Indicators (KPIs)
- **Total Revenue** - Year-to-date closed revenue
- **Pipeline Value** - Total value of open opportunities  
- **Win Rate** - Percentage of won vs lost deals
- **Average Deal Size** - Average value of closed won deals

### 2. Sales Funnel
- Visual funnel showing deal progression through stages
- Deal count and value by stage
- Conversion rates between stages

### 3. Revenue Trends
- Daily/Weekly/Monthly revenue trends
- New vs Expansion vs Churned revenue
- Year-over-year comparisons

### 4. Sales Team Performance
- Leaderboard by revenue closed
- Individual rep metrics and quotas
- Average sales cycle by rep

### 5. Deal Analytics
- Top 10 open opportunities
- Deal aging analysis
- Stalled deal alerts
- Deal velocity metrics

### 6. Lead Source Analysis
- Lead volume by source
- Conversion rates by source
- ROI by marketing channel

## Setup Instructions

### Step 1: Access Superset
1. Navigate to http://localhost:8088
2. Login with credentials:
   - Username: `admin`
   - Password: `admin_password_2024`

### Step 2: Create Datasets
1. Go to **Data → Datasets**
2. Click **+ Dataset** and add the following:

#### Core Datasets:
- `public.metrics_sales` - Pre-aggregated sales metrics
- `mart.mart_sales__pipeline` - Detailed pipeline data
- `entity.entity_customers_daily` - Daily customer metrics
- `marketing.marketing_qualified_leads` - Lead data

### Step 3: Create Charts

#### A. Revenue KPI
1. Click **+ Chart**
2. Select dataset: `public.metrics_sales`
3. Choose visualization: **Big Number with Trendline**
4. Configure:
   - Metric: `SUM(total_revenue)`
   - Time Column: `metric_date`
   - Time Range: Year to Date
   - Format: $,.0f

#### B. Pipeline Funnel
1. Create new chart with `mart.mart_sales__pipeline`
2. Visualization: **Funnel Chart**
3. Configure:
   - Group by: `stage_name`
   - Metric: `SUM(amount)`
   - Sort by: Stage order

#### C. Revenue Trend Line
1. Dataset: `entity.entity_customers_daily`
2. Visualization: **Line Chart**
3. Configure:
   - Time Column: `date`
   - Metrics: 
     - `SUM(new_mrr)` as "New Revenue"
     - `SUM(expansion_revenue)` as "Expansion"
   - Time Grain: Day
   - Time Range: Last 30 days

#### D. Sales Leaderboard
1. Dataset: `mart.mart_sales__pipeline`
2. Visualization: **Bar Chart**
3. Configure:
   - Dimension: `owner_name`
   - Metric: `SUM(amount)` where `stage_name = 'Closed Won'`
   - Sort: Descending by metric
   - Limit: Top 10

#### E. Top Deals Table
1. Dataset: `mart.mart_sales__pipeline`
2. Visualization: **Table**
3. Configure:
   - Columns: `deal_name`, `company_name`, `amount`, `stage_name`, `close_date`
   - Filters: `stage_name NOT IN ('Closed Won', 'Closed Lost')`
   - Order by: `amount DESC`
   - Row Limit: 10

### Step 4: Create Dashboard
1. Go to **Dashboards → + Dashboard**
2. Name: "Sales Performance Dashboard"
3. Drag and drop charts into layout:
   ```
   [Revenue KPI] [Pipeline KPI] [Win Rate] [Avg Deal Size]
   [------------Pipeline Funnel------------] [Revenue Trend]
   [----------Top Deals Table-------------] [--Leaderboard--]
   ```

### Step 5: Add Filters
1. Click **Edit Dashboard**
2. Add Filter Box with:
   - Date Range picker
   - Sales Rep selector
   - Deal Stage filter
   - Region filter (if applicable)

### Step 6: Configure Auto-Refresh
1. Dashboard Settings → JSON Metadata
2. Add: `{"refresh_frequency": 300}` (5-minute refresh)

## SQL Queries Reference

See `sales_queries.sql` for all the queries used in this dashboard.

## Custom Styling

To apply custom colors:
1. Edit Dashboard → CSS
2. Add the provided CSS from `sales_dashboard.json`

## Best Practices

1. **Performance**: Use pre-aggregated metrics tables where possible
2. **Filters**: Apply dashboard-level filters for consistency
3. **Time Ranges**: Use relative time ranges for automatic updates
4. **Permissions**: Set row-level security for sales rep data

## Troubleshooting

### Common Issues:
1. **No data showing**: Check that dbt models have run successfully
2. **Slow performance**: Create indexes on commonly filtered columns
3. **Access errors**: Verify database permissions for Superset user

## Next Steps

After creating the Sales dashboard:
1. Schedule email reports for leadership
2. Create mobile-optimized version
3. Set up alerts for key metrics
4. Train sales team on self-service analytics