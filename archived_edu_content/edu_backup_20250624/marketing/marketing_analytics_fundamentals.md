# Marketing Analytics Fundamentals

## Module Overview

This module covers essential marketing analytics concepts for B2B SaaS companies. You'll learn to measure campaign effectiveness, optimize marketing spend, implement attribution models, and demonstrate marketing's impact on revenue growth.

## Learning Objectives

By completing this module, you will be able to:
1. Build multi-touch attribution models to understand marketing influence
2. Calculate and optimize customer acquisition costs (CAC)
3. Measure campaign ROI across channels
4. Develop lead scoring models for sales alignment
5. Design marketing mix optimization strategies
6. Present marketing performance to executive stakeholders

## 1. Introduction to Marketing Analytics

### The Evolution of B2B Marketing Analytics

Modern B2B marketing has shifted from:
- **Vanity Metrics** → **Revenue Metrics**
- **Last-Touch Attribution** → **Multi-Touch Attribution**
- **Channel Silos** → **Integrated Journey Analysis**
- **Volume Focus** → **Quality + Efficiency Focus**

### Key Stakeholders

**Primary Users:**
- Chief Marketing Officer (CMO)
- VP of Demand Generation
- Marketing Operations Manager
- Growth Marketing Team

**Cross-functional Partners:**
- Sales (lead quality, alignment)
- Finance (budget allocation, ROI)
- Product (product-led growth)
- Customer Success (expansion marketing)

## 2. Foundational Marketing Metrics

### Funnel Metrics

**The B2B Marketing Funnel**
```sql
-- Marketing funnel analysis
WITH funnel_stages AS (
    SELECT 
        'Visitors' as stage, 1 as stage_order, COUNT(DISTINCT visitor_id) as count
    FROM website_visitors
    WHERE visit_date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'Leads' as stage, 2 as stage_order, COUNT(DISTINCT lead_id) as count
    FROM leads
    WHERE created_date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'MQLs' as stage, 3 as stage_order, COUNT(DISTINCT lead_id) as count
    FROM leads
    WHERE mql_date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'SQLs' as stage, 4 as stage_order, COUNT(DISTINCT lead_id) as count
    FROM leads
    WHERE sql_date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'Opportunities' as stage, 5 as stage_order, COUNT(DISTINCT opportunity_id) as count
    FROM opportunities
    WHERE created_date >= CURRENT_DATE - INTERVAL '30 days'
    
    UNION ALL
    
    SELECT 
        'Customers' as stage, 6 as stage_order, COUNT(DISTINCT customer_id) as count
    FROM opportunities
    WHERE stage = 'Closed Won' 
      AND close_date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    stage,
    count,
    ROUND(count * 100.0 / FIRST_VALUE(count) OVER (ORDER BY stage_order), 2) as pct_of_top,
    ROUND(count * 100.0 / LAG(count) OVER (ORDER BY stage_order), 2) as conversion_rate
FROM funnel_stages
ORDER BY stage_order;
```

### Customer Acquisition Cost (CAC)

**CAC Calculation Framework**
```sql
-- Comprehensive CAC calculation
WITH marketing_costs AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(CASE WHEN category = 'Paid Media' THEN amount ELSE 0 END) as paid_media_cost,
        SUM(CASE WHEN category = 'Content' THEN amount ELSE 0 END) as content_cost,
        SUM(CASE WHEN category = 'Events' THEN amount ELSE 0 END) as events_cost,
        SUM(CASE WHEN category = 'Tools' THEN amount ELSE 0 END) as tools_cost,
        SUM(CASE WHEN category = 'Salaries' THEN amount ELSE 0 END) as people_cost,
        SUM(amount) as total_marketing_cost
    FROM marketing_expenses
    GROUP BY DATE_TRUNC('month', date)
),
sales_costs AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(amount) as total_sales_cost
    FROM sales_expenses
    GROUP BY DATE_TRUNC('month', date)
),
new_customers AS (
    SELECT 
        DATE_TRUNC('month', close_date) as month,
        COUNT(*) as customers_acquired,
        SUM(first_year_acv) as total_acv
    FROM opportunities
    WHERE stage = 'Closed Won'
      AND is_new_business = true
    GROUP BY DATE_TRUNC('month', close_date)
)
SELECT 
    m.month,
    nc.customers_acquired,
    m.total_marketing_cost,
    s.total_sales_cost,
    (m.total_marketing_cost + s.total_sales_cost) / NULLIF(nc.customers_acquired, 0) as blended_cac,
    m.total_marketing_cost / NULLIF(nc.customers_acquired, 0) as marketing_cac,
    nc.total_acv / NULLIF(nc.customers_acquired, 0) as avg_acv,
    nc.total_acv / NULLIF(m.total_marketing_cost + s.total_sales_cost, 0) as cac_ratio
FROM marketing_costs m
LEFT JOIN sales_costs s ON m.month = s.month
LEFT JOIN new_customers nc ON m.month = nc.month
ORDER BY m.month DESC;
```

### Marketing Qualified Lead (MQL) Metrics

**Lead Scoring Framework**
```sql
-- Lead scoring model
WITH lead_scores AS (
    SELECT 
        l.lead_id,
        l.email,
        l.company,
        -- Demographic scoring
        CASE 
            WHEN l.company_size >= 1000 THEN 30
            WHEN l.company_size >= 100 THEN 20
            ELSE 10
        END as size_score,
        
        -- Behavioral scoring
        COALESCE(w.page_views, 0) * 2 as engagement_score,
        CASE WHEN w.pricing_page_viewed THEN 20 ELSE 0 END as intent_score,
        CASE WHEN e.email_opens >= 3 THEN 15 ELSE e.email_opens * 5 END as email_score,
        
        -- Fit scoring
        CASE 
            WHEN l.industry IN ('SaaS', 'Technology', 'Financial Services') THEN 20
            WHEN l.industry IN ('Retail', 'Healthcare') THEN 15
            ELSE 5
        END as industry_score,
        
        -- Recency scoring
        CASE 
            WHEN l.created_date >= CURRENT_DATE - INTERVAL '7 days' THEN 15
            WHEN l.created_date >= CURRENT_DATE - INTERVAL '30 days' THEN 10
            ELSE 5
        END as recency_score
        
    FROM leads l
    LEFT JOIN website_behavior w ON l.lead_id = w.lead_id
    LEFT JOIN email_engagement e ON l.lead_id = e.lead_id
)
SELECT 
    lead_id,
    email,
    company,
    size_score + engagement_score + intent_score + email_score + industry_score + recency_score as total_score,
    CASE 
        WHEN size_score + engagement_score + intent_score + email_score + industry_score + recency_score >= 70 THEN 'Hot'
        WHEN size_score + engagement_score + intent_score + email_score + industry_score + recency_score >= 50 THEN 'Warm'
        ELSE 'Cold'
    END as lead_temperature
FROM lead_scores
ORDER BY total_score DESC;
```

## 3. Attribution Modeling

### Understanding Attribution Models

**Types of Attribution**
1. **First-Touch**: 100% credit to first interaction
2. **Last-Touch**: 100% credit to last interaction
3. **Linear**: Equal credit to all touchpoints
4. **Time-Decay**: More credit to recent touchpoints
5. **U-Shaped**: 40% first, 40% last, 20% middle
6. **W-Shaped**: 30% first, 30% lead creation, 30% opportunity, 10% others
7. **Data-Driven**: Machine learning based on actual impact

### Multi-Touch Attribution Implementation

```sql
-- W-shaped attribution model
WITH touchpoints AS (
    SELECT 
        t.lead_id,
        t.touchpoint_date,
        t.channel,
        t.campaign,
        t.touchpoint_type,
        ROW_NUMBER() OVER (PARTITION BY t.lead_id ORDER BY t.touchpoint_date) as touch_number,
        COUNT(*) OVER (PARTITION BY t.lead_id) as total_touches,
        l.mql_date,
        o.opportunity_id,
        o.amount as opportunity_value
    FROM marketing_touchpoints t
    JOIN leads l ON t.lead_id = l.lead_id
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    WHERE o.opportunity_id IS NOT NULL
),
attributed_value AS (
    SELECT 
        lead_id,
        touchpoint_date,
        channel,
        campaign,
        opportunity_value,
        CASE 
            -- First touch (30%)
            WHEN touch_number = 1 THEN 0.30
            -- Lead creation touch (30%)
            WHEN touchpoint_date::date = mql_date::date THEN 0.30
            -- Opportunity creation touch (30%)
            WHEN touchpoint_type = 'opportunity_created' THEN 0.30
            -- All other touches share remaining 10%
            ELSE 0.10 / NULLIF(total_touches - 3, 0)
        END as attribution_weight,
        opportunity_value * 
        CASE 
            WHEN touch_number = 1 THEN 0.30
            WHEN touchpoint_date::date = mql_date::date THEN 0.30
            WHEN touchpoint_type = 'opportunity_created' THEN 0.30
            ELSE 0.10 / NULLIF(total_touches - 3, 0)
        END as attributed_revenue
    FROM touchpoints
)
SELECT 
    channel,
    COUNT(DISTINCT lead_id) as influenced_deals,
    SUM(attributed_revenue) as total_attributed_revenue,
    AVG(attributed_revenue) as avg_attributed_revenue,
    SUM(attribution_weight) / COUNT(DISTINCT lead_id) as avg_influence_weight
FROM attributed_value
GROUP BY channel
ORDER BY total_attributed_revenue DESC;
```

### Attribution Model Comparison

```sql
-- Compare different attribution models
WITH attribution_comparison AS (
    SELECT 
        channel,
        -- First touch attribution
        SUM(CASE WHEN touch_number = 1 THEN opportunity_value ELSE 0 END) as first_touch_revenue,
        -- Last touch attribution  
        SUM(CASE WHEN touch_number = total_touches THEN opportunity_value ELSE 0 END) as last_touch_revenue,
        -- Linear attribution
        SUM(opportunity_value / total_touches) as linear_revenue,
        -- W-shaped attribution (simplified)
        SUM(
            CASE 
                WHEN touch_number = 1 THEN opportunity_value * 0.30
                WHEN touchpoint_type = 'mql_created' THEN opportunity_value * 0.30  
                WHEN touchpoint_type = 'opportunity_created' THEN opportunity_value * 0.30
                ELSE opportunity_value * 0.10 / NULLIF(total_touches - 3, 0)
            END
        ) as w_shaped_revenue
    FROM touchpoints
    GROUP BY channel
)
SELECT 
    channel,
    ROUND(first_touch_revenue) as first_touch,
    ROUND(last_touch_revenue) as last_touch,
    ROUND(linear_revenue) as linear,
    ROUND(w_shaped_revenue) as w_shaped,
    ROUND(w_shaped_revenue - first_touch_revenue) as w_vs_first_delta
FROM attribution_comparison
ORDER BY w_shaped_revenue DESC;
```

## 4. Campaign Analytics

### Campaign Performance Framework

```sql
-- Comprehensive campaign analysis
WITH campaign_metrics AS (
    SELECT 
        c.campaign_id,
        c.campaign_name,
        c.campaign_type,
        c.channel,
        c.start_date,
        c.total_budget,
        COUNT(DISTINCT l.lead_id) as leads_generated,
        COUNT(DISTINCT CASE WHEN l.mql_date IS NOT NULL THEN l.lead_id END) as mqls_generated,
        COUNT(DISTINCT o.opportunity_id) as opportunities_created,
        COUNT(DISTINCT CASE WHEN o.stage = 'Closed Won' THEN o.opportunity_id END) as deals_closed,
        SUM(CASE WHEN o.stage = 'Closed Won' THEN o.amount ELSE 0 END) as revenue_generated
    FROM campaigns c
    LEFT JOIN leads l ON c.campaign_id = l.campaign_id
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    WHERE c.start_date >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY c.campaign_id, c.campaign_name, c.campaign_type, c.channel, c.start_date, c.total_budget
)
SELECT 
    campaign_name,
    campaign_type,
    channel,
    total_budget,
    leads_generated,
    mqls_generated,
    opportunities_created,
    deals_closed,
    revenue_generated,
    -- Efficiency metrics
    ROUND(total_budget / NULLIF(leads_generated, 0), 2) as cost_per_lead,
    ROUND(total_budget / NULLIF(mqls_generated, 0), 2) as cost_per_mql,
    ROUND(total_budget / NULLIF(opportunities_created, 0), 2) as cost_per_opportunity,
    ROUND(total_budget / NULLIF(deals_closed, 0), 2) as cost_per_customer,
    -- Conversion rates
    ROUND(mqls_generated * 100.0 / NULLIF(leads_generated, 0), 2) as lead_to_mql_rate,
    ROUND(opportunities_created * 100.0 / NULLIF(mqls_generated, 0), 2) as mql_to_opp_rate,
    ROUND(deals_closed * 100.0 / NULLIF(opportunities_created, 0), 2) as opp_to_close_rate,
    -- ROI
    ROUND((revenue_generated - total_budget) / NULLIF(total_budget, 0) * 100, 2) as roi_percentage,
    ROUND(revenue_generated / NULLIF(total_budget, 0), 2) as revenue_multiple
FROM campaign_metrics
ORDER BY revenue_generated DESC;
```

### Channel Performance Analysis

```sql
-- Channel performance comparison
WITH channel_performance AS (
    SELECT 
        DATE_TRUNC('month', l.created_date) as month,
        mt.channel,
        COUNT(DISTINCT l.lead_id) as leads,
        COUNT(DISTINCT CASE WHEN l.mql_date IS NOT NULL THEN l.lead_id END) as mqls,
        COUNT(DISTINCT o.opportunity_id) as opportunities,
        SUM(CASE WHEN o.stage = 'Closed Won' THEN o.amount ELSE 0 END) as revenue,
        SUM(me.amount) as channel_spend
    FROM leads l
    JOIN marketing_touchpoints mt ON l.lead_id = mt.lead_id AND mt.touch_number = 1  -- First touch
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    LEFT JOIN marketing_expenses me ON mt.channel = me.channel 
        AND DATE_TRUNC('month', l.created_date) = DATE_TRUNC('month', me.date)
    WHERE l.created_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', l.created_date), mt.channel
)
SELECT 
    channel,
    SUM(leads) as total_leads,
    SUM(mqls) as total_mqls,
    SUM(opportunities) as total_opportunities,
    SUM(revenue) as total_revenue,
    SUM(channel_spend) as total_spend,
    -- Efficiency metrics
    ROUND(AVG(mqls * 100.0 / NULLIF(leads, 0)), 2) as avg_lead_to_mql_rate,
    ROUND(SUM(revenue) / NULLIF(SUM(channel_spend), 0), 2) as overall_roas,
    ROUND(SUM(channel_spend) / NULLIF(SUM(opportunities), 0), 2) as cost_per_opportunity,
    -- Velocity
    ROUND(AVG(opportunities * 1.0 / NULLIF(leads, 0) * 30), 2) as opportunities_per_30_days
FROM channel_performance
GROUP BY channel
HAVING SUM(channel_spend) > 0
ORDER BY total_revenue DESC;
```

## 5. Lead Scoring and Qualification

### Advanced Lead Scoring Model

```sql
-- Predictive lead scoring based on historical conversions
WITH lead_features AS (
    SELECT 
        l.lead_id,
        l.created_date,
        -- Firmographic features
        CASE 
            WHEN l.company_size >= 1000 THEN 'Enterprise'
            WHEN l.company_size >= 100 THEN 'Mid-Market'
            ELSE 'SMB'
        END as size_segment,
        l.industry,
        l.job_title_category,
        
        -- Behavioral features
        COALESCE(w.total_page_views, 0) as page_views,
        COALESCE(w.unique_pages_viewed, 0) as unique_pages,
        COALESCE(w.total_time_on_site, 0) as time_on_site,
        CASE WHEN w.pricing_page_viewed THEN 1 ELSE 0 END as viewed_pricing,
        CASE WHEN w.demo_page_viewed THEN 1 ELSE 0 END as viewed_demo,
        COALESCE(e.email_opens, 0) as email_opens,
        COALESCE(e.email_clicks, 0) as email_clicks,
        
        -- Engagement recency
        CURRENT_DATE - l.created_date::date as days_since_creation,
        CURRENT_DATE - COALESCE(w.last_visit_date, l.created_date)::date as days_since_last_visit,
        
        -- Outcome
        CASE WHEN o.opportunity_id IS NOT NULL THEN 1 ELSE 0 END as converted_to_opportunity
        
    FROM leads l
    LEFT JOIN website_behavior_summary w ON l.lead_id = w.lead_id
    LEFT JOIN email_engagement_summary e ON l.lead_id = e.lead_id
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    WHERE l.created_date >= CURRENT_DATE - INTERVAL '12 months'
),
scoring_weights AS (
    -- Calculate weights based on historical conversion rates
    SELECT 
        'size_segment' as feature,
        size_segment as value,
        AVG(converted_to_opportunity) as conversion_rate,
        LOG(AVG(converted_to_opportunity) / NULLIF((SELECT AVG(converted_to_opportunity) FROM lead_features), 0)) * 10 as weight
    FROM lead_features
    GROUP BY size_segment
    
    UNION ALL
    
    SELECT 
        'industry' as feature,
        industry as value,
        AVG(converted_to_opportunity) as conversion_rate,
        LOG(AVG(converted_to_opportunity) / NULLIF((SELECT AVG(converted_to_opportunity) FROM lead_features), 0)) * 10 as weight
    FROM lead_features
    GROUP BY industry
)
-- Apply scoring to current leads
SELECT 
    l.lead_id,
    l.company,
    l.email,
    -- Calculate composite score
    (
        -- Firmographic score
        COALESCE(sw1.weight, 0) + COALESCE(sw2.weight, 0) +
        -- Behavioral score
        LEAST(lf.page_views * 2, 20) +
        LEAST(lf.email_opens * 3, 15) +
        lf.viewed_pricing * 15 +
        lf.viewed_demo * 10 +
        -- Recency score
        CASE 
            WHEN lf.days_since_last_visit <= 7 THEN 10
            WHEN lf.days_since_last_visit <= 30 THEN 5
            ELSE 0
        END
    ) as lead_score,
    -- Score components for transparency
    COALESCE(sw1.weight, 0) + COALESCE(sw2.weight, 0) as fit_score,
    LEAST(lf.page_views * 2, 20) + LEAST(lf.email_opens * 3, 15) + lf.viewed_pricing * 15 + lf.viewed_demo * 10 as behavior_score,
    CASE 
        WHEN lf.days_since_last_visit <= 7 THEN 10
        WHEN lf.days_since_last_visit <= 30 THEN 5
        ELSE 0
    END as recency_score
FROM leads l
JOIN lead_features lf ON l.lead_id = lf.lead_id
LEFT JOIN scoring_weights sw1 ON sw1.feature = 'size_segment' AND sw1.value = lf.size_segment
LEFT JOIN scoring_weights sw2 ON sw2.feature = 'industry' AND sw2.value = lf.industry
WHERE l.status = 'Open'
  AND lf.converted_to_opportunity = 0
ORDER BY lead_score DESC;
```

## 6. Marketing Mix Optimization

### Budget Allocation Analysis

```sql
-- Marketing mix optimization based on marginal ROI
WITH channel_performance AS (
    SELECT 
        channel,
        DATE_TRUNC('month', date) as month,
        SUM(spend) as monthly_spend,
        SUM(attributed_revenue) as monthly_revenue,
        SUM(attributed_revenue) / NULLIF(SUM(spend), 0) as roas
    FROM marketing_channel_performance
    WHERE date >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY channel, DATE_TRUNC('month', date)
),
marginal_roi AS (
    SELECT 
        channel,
        monthly_spend,
        monthly_revenue,
        roas,
        -- Calculate marginal ROI (change in revenue / change in spend)
        (monthly_revenue - LAG(monthly_revenue) OVER (PARTITION BY channel ORDER BY month)) /
        NULLIF(monthly_spend - LAG(monthly_spend) OVER (PARTITION BY channel ORDER BY month), 0) as marginal_roi,
        -- Efficiency at different spend levels
        NTILE(4) OVER (PARTITION BY channel ORDER BY monthly_spend) as spend_quartile
    FROM channel_performance
),
optimization_recommendations AS (
    SELECT 
        channel,
        AVG(CASE WHEN spend_quartile = 1 THEN roas END) as roas_q1,
        AVG(CASE WHEN spend_quartile = 2 THEN roas END) as roas_q2,
        AVG(CASE WHEN spend_quartile = 3 THEN roas END) as roas_q3,
        AVG(CASE WHEN spend_quartile = 4 THEN roas END) as roas_q4,
        AVG(marginal_roi) as avg_marginal_roi,
        -- Recommendation based on ROI trend
        CASE 
            WHEN AVG(CASE WHEN spend_quartile = 4 THEN roas END) > AVG(CASE WHEN spend_quartile = 3 THEN roas END) THEN 'Increase spend'
            WHEN AVG(CASE WHEN spend_quartile = 4 THEN roas END) < AVG(CASE WHEN spend_quartile = 1 THEN roas END) * 0.5 THEN 'Decrease spend'
            ELSE 'Maintain spend'
        END as recommendation
    FROM marginal_roi
    GROUP BY channel
)
SELECT * FROM optimization_recommendations
ORDER BY avg_marginal_roi DESC;
```

## 7. Content Marketing Analytics

### Content Performance Measurement

```sql
-- Content marketing effectiveness
WITH content_metrics AS (
    SELECT 
        c.content_id,
        c.title,
        c.content_type,
        c.publish_date,
        c.production_cost,
        -- Engagement metrics
        COALESCE(SUM(ce.page_views), 0) as total_views,
        COALESCE(SUM(ce.unique_visitors), 0) as unique_visitors,
        COALESCE(AVG(ce.avg_time_on_page), 0) as avg_engagement_time,
        -- Conversion metrics
        COUNT(DISTINCT l.lead_id) as leads_generated,
        COUNT(DISTINCT CASE WHEN o.opportunity_id IS NOT NULL THEN l.lead_id END) as influenced_opportunities,
        SUM(CASE WHEN o.stage = 'Closed Won' THEN o.amount ELSE 0 END) as influenced_revenue
    FROM content c
    LEFT JOIN content_engagement ce ON c.content_id = ce.content_id
    LEFT JOIN lead_content_touches lct ON c.content_id = lct.content_id
    LEFT JOIN leads l ON lct.lead_id = l.lead_id
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    WHERE c.publish_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY c.content_id, c.title, c.content_type, c.publish_date, c.production_cost
)
SELECT 
    content_type,
    COUNT(*) as pieces_published,
    SUM(production_cost) as total_cost,
    SUM(total_views) as total_views,
    SUM(leads_generated) as total_leads,
    SUM(influenced_opportunities) as total_opportunities,
    SUM(influenced_revenue) as total_influenced_revenue,
    -- Efficiency metrics
    ROUND(AVG(total_views), 0) as avg_views_per_piece,
    ROUND(AVG(leads_generated), 2) as avg_leads_per_piece,
    ROUND(SUM(production_cost) / NULLIF(SUM(leads_generated), 0), 2) as cost_per_lead,
    ROUND(SUM(influenced_revenue) / NULLIF(SUM(production_cost), 0), 2) as content_roi
FROM content_metrics
GROUP BY content_type
ORDER BY total_influenced_revenue DESC;
```

## 8. Marketing Experiment Design

### A/B Testing Framework

```sql
-- A/B test analysis for marketing campaigns
WITH experiment_results AS (
    SELECT 
        experiment_id,
        variant,
        COUNT(DISTINCT visitor_id) as visitors,
        COUNT(DISTINCT CASE WHEN converted THEN visitor_id END) as conversions,
        SUM(revenue) as total_revenue
    FROM marketing_experiments
    WHERE experiment_id = 'email_subject_test_q3'
      AND experiment_date >= '2024-07-01'
      AND experiment_date <= '2024-07-31'
    GROUP BY experiment_id, variant
),
statistical_significance AS (
    SELECT 
        experiment_id,
        variant,
        visitors,
        conversions,
        conversions * 1.0 / visitors as conversion_rate,
        total_revenue / NULLIF(visitors, 0) as revenue_per_visitor,
        -- Calculate statistical significance (simplified)
        SQRT(
            (conversions * 1.0 / visitors * (1 - conversions * 1.0 / visitors)) / visitors
        ) as standard_error
    FROM experiment_results
)
SELECT 
    s.*,
    s.conversion_rate - LAG(s.conversion_rate) OVER (PARTITION BY s.experiment_id ORDER BY s.variant) as lift,
    -- 95% confidence interval
    s.conversion_rate - 1.96 * s.standard_error as ci_lower,
    s.conversion_rate + 1.96 * s.standard_error as ci_upper,
    -- Is the difference significant?
    CASE 
        WHEN s.conversion_rate - 1.96 * s.standard_error > 
             LAG(s.conversion_rate + 1.96 * s.standard_error) OVER (PARTITION BY s.experiment_id ORDER BY s.variant)
        THEN 'Significant'
        ELSE 'Not Significant'
    END as statistical_significance
FROM statistical_significance s
ORDER BY variant;
```

## 9. Executive Reporting

### Marketing Performance Dashboard

```sql
-- Executive marketing metrics summary
WITH current_period AS (
    SELECT 
        -- Revenue metrics
        COUNT(DISTINCT CASE WHEN o.stage = 'Closed Won' THEN o.opportunity_id END) as customers_acquired,
        SUM(CASE WHEN o.stage = 'Closed Won' THEN o.amount ELSE 0 END) as revenue_generated,
        -- Lead metrics
        COUNT(DISTINCT l.lead_id) as leads_generated,
        COUNT(DISTINCT CASE WHEN l.mql_date IS NOT NULL THEN l.lead_id END) as mqls_generated,
        -- Cost metrics
        SUM(DISTINCT me.amount) as total_marketing_spend
    FROM leads l
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    CROSS JOIN marketing_expenses me
    WHERE l.created_date >= DATE_TRUNC('quarter', CURRENT_DATE)
      AND me.date >= DATE_TRUNC('quarter', CURRENT_DATE)
),
previous_period AS (
    -- Same metrics for previous quarter for comparison
    SELECT 
        COUNT(DISTINCT CASE WHEN o.stage = 'Closed Won' THEN o.opportunity_id END) as customers_acquired,
        SUM(CASE WHEN o.stage = 'Closed Won' THEN o.amount ELSE 0 END) as revenue_generated,
        COUNT(DISTINCT l.lead_id) as leads_generated,
        SUM(DISTINCT me.amount) as total_marketing_spend
    FROM leads l
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    CROSS JOIN marketing_expenses me
    WHERE l.created_date >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
      AND l.created_date < DATE_TRUNC('quarter', CURRENT_DATE)
      AND me.date >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
      AND me.date < DATE_TRUNC('quarter', CURRENT_DATE)
)
SELECT 
    'Current Quarter' as period,
    cp.customers_acquired,
    cp.revenue_generated,
    cp.leads_generated,
    cp.mqls_generated,
    cp.total_marketing_spend,
    cp.total_marketing_spend / NULLIF(cp.customers_acquired, 0) as cac,
    cp.revenue_generated / NULLIF(cp.total_marketing_spend, 0) as marketing_roi,
    -- QoQ comparison
    (cp.customers_acquired - pp.customers_acquired) * 100.0 / NULLIF(pp.customers_acquired, 0) as customer_growth_pct,
    (cp.revenue_generated - pp.revenue_generated) * 100.0 / NULLIF(pp.revenue_generated, 0) as revenue_growth_pct,
    (cp.total_marketing_spend - pp.total_marketing_spend) * 100.0 / NULLIF(pp.total_marketing_spend, 0) as spend_growth_pct
FROM current_period cp
CROSS JOIN previous_period pp;
```

## 10. Practical Exercises

### Exercise 1: Multi-Touch Attribution Model
Build and compare three attribution models:
1. First-touch attribution
2. W-shaped attribution
3. Data-driven attribution

Analyze how channel value changes under each model.

### Exercise 2: Lead Scoring Optimization
Current lead scoring has 65% accuracy. Improve it by:
1. Analyzing which features predict conversion
2. Adjusting scoring weights
3. Adding new behavioral signals
4. Validating with holdout data

### Exercise 3: Campaign ROI Analysis
Marketing spent $500K last quarter. Analyze:
1. ROI by campaign type
2. Optimal budget allocation
3. Underperforming campaigns to cut
4. High-potential campaigns to scale

## Key Takeaways

1. **Attribution Matters**: Different models tell different stories - choose based on your sales cycle
2. **Quality > Quantity**: Focus on lead quality metrics, not just volume
3. **Test Everything**: Use A/B testing to validate assumptions
4. **Align with Sales**: Marketing success requires sales alignment
5. **ROI Focus**: Every marketing activity should tie to revenue impact

## Next Steps

- Project 1: Multi-Touch Attribution Model Implementation
- Project 2: Campaign Optimization Study (follow-up)
- Advanced Topics: Predictive lead scoring with ML
- Cross-functional: Marketing-Sales alignment dashboard