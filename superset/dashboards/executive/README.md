# Executive Summary Dashboard Setup Guide

## Overview
High-level business metrics and KPIs for C-suite and board reporting, combining data from all departments.

## Key Components

### 1. Business Health Score
- **Overall Health Score** - Weighted combination of all metrics
- **Revenue Growth** - MoM and YoY growth rates
- **Customer Metrics** - Count, NPS, retention
- **Operational Efficiency** - Key ratios and metrics

### 2. Financial Performance
- **MRR/ARR** - Current and projected
- **Cash Burn Rate** - Monthly operating expenses
- **Runway** - Months of cash remaining
- **Unit Economics** - CAC, LTV, LTV:CAC ratio

### 3. Growth Metrics
- **Customer Growth** - New, expansion, churn
- **Revenue Growth** - By segment and product
- **Market Penetration** - TAM coverage
- **Geographic Expansion** - Revenue by region

### 4. Leading Indicators
- **Pipeline Coverage** - Next quarter pipeline vs target
- **Product Usage** - Engagement trends
- **Customer Health** - At-risk revenue
- **Employee Metrics** - Headcount, productivity

## Key Datasets
- `public.metrics_unified` - Combined metrics from all domains
- `public.metrics_company_overview` - Executive-level rollups
- All domain-specific metric tables

## Essential Visualizations

### 1. Company Scorecard
```sql
SELECT 
    -- Financial
    total_mrr,
    ROUND((total_mrr - LAG(total_mrr) OVER (ORDER BY metric_date)) / 
          NULLIF(LAG(total_mrr) OVER (ORDER BY metric_date), 0) * 100, 1) as mrr_growth_pct,
    
    -- Customers
    active_customers,
    ROUND(avg_customer_health, 0) as health_score,
    
    -- Sales
    pipeline_value,
    ROUND(pipeline_value / (total_mrr * 3), 1) as pipeline_coverage_ratio,
    
    -- Product
    dau,
    ROUND(dau::numeric / mau * 100, 1) as stickiness_pct,
    
    -- Operations
    device_availability_pct,
    
    -- Marketing
    total_mqls,
    
    metric_date
FROM public.metrics_unified
WHERE metric_date = CURRENT_DATE;
```

### 2. Revenue Waterfall
```sql
WITH revenue_components AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(new_mrr) as new_revenue,
        SUM(expansion_revenue) as expansion,
        SUM(contraction_revenue) as contraction,
        SUM(churned_revenue) as churn
    FROM entity.entity_customers_daily
    WHERE date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '6 months')
    GROUP BY DATE_TRUNC('month', date)
)
SELECT 
    month,
    new_revenue,
    expansion,
    -contraction as contraction,
    -churn as churn,
    new_revenue + expansion - contraction - churn as net_change
FROM revenue_components
ORDER BY month;
```

### 3. Business Metrics Trend
```sql
SELECT 
    display_value,
    metric_name,
    metric_category,
    current_value,
    CASE 
        WHEN metric_name LIKE '%Growth%' THEN 'Higher is Better'
        WHEN metric_name LIKE '%Churn%' THEN 'Lower is Better'
        WHEN metric_name LIKE '%Cost%' THEN 'Lower is Better'
        ELSE 'Higher is Better'
    END as direction
FROM public.metrics_company_overview
WHERE metric_category IN ('revenue', 'customers', 'operations')
ORDER BY 
    CASE metric_category
        WHEN 'revenue' THEN 1
        WHEN 'customers' THEN 2
        WHEN 'operations' THEN 3
        ELSE 4
    END;
```

### 4. Strategic Initiatives Tracker
```sql
-- Custom table for tracking OKRs and initiatives
SELECT 
    initiative_name,
    owner,
    target_date,
    current_progress,
    target_value,
    ROUND(current_progress::numeric / target_value * 100, 0) as completion_pct,
    CASE 
        WHEN current_progress >= target_value THEN 'Complete'
        WHEN target_date < CURRENT_DATE THEN 'Overdue'
        WHEN current_progress::numeric / target_value > 0.7 THEN 'On Track'
        ELSE 'At Risk'
    END as status
FROM strategic_initiatives
WHERE is_active = true
ORDER BY target_date;
```

## Recommended Layout
```
[MRR KPI] [Customers KPI] [NPS KPI] [Health Score KPI]
[-----------Revenue Waterfall Chart-------------]
[--Growth Metrics--] [--Pipeline Coverage Gauge--]
[-------Business Metrics Table-------] 
[--Geographic Map--] [--Initiatives Tracker--]
```

## Executive-Specific Features

### 1. Drill-Down Capability
- Click any metric to see departmental breakdown
- Time-based comparisons (MoM, QoQ, YoY)
- Cohort analysis for key metrics

### 2. Forecasting
- Revenue projections based on pipeline
- Customer growth projections
- Cash runway calculations

### 3. Benchmarking
- Industry comparison metrics
- Growth rate percentiles
- Efficiency ratios vs peers

### 4. Board Package Export
- PDF export with commentary
- Scheduled monthly reports
- Variance analysis included

## Alerts for Executives
1. MRR growth below plan (threshold: 10%)
2. Customer health score decline (>5 points)
3. Cash runway below 12 months
4. Major customer churn risk (>$50k MRR)

## Mobile Optimization
- Responsive design for tablets
- Key metrics summary view
- Swipe between metric categories
- Push notifications for alerts