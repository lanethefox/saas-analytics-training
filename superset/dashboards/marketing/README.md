# Marketing Dashboard Setup Guide

## Overview
Track campaign performance, lead generation, attribution, and marketing ROI across all channels.

## Key Components

### 1. Marketing KPIs
- **Total MQLs** - Marketing qualified leads generated
- **Cost per Lead** - Average acquisition cost
- **Campaign ROI** - Return on marketing spend
- **Conversion Rate** - MQL to customer conversion

### 2. Campaign Performance
- **Active Campaigns** - Current running campaigns by channel
- **Campaign Funnel** - Impressions → Clicks → Leads → Customers
- **Channel Attribution** - Multi-touch attribution analysis
- **A/B Test Results** - Campaign variant performance

### 3. Lead Analytics
- **Lead Velocity** - New leads over time
- **Lead Scoring** - Distribution of lead quality scores
- **Source Analysis** - Performance by lead source
- **Geographic Distribution** - Leads by region

### 4. Budget & Spend
- **Budget Utilization** - Actual vs planned spend
- **Channel Efficiency** - Cost per acquisition by channel
- **Monthly Burn Rate** - Marketing spend trends
- **ROI by Campaign Type** - Performance comparison

## Key Datasets
- `public.metrics_marketing` - Aggregated marketing metrics
- `entity.entity_campaigns` - Campaign master data
- `entity.entity_campaigns_daily` - Daily campaign metrics
- `mart.mart_marketing__attribution` - Attribution analysis

## Essential Charts

### 1. Campaign Performance Dashboard
```sql
SELECT 
    campaign_name,
    platform,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(conversions) as conversions,
    SUM(spend) as total_spend,
    ROUND(SUM(clicks)::numeric / NULLIF(SUM(impressions), 0) * 100, 2) as ctr,
    ROUND(SUM(conversions)::numeric / NULLIF(SUM(clicks), 0) * 100, 2) as conversion_rate,
    ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2) as cpa,
    ROUND((SUM(conversion_value) - SUM(spend)) / NULLIF(SUM(spend), 0) * 100, 2) as roi
FROM entity.entity_campaigns
WHERE campaign_status = 'active'
GROUP BY campaign_name, platform
ORDER BY total_spend DESC;
```

### 2. Lead Generation Trend
```sql
SELECT 
    DATE_TRUNC('week', created_at) as week,
    lead_source,
    COUNT(*) as lead_count,
    AVG(mql_score) as avg_score,
    SUM(CASE WHEN became_customer THEN 1 ELSE 0 END) as converted
FROM marketing.marketing_qualified_leads
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY week, lead_source
ORDER BY week DESC;
```

### 3. Attribution Analysis
```sql
SELECT 
    attribution_model,
    channel,
    SUM(attributed_conversions) as conversions,
    SUM(attributed_revenue) as revenue,
    AVG(touchpoints_count) as avg_touchpoints
FROM mart.mart_marketing__attribution
GROUP BY attribution_model, channel
ORDER BY revenue DESC;
```

## Filters to Include
- Date Range selector
- Campaign Platform filter
- Campaign Type dropdown
- Geographic region
- Attribution model selector

## Recommended Layout
```
[MQLs KPI] [CPL KPI] [ROI KPI] [Conversion KPI]
[--------Campaign Performance Table--------]
[--Lead Velocity Chart--] [Channel Mix Pie]
[------Attribution Heatmap------] [Budget Gauge]
```

## Alerts to Configure
1. Campaign overspend (>110% of budget)
2. Low performing campaigns (ROI < 50%)
3. Lead velocity decline (>20% WoW drop)
4. High CPL channels (>$200)