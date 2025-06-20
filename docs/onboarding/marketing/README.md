# Marketing Analytics Guide

Welcome to the Marketing Analytics guide for the SaaS Analytics Platform. This guide will help you measure campaign effectiveness, optimize marketing spend, track attribution, and drive pipeline generation.

## 🎯 Overview

As a Marketing Analyst, you have access to comprehensive marketing metrics across all channels and campaigns. Our platform provides insights into:

- Multi-channel campaign ROI
- Lead generation and quality
- Attribution modeling
- Marketing spend optimization
- Website and content performance
- Email marketing effectiveness

## 📊 Key Tables & Metrics

### Primary Marketing Tables

1. **`metrics.marketing`** - Your main analytics table
   - Campaign performance metrics
   - Channel-specific ROI
   - Lead generation KPIs
   - Attribution metrics
   - Updated daily

2. **`entity.entity_campaigns`** - Campaign master data
   - Campaign details and taxonomy
   - Performance metrics
   - Attribution data
   - Cost and conversion tracking

3. **`marketing_qualified_leads`** - MQL tracking
   - Lead source attribution
   - Quality scoring
   - Conversion tracking
   - Demographic data

4. **`attribution_touchpoints`** - Multi-touch attribution
   - Customer journey mapping
   - Channel interactions
   - Conversion paths
   - Attribution modeling

### Essential Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| `overall_roi` | Blended marketing ROI | Overall effectiveness |
| `cost_per_acquisition` | Blended CPA | Efficiency tracking |
| `total_mqls` | Marketing qualified leads | Volume tracking |
| `mql_conversion_rate` | MQL → SQL conversion | Lead quality |
| `cost_per_mql` | Cost per qualified lead | Efficiency metric |
| `facebook_roi` | Facebook ads ROI | Channel performance |
| `google_roi` | Google ads ROI | Channel performance |
| `linkedin_roi` | LinkedIn ads ROI | Channel performance |
| `website_conversion_rate` | Site visitor → lead | Website effectiveness |
| `email_open_rate` | Email engagement | Content effectiveness |

## 🚀 Common Reports & Queries

### 1. Marketing Performance Dashboard
```sql
-- Overall marketing performance summary
WITH performance_summary AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(total_ad_spend_active) as total_spend,
        SUM(total_mqls) as total_mqls,
        SUM(total_customers_attributed) as new_customers,
        SUM(total_revenue_attributed) as attributed_revenue,
        AVG(overall_roi) as avg_roi,
        AVG(cost_per_mql) as avg_cost_per_mql,
        AVG(mql_conversion_rate) as avg_mql_conversion
    FROM metrics.marketing
    WHERE date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', date)
)
SELECT 
    month,
    total_spend,
    total_mqls,
    new_customers,
    attributed_revenue,
    ROUND(avg_roi, 2) as roi,
    ROUND(attributed_revenue / NULLIF(total_spend, 0), 2) as roas,
    ROUND(avg_cost_per_mql, 2) as cost_per_mql,
    ROUND(avg_mql_conversion * 100, 1) as mql_conversion_rate,
    ROUND(total_spend / NULLIF(new_customers, 0), 2) as cac
FROM performance_summary
ORDER BY month DESC;
```

### 2. Channel Performance Analysis
```sql
-- Channel-by-channel performance comparison
WITH channel_metrics AS (
    SELECT 
        'Facebook' as channel,
        SUM(facebook_spend) as spend,
        SUM(facebook_mqls) as mqls,
        SUM(facebook_customers) as customers,
        SUM(facebook_revenue) as revenue,
        AVG(facebook_roi) as roi
    FROM metrics.marketing
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'Google' as channel,
        SUM(google_spend) as spend,
        SUM(google_mqls) as mqls,
        SUM(google_customers) as customers,
        SUM(google_revenue) as revenue,
        AVG(google_roi) as roi
    FROM metrics.marketing
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'LinkedIn' as channel,
        SUM(linkedin_spend) as spend,
        SUM(linkedin_mqls) as mqls,
        SUM(linkedin_customers) as customers,
        SUM(linkedin_revenue) as revenue,
        AVG(linkedin_roi) as roi
    FROM metrics.marketing
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'Email' as channel,
        SUM(email_spend) as spend,
        SUM(email_mqls) as mqls,
        SUM(email_customers) as customers,
        SUM(email_revenue) as revenue,
        AVG(email_roi) as roi
    FROM metrics.marketing
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    channel,
    spend,
    mqls,
    ROUND(spend / NULLIF(mqls, 0), 2) as cost_per_mql,
    customers,
    ROUND(spend / NULLIF(customers, 0), 2) as cac,
    revenue,
    ROUND(roi, 2) as roi,
    ROUND(revenue / NULLIF(spend, 0), 2) as roas,
    ROUND(100.0 * spend / SUM(spend) OVER (), 1) as spend_share,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) as revenue_share
FROM channel_metrics
WHERE spend > 0
ORDER BY revenue DESC;
```

### 3. Lead Quality Funnel
```sql
-- Lead progression through funnel stages
WITH lead_funnel AS (
    SELECT 
        DATE_TRUNC('week', mql.created_at) as week,
        COUNT(DISTINCT mql.lead_id) as mqls,
        COUNT(DISTINCT sql.lead_id) as sqls,
        COUNT(DISTINCT opp.lead_id) as opportunities,
        COUNT(DISTINCT won.lead_id) as customers,
        AVG(mql.lead_score) as avg_mql_score,
        AVG(EXTRACT(EPOCH FROM (sql.created_at - mql.created_at))/3600) as avg_mql_to_sql_hours
    FROM marketing_qualified_leads mql
    LEFT JOIN sales_qualified_leads sql 
        ON mql.lead_id = sql.lead_id
    LEFT JOIN opportunities opp 
        ON sql.lead_id = opp.lead_id
    LEFT JOIN (
        SELECT DISTINCT lead_id 
        FROM opportunities 
        WHERE stage = 'Closed Won'
    ) won ON opp.lead_id = won.lead_id
    WHERE mql.created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY DATE_TRUNC('week', mql.created_at)
)
SELECT 
    week,
    mqls,
    sqls,
    opportunities,
    customers,
    ROUND(100.0 * sqls / NULLIF(mqls, 0), 1) as mql_to_sql_rate,
    ROUND(100.0 * opportunities / NULLIF(sqls, 0), 1) as sql_to_opp_rate,
    ROUND(100.0 * customers / NULLIF(opportunities, 0), 1) as opp_to_customer_rate,
    ROUND(100.0 * customers / NULLIF(mqls, 0), 1) as overall_conversion_rate,
    ROUND(avg_mql_score, 1) as avg_lead_score,
    ROUND(avg_mql_to_sql_hours / 24, 1) as avg_mql_to_sql_days
FROM lead_funnel
ORDER BY week DESC;
```

### 4. Attribution Analysis
```sql
-- Multi-touch attribution impact
WITH attribution_summary AS (
    SELECT 
        at.attribution_model,
        at.channel,
        COUNT(DISTINCT at.customer_id) as attributed_customers,
        SUM(at.attribution_credit) as total_credit,
        SUM(at.attributed_revenue) as attributed_revenue,
        AVG(at.touchpoint_position) as avg_position,
        AVG(at.days_to_conversion) as avg_days_to_conversion
    FROM attribution_touchpoints at
    WHERE at.conversion_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY at.attribution_model, at.channel
)
SELECT 
    attribution_model,
    channel,
    attributed_customers,
    ROUND(total_credit, 1) as attribution_credits,
    ROUND(attributed_revenue, 0) as revenue,
    ROUND(attributed_revenue / NULLIF(total_credit, 0), 0) as revenue_per_credit,
    ROUND(avg_position, 1) as avg_touchpoint_position,
    ROUND(avg_days_to_conversion, 1) as avg_conversion_days,
    ROUND(100.0 * total_credit / SUM(total_credit) OVER (PARTITION BY attribution_model), 1) as credit_share
FROM attribution_summary
WHERE attribution_model IN ('first_touch', 'last_touch', 'linear', 'time_decay')
ORDER BY attribution_model, attributed_revenue DESC;
```

### 5. Content Performance
```sql
-- Content engagement and conversion metrics
WITH content_metrics AS (
    SELECT 
        content_type,
        content_category,
        COUNT(DISTINCT session_id) as total_sessions,
        COUNT(DISTINCT user_id) as unique_visitors,
        AVG(time_on_page_seconds) as avg_time_on_page,
        AVG(bounce_rate) as avg_bounce_rate,
        COUNT(DISTINCT CASE WHEN converted_to_mql THEN session_id END) as converting_sessions,
        COUNT(DISTINCT mql_id) as mqls_generated
    FROM website_content_analytics
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY content_type, content_category
)
SELECT 
    content_type,
    content_category,
    total_sessions,
    unique_visitors,
    ROUND(avg_time_on_page / 60, 1) as avg_time_minutes,
    ROUND(avg_bounce_rate * 100, 1) as bounce_rate_pct,
    converting_sessions,
    ROUND(100.0 * converting_sessions / NULLIF(total_sessions, 0), 2) as conversion_rate,
    mqls_generated,
    ROUND(mqls_generated::NUMERIC / NULLIF(converting_sessions, 0), 2) as mqls_per_conversion
FROM content_metrics
WHERE total_sessions > 100
ORDER BY mqls_generated DESC;
```

## 📈 Advanced Analytics

### Campaign Attribution ROI Model
```sql
-- Advanced ROI calculation with attribution
WITH campaign_attribution AS (
    SELECT 
        c.campaign_id,
        c.campaign_name,
        c.campaign_type,
        c.total_spend,
        COUNT(DISTINCT at.customer_id) as attributed_customers,
        SUM(at.attribution_credit) as total_attribution_credits,
        SUM(at.attributed_revenue) as attributed_revenue,
        SUM(CASE WHEN at.touchpoint_position = 1 THEN at.attribution_credit END) as first_touch_credits,
        SUM(CASE WHEN at.is_last_touch THEN at.attribution_credit END) as last_touch_credits
    FROM entity.entity_campaigns c
    LEFT JOIN attribution_touchpoints at 
        ON c.campaign_id = at.campaign_id
        AND at.attribution_model = 'linear'
    WHERE c.start_date >= CURRENT_DATE - INTERVAL '180 days'
    GROUP BY c.campaign_id, c.campaign_name, c.campaign_type, c.total_spend
)
SELECT 
    campaign_name,
    campaign_type,
    total_spend,
    attributed_customers,
    attributed_revenue,
    ROUND(attributed_revenue / NULLIF(total_spend, 0) - 1, 2) as roi,
    ROUND(attributed_revenue / NULLIF(total_spend, 0), 2) as roas,
    ROUND(total_spend / NULLIF(attributed_customers, 0), 2) as cac,
    ROUND(attributed_revenue / NULLIF(attributed_customers, 0), 0) as avg_customer_value,
    ROUND(100.0 * first_touch_credits / NULLIF(total_attribution_credits, 0), 1) as first_touch_influence,
    ROUND(100.0 * last_touch_credits / NULLIF(total_attribution_credits, 0), 1) as last_touch_influence
FROM campaign_attribution
WHERE total_spend > 1000
ORDER BY roi DESC;
```

### Lead Scoring Model Performance
```sql
-- Evaluate lead scoring model effectiveness
WITH lead_scores AS (
    SELECT 
        CASE 
            WHEN lead_score >= 80 THEN 'A - Hot'
            WHEN lead_score >= 60 THEN 'B - Warm'
            WHEN lead_score >= 40 THEN 'C - Cool'
            ELSE 'D - Cold'
        END as score_grade,
        COUNT(DISTINCT lead_id) as total_leads,
        COUNT(DISTINCT CASE WHEN became_sql THEN lead_id END) as converted_to_sql,
        COUNT(DISTINCT CASE WHEN became_customer THEN lead_id END) as converted_to_customer,
        AVG(days_to_sql) as avg_days_to_sql,
        SUM(customer_revenue) as total_revenue
    FROM marketing_qualified_leads
    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY score_grade
)
SELECT 
    score_grade,
    total_leads,
    converted_to_sql,
    ROUND(100.0 * converted_to_sql / NULLIF(total_leads, 0), 1) as sql_conversion_rate,
    converted_to_customer,
    ROUND(100.0 * converted_to_customer / NULLIF(total_leads, 0), 1) as customer_conversion_rate,
    ROUND(avg_days_to_sql, 1) as avg_days_to_sql,
    ROUND(total_revenue / NULLIF(converted_to_customer, 0), 0) as avg_customer_value,
    ROUND(100.0 * total_leads / SUM(total_leads) OVER (), 1) as pct_of_leads,
    ROUND(100.0 * total_revenue / SUM(total_revenue) OVER (), 1) as pct_of_revenue
FROM lead_scores
ORDER BY 
    CASE score_grade
        WHEN 'A - Hot' THEN 1
        WHEN 'B - Warm' THEN 2
        WHEN 'C - Cool' THEN 3
        WHEN 'D - Cold' THEN 4
    END;
```

### Marketing Velocity Optimization
```sql
-- Calculate marketing velocity components
WITH velocity_components AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        -- L: Number of Leads
        SUM(total_mqls) as qualified_leads,
        -- C: Conversion Rate
        AVG(mql_conversion_rate) as conversion_rate,
        -- V: Average Deal Value
        AVG(avg_deal_value) as avg_deal_value,
        -- T: Sales Cycle Length
        AVG(avg_sales_cycle_days) as avg_cycle_days,
        -- Marketing Velocity = (L × C × V) / T
        (SUM(total_mqls) * AVG(mql_conversion_rate) * AVG(avg_deal_value)) / 
            NULLIF(AVG(avg_sales_cycle_days), 0) as marketing_velocity
    FROM metrics.marketing
    WHERE date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', date)
)
SELECT 
    month,
    qualified_leads,
    ROUND(conversion_rate * 100, 1) as conversion_rate_pct,
    ROUND(avg_deal_value, 0) as avg_deal_value,
    ROUND(avg_cycle_days, 1) as avg_cycle_days,
    ROUND(marketing_velocity, 0) as marketing_velocity,
    ROUND(100.0 * (marketing_velocity - LAG(marketing_velocity) OVER (ORDER BY month)) / 
          NULLIF(LAG(marketing_velocity) OVER (ORDER BY month), 0), 1) as velocity_growth_pct
FROM velocity_components
ORDER BY month DESC;
```

## 🎯 Best Practices

### 1. **ROI Calculation Standards**
- Always include all costs (ad spend, tools, labor)
- Use consistent attribution windows (30/60/90 days)
- Account for customer lifetime value
- Consider both direct and assisted conversions

### 2. **Lead Quality Monitoring**
- Track MQL to SQL conversion rates by source
- Monitor lead velocity through funnel
- Measure time to conversion
- Score leads based on engagement

### 3. **Channel Mix Optimization**
- Diversify spend across channels
- Test incrementally with new channels
- Monitor diminishing returns
- Balance brand vs. performance marketing

### 4. **Attribution Best Practices**
- Use multiple attribution models
- Consider full customer journey
- Account for offline touchpoints
- Validate with holdout tests

## 🔗 Integration Points

### Marketing Platforms
- **Google Ads** → Performance metrics
- **Facebook Ads** → Social advertising
- **LinkedIn Campaign Manager** → B2B targeting
- **Iterable** → Email marketing
- **Google Analytics** → Website analytics

### CRM Integration
- **HubSpot** → Lead management
- **Campaigns** → Attribution tracking
- **Contacts** → Lead scoring
- **Deals** → Revenue attribution

### Analytics Tools
- **Attribution models** → Multi-touch analysis
- **UTM tracking** → Campaign performance
- **Conversion tracking** → ROI measurement

## 📚 Additional Resources

- [Metrics Catalog](../common/metrics-catalog.md) - Complete metrics list
- [Query Patterns](../common/query-patterns.md) - SQL templates
- [Attribution Guide](./attribution-methodology.md) - Attribution models explained
- [Channel Playbooks](./channel-playbooks/) - Channel-specific strategies

## 🚦 Getting Started Checklist

- [ ] Access marketing metrics tables
- [ ] Run channel performance query
- [ ] Review current month's ROI
- [ ] Explore attribution data
- [ ] Join #marketing-analytics Slack
- [ ] Meet with marketing ops team

Welcome to Marketing Analytics! 🚀