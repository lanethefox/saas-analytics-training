# Superset Dashboard Setup Master Guide

## Overview
This guide covers the complete setup process for all departmental dashboards in Apache Superset.

## Prerequisites

### 1. Access Superset
- URL: http://localhost:8088
- Username: `admin`
- Password: `admin_password_2024`

### 2. Verify Database Connection
1. Go to **Data → Databases**
2. Confirm PostgreSQL connection exists
3. Test connection to ensure it's working

### 3. Verify dbt Models
All dbt models should be built and passing:
```bash
docker exec saas_platform_dbt_core bash -c "cd /opt/dbt_project && dbt run --profiles-dir ."
```

## Dashboard Creation Process

### Step 1: Create Datasets

Navigate to **Data → Datasets** and add these core datasets:

#### Universal Datasets (used across multiple dashboards)
- `public.metrics_unified` - Combined metrics
- `public.metrics_company_overview` - Executive rollups
- `entity.entity_customers` - Customer master data
- `entity.entity_customers_daily` - Daily customer metrics

#### Department-Specific Datasets

**Sales:**
- `public.metrics_sales`
- `mart.mart_sales__pipeline`
- `marketing.marketing_qualified_leads`

**Customer Success:**
- `public.metrics_customer_success`
- `entity.entity_users`
- `entity.entity_features`

**Marketing:**
- `public.metrics_marketing`
- `entity.entity_campaigns`
- `entity.entity_campaigns_daily`
- `mart.mart_marketing__attribution`

**Product:**
- `public.metrics_product_analytics`
- `entity.entity_devices`
- `staging.stg_app_database__page_views`

### Step 2: Create Charts

For each dashboard, create charts following this pattern:

1. **KPI Cards** (Big Number viz)
   - Primary metric with comparison
   - Format appropriately ($, %, #)
   - Add sparkline for trend

2. **Trend Charts** (Line/Area viz)
   - Time-series data
   - Multiple metrics on dual axis
   - Relative date ranges

3. **Distribution Charts** (Pie/Donut/Sunburst)
   - Categorical breakdowns
   - Show percentages
   - Limit to top 10 items

4. **Detailed Tables** (Table viz)
   - Sortable columns
   - Conditional formatting
   - Search functionality
   - Export capability

5. **Comparison Charts** (Bar/Column viz)
   - Side-by-side comparisons
   - Grouped or stacked options
   - Clear axis labels

### Step 3: Dashboard Assembly

1. Create new dashboard: **Dashboards → + Dashboard**
2. Name appropriately: "[Department] Performance Dashboard"
3. Arrange charts in logical flow:
   ```
   [KPI 1] [KPI 2] [KPI 3] [KPI 4]
   [-------Main Trend Chart-------]
   [--Table/List--] [--Pie Chart--]
   [----Secondary Analytics----]
   ```

### Step 4: Add Interactivity

#### Filters
1. Add Filter Box chart
2. Common filters:
   - Date Range
   - Department/Team
   - Product/Feature
   - Customer Segment
   - Geographic Region

#### Cross-Filtering
1. Enable in dashboard settings
2. Click on chart elements to filter others
3. Clear filters button

#### Drill-Down
1. Create detail dashboards
2. Link from summary metrics
3. Pass filter context

### Step 5: Configure Refresh & Alerts

#### Auto-Refresh
```json
{
  "refresh_frequency": 300,
  "timed_refresh_immune_slices": []
}
```

#### Email Reports
1. Dashboard → Settings → Email Reports
2. Schedule: Daily/Weekly/Monthly
3. Recipients: Stakeholder list
4. Format: Inline/PDF attachment

#### Alerts
1. Chart → Settings → Alerts
2. Condition: Metric threshold
3. Frequency: Check interval
4. Actions: Email/Slack

## Best Practices

### 1. Performance Optimization
- Use materialized views for complex queries
- Limit time ranges in default views
- Create indexes on filter columns
- Cache frequently accessed data

### 2. Visual Design
- Consistent color scheme across dashboards
- Clear, descriptive titles
- Appropriate chart types for data
- Mobile-responsive layouts

### 3. Data Governance
- Row-level security for sensitive data
- Clear metric definitions
- Data quality indicators
- Last refresh timestamp

### 4. User Experience
- Intuitive navigation
- Help text for complex metrics
- Export capabilities
- Bookmark important views

## Dashboard Inventory

| Dashboard | Purpose | Primary Users | Refresh Rate |
|-----------|---------|---------------|--------------|
| Sales Performance | Pipeline & revenue tracking | Sales team, Leadership | 5 min |
| Customer Success | Health & retention monitoring | CS team, Account Mgmt | 15 min |
| Marketing Analytics | Campaign ROI & attribution | Marketing team | Hourly |
| Product Analytics | Usage & adoption metrics | Product team, Engineering | 30 min |
| Executive Summary | High-level business metrics | C-suite, Board | 15 min |

## Security Configuration

### 1. User Roles
```sql
-- Create role-based access
CREATE ROLE sales_viewer;
CREATE ROLE cs_viewer;
CREATE ROLE marketing_viewer;
CREATE ROLE executive_viewer;

-- Grant appropriate permissions
GRANT SELECT ON mart.mart_sales__pipeline TO sales_viewer;
GRANT SELECT ON entity.entity_customers TO cs_viewer;
-- etc.
```

### 2. Row-Level Security
```python
# In Superset dataset configuration
row_level_security_filters = [
    {
        "clause": "sales_rep = '{{ current_username() }}'",
        "roles": ["sales_viewer"]
    }
]
```

## Maintenance Tasks

### Daily
- Check dashboard load times
- Verify data freshness
- Review error logs

### Weekly
- Update metric calculations
- Clean up unused charts
- Review user feedback

### Monthly
- Performance tuning
- Dashboard usage analytics
- Update documentation

## Troubleshooting

### Common Issues

1. **No Data Showing**
   - Check dataset permissions
   - Verify dbt models ran
   - Confirm time range filters

2. **Slow Performance**
   - Reduce time range
   - Add database indexes
   - Enable caching

3. **Incorrect Calculations**
   - Verify metric definitions
   - Check aggregation levels
   - Confirm join conditions

4. **Access Denied**
   - Check user permissions
   - Verify dataset access
   - Review row-level security

## Next Steps

1. **Training**
   - Schedule team training sessions
   - Create video tutorials
   - Build self-service templates

2. **Expansion**
   - Add predictive analytics
   - Integrate external data
   - Build mobile apps

3. **Automation**
   - Automated insights
   - Anomaly detection
   - Smart alerts

## Support

For assistance:
- Slack: #data-platform
- Email: data-team@company.com
- Wiki: /data-platform/dashboards