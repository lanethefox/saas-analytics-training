# 📊 Superset Dashboard Setup Guide

## Overview
Your Superset instance is now connected to the PostgreSQL database with all the entity and mart layer tables. This guide will walk you through creating datasets and building domain-specific dashboards.

## 🔗 Access Information
- **URL**: http://localhost:8088
- **Username**: admin
- **Password**: admin_password_2024
- **Database**: SaaS Platform Analytics (ID: 3)

## 📦 Step 1: Create Datasets

### Manual Dataset Creation Process:
1. Navigate to **Data → Datasets**
2. Click **+ Dataset** button
3. Select:
   - **Database**: SaaS Platform Analytics
   - **Schema**: Choose schema (entity or mart)
   - **Table**: Select table name
4. Click **Add**

### Priority Datasets to Create:

#### Entity Layer (Core Business Entities):
| Schema | Table | Description |
|--------|-------|-------------|
| entity | entity_customers | Customer master with health scores and MRR |
| entity | entity_devices | IoT devices with performance metrics |
| entity | entity_users | User profiles with engagement scores |
| entity | entity_subscriptions | Subscription lifecycle and revenue |
| entity | entity_locations | Location operational metrics |
| entity | entity_campaigns | Marketing campaign performance |
| entity | entity_features | Product feature adoption |
| entity | entity_customers_daily | Daily customer snapshots |
| entity | entity_devices_hourly | Hourly device metrics |
| entity | entity_users_weekly | Weekly user rollups |

#### Mart Layer (Domain Analytics):
| Schema | Table | Description |
|--------|-------|-------------|
| mart | mart_customer_success__health | Customer health analysis |
| mart | mart_sales__pipeline | Sales pipeline metrics |
| mart | mart_marketing__attribution | Marketing attribution |
| mart | mart_product__adoption | Product usage analytics |
| mart | mart_operations__performance | Operational KPIs |

## 📈 Step 2: Create Charts

### Chart Creation Process:
1. Navigate to **Charts → + Chart**
2. Select a dataset
3. Choose visualization type
4. Configure metrics and dimensions
5. Save chart

### Recommended Charts by Domain:

#### 🎯 Customer Success Dashboard
1. **Customer Health Distribution** (Pie Chart)
   - Dataset: `entity_customers`
   - Dimension: `customer_health_tier`
   - Metric: COUNT(DISTINCT account_id)

2. **MRR by Health Tier** (Bar Chart)
   - Dataset: `entity_customers`
   - Dimension: `customer_health_tier`
   - Metric: SUM(monthly_recurring_revenue)

3. **Churn Risk Heatmap** (Heatmap)
   - Dataset: `entity_customers`
   - X-axis: `industry`
   - Y-axis: `customer_segment`
   - Metric: AVG(churn_risk_score)

4. **Health Score Trend** (Line Chart)
   - Dataset: `entity_customers_daily`
   - Time: `snapshot_date`
   - Dimension: `customer_health_tier`
   - Metric: AVG(avg_health_score)

5. **At-Risk Customers** (Table)
   - Dataset: `entity_customers`
   - Columns: company_name, MRR, churn_risk_score
   - Filter: churn_risk_score > 70
   - Sort: churn_risk_score DESC

#### 💰 Sales Dashboard
1. **Pipeline by Stage** (Funnel)
   - Dataset: `mart_sales__pipeline`
   - Dimension: `pipeline_stage`
   - Metric: SUM(opportunity_value)

2. **Win Rate by Product** (Bar Chart)
   - Dataset: `mart_sales__pipeline`
   - Dimension: `product_category`
   - Metric: SUM(CASE WHEN deal_status='won' THEN 1 ELSE 0 END)*100.0/COUNT(*)

3. **Sales Velocity** (Big Number)
   - Dataset: `mart_sales__pipeline`
   - Metric: AVG(days_in_pipeline)

#### 📈 Marketing Dashboard
1. **Channel Performance** (Sunburst)
   - Dataset: `mart_marketing__attribution`
   - Hierarchy: channel → campaign_type
   - Metric: SUM(attributed_revenue)

2. **CAC by Channel** (Bar Chart)
   - Dataset: `mart_marketing__attribution`
   - Dimension: `channel`
   - Metric: SUM(spend)/COUNT(DISTINCT customer_id)

#### 🚀 Product Dashboard
1. **Feature Adoption** (Funnel)
   - Dataset: `entity_features`
   - Dimension: `adoption_stage`
   - Metric: SUM(unique_users)

2. **User Engagement** (Histogram)
   - Dataset: `entity_users`
   - Column: `engagement_score`
   - Bins: 20

#### ⚙️ Operations Dashboard
1. **Device Status** (Pie Chart)
   - Dataset: `entity_devices`
   - Dimension: `device_status`
   - Metric: COUNT(DISTINCT device_id)

2. **Performance Heatmap** (Calendar Heatmap)
   - Dataset: `entity_devices_hourly`
   - Time: `hour_timestamp`
   - Metric: AVG(avg_response_time)

## 🎨 Step 3: Create Dashboards

### Dashboard Creation Process:
1. Navigate to **Dashboards → + Dashboard**
2. Add title and description
3. Drag charts from the right panel
4. Arrange in grid layout
5. Add markdown tiles for documentation
6. Configure cross-filters
7. Save and publish

### Dashboard Templates:

#### Customer Success Command Center
**Layout**:
```
[Header: Customer Success Metrics]
[Doc: Key Metrics] | [Health Pie] | [MRR Bar]
[Risk Heatmap - Full Width]
[Health Trend] | [At-Risk Table]
```

**Markdown Documentation**:
```markdown
## 🎯 Customer Success KPIs

### Health Score Components:
- Usage Frequency (40%)
- Feature Adoption (20%)
- Support Sentiment (20%)
- Payment History (20%)

### Action Thresholds:
- 🔴 Critical (<60): Immediate intervention
- 🟡 At Risk (60-79): Increase touchpoints
- 🟢 Healthy (80+): Upsell opportunity

### Data Freshness:
- Real-time: Usage events
- Hourly: Health scores
- Daily: Churn predictions
```

## 🔧 Step 4: Configure Features

### Enable Cross-Filtering:
1. Edit dashboard
2. Click gear icon → Settings
3. Enable "Cross-filtering enabled"
4. Save

### Add Filters:
1. Click Filters → + Add/Edit Filters
2. Common filters:
   - Date Range (time columns)
   - Customer Segment
   - Product Type
   - Geographic Region

### Set Refresh Schedule:
1. Dashboard → Settings → Advanced
2. Set refresh frequency (e.g., 300 seconds)
3. Configure auto-refresh

## 📊 Step 5: Advanced Features

### Create Calculated Metrics:
Example SQL expressions for charts:
```sql
-- Net Revenue Retention
SUM(CASE WHEN customer_type='existing' THEN mrr ELSE 0 END) / 
SUM(CASE WHEN customer_type='existing' AND period_lag=1 THEN mrr ELSE 0 END) * 100

-- CAC Payback Period
SUM(customer_acquisition_cost) / 
(SUM(monthly_recurring_revenue) * AVG(gross_margin))

-- Feature Adoption Rate
COUNT(DISTINCT CASE WHEN feature_used THEN user_id END) * 100.0 / 
COUNT(DISTINCT user_id)
```

### Add Annotations:
1. Charts → Select chart → Edit
2. Annotations tab → Add Annotation Layer
3. Configure:
   - Formula annotations for thresholds
   - Event annotations for releases
   - Time series annotations for trends

## 🎯 Quick Start Checklist

- [ ] Create priority datasets (at least 5 from each layer)
- [ ] Build 3-5 charts for your primary domain
- [ ] Create your first dashboard with documentation
- [ ] Enable cross-filtering
- [ ] Add at least one filter
- [ ] Share dashboard with team

## 🆘 Troubleshooting

### Dataset Not Showing Columns:
1. Edit dataset
2. Click "Sync columns from source"
3. Save

### Chart Not Loading:
1. Check dataset permissions
2. Verify column names match
3. Test query in SQL Lab first

### Performance Issues:
1. Create aggregated tables for large datasets
2. Use time filters to limit data
3. Consider materialized views

## 📚 Resources

- **SQL Lab**: Test queries before creating charts
- **Chart Gallery**: Browse visualization types
- **Explore View**: Advanced chart configuration
- **Dashboard Examples**: http://localhost:8088/superset/dashboard/2/

## 🎉 Congratulations!

You now have a fully configured Superset instance with:
- ✅ Database connection to PostgreSQL
- ✅ Access to all entity and mart tables
- ✅ Example dashboard with documentation
- ✅ Guidelines for creating domain dashboards

Start with one domain dashboard and expand from there. The entity-centric model makes it easy to create powerful analytics with simple queries!
