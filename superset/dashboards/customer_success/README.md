# Customer Success Dashboard Setup Guide

## Overview
The Customer Success dashboard provides comprehensive insights into customer health, retention, and engagement metrics to proactively manage customer relationships.

## Dashboard Components

### 1. Key Performance Indicators (KPIs)
- **Total Active Customers** - Current count of active accounts
- **Average Health Score** - Overall customer health (0-100)
- **Monthly Churn Rate** - Percentage of customers lost per month
- **Net Promoter Score** - Customer satisfaction metric

### 2. Customer Health Monitoring
- **Health Distribution** - Pie chart showing customers by health category
- **At-Risk Accounts** - Table of customers requiring immediate attention
- **Churn Risk Factors** - Analysis of behaviors correlating with churn

### 3. Revenue & Retention
- **MRR Trends** - Monthly recurring revenue over time
- **Retention Cohorts** - Customer retention by signup cohort
- **Expansion Revenue** - Upsell and cross-sell performance

### 4. Product Usage Analytics
- **User Activity Trends** - Daily/weekly active users
- **Feature Adoption** - Most and least used features
- **Engagement Patterns** - Login frequency and session duration

### 5. Support Metrics
- **Ticket Volume** - Support requests by customer tier
- **Resolution Time** - Average time to resolve issues
- **Customer Satisfaction** - CSAT scores by segment

## Setup Instructions

### Step 1: Create Datasets in Superset

Add the following datasets:
1. `public.metrics_customer_success` - Aggregated CX metrics
2. `entity.entity_customers` - Customer master data with health scores
3. `entity.entity_customers_daily` - Daily customer metrics
4. `entity.entity_users` - User engagement data
5. `entity.entity_features` - Feature adoption metrics

### Step 2: Create Visualizations

#### A. Health Score Gauge
- **Type**: Gauge Chart
- **Dataset**: `metrics_customer_success`
- **Metric**: `avg_health_score`
- **Ranges**: 
  - 0-40: Red (Critical)
  - 40-70: Yellow (At Risk)
  - 70-100: Green (Healthy)

#### B. At-Risk Accounts Table
- **Type**: Table
- **Dataset**: `entity_customers`
- **Columns**: 
  - `customer_name`
  - `health_score` (with color coding)
  - `churn_risk_score`
  - `customer_mrr`
  - `last_login_days_ago`
- **Filter**: `health_score < 40 OR churn_risk_score > 70`
- **Sort**: By `churn_risk_score DESC`

#### C. MRR & Retention Chart
- **Type**: Mixed Time-Series (dual Y-axis)
- **Dataset**: `entity_customers_daily`
- **Primary Metric**: `SUM(total_mrr)`
- **Secondary Metric**: `AVG(retention_rate)`
- **Time Range**: Last 90 days

#### D. Customer Segments Sunburst
- **Type**: Sunburst Chart
- **Dataset**: `entity_customers`
- **Hierarchy**: `customer_tier` → `industry` → `health_category`
- **Metric**: `SUM(customer_mrr)`

#### E. Usage Heatmap
- **Type**: Calendar Heatmap
- **Dataset**: `entity_customers_daily`
- **Metric**: `SUM(active_users)`
- **Time Range**: Last 90 days

### Step 3: Configure Filters

Add dashboard filters for:
- **Date Range** - For trend analysis
- **Customer Tier** - Enterprise/Mid-Market/SMB
- **Health Category** - Healthy/At Risk/Critical
- **CSM Owner** - Filter by customer success manager
- **Industry** - Vertical-specific views

### Step 4: Set Up Alerts

Configure alerts for:
1. **Health Score Drop**: Alert when customer health < 40
2. **High Churn Risk**: Alert when churn risk > 80%
3. **No Login**: Alert when customer hasn't logged in for 14+ days
4. **Support Escalation**: Alert on unresolved critical tickets

### Step 5: Create Drill-Down Dashboards

#### Customer Detail View
When clicking on a customer, show:
- Complete health history
- User activity details
- Support ticket history
- Feature usage breakdown
- Revenue timeline

## Best Practices

### 1. Data Freshness
- Refresh health scores every 4 hours
- Update usage metrics daily
- Recalculate churn risk weekly

### 2. Actionable Insights
- Include recommended actions for at-risk accounts
- Link to CRM records for context
- Provide playbooks for common scenarios

### 3. Segmentation
- Create tier-specific views (Enterprise vs SMB)
- Industry-specific benchmarks
- Lifecycle stage groupings

### 4. Collaboration Features
- Enable comments on at-risk accounts
- Share dashboard with sales team
- Export reports for QBRs

## Metrics Definitions

### Health Score Components
- **Product Usage** (40%): Login frequency, feature adoption
- **Support** (20%): Ticket volume, satisfaction scores  
- **Commercial** (20%): Payment history, contract status
- **Engagement** (20%): NPS, community participation

### Churn Risk Calculation
- Predictive model using:
  - Days since last login
  - Declining usage trends
  - Support ticket sentiment
  - Contract renewal proximity
  - Payment delays

## SQL Query Examples

See `cx_queries.sql` for all queries used in this dashboard.

## Automation

### Scheduled Reports
1. **Daily**: At-risk account summary to CSM team
2. **Weekly**: Health score changes report
3. **Monthly**: Executive retention summary

### Workflow Integration
- Sync at-risk accounts to CRM
- Create Jira tickets for intervention
- Trigger email campaigns for re-engagement

## Troubleshooting

### Common Issues
1. **Missing Health Scores**: Check that ML models are running
2. **Stale Data**: Verify ETL pipeline schedule
3. **Performance**: Add indexes on customer_id, date columns

## Next Steps

1. Implement predictive churn model
2. Add customer journey visualization
3. Create mobile app for CSM team
4. Build customer-facing health dashboard