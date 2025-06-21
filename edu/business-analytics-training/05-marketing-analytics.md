# Module 5: Marketing Analytics

## Overview

Marketing analytics measures the effectiveness of efforts to attract, convert, and retain customers. In SaaS businesses, where customer acquisition costs are high and payback periods are long, sophisticated marketing analytics can make the difference between efficient growth and unsustainable burn rates.

## The Marketing Analytics Framework

### Marketing Funnel Stages

1. **Awareness**: First exposure to brand/product
2. **Interest**: Engagement with content/website
3. **Consideration**: Evaluation and comparison
4. **Intent**: Demo requests, pricing views
5. **Purchase**: Conversion to customer
6. **Loyalty**: Retention and advocacy

### Attribution Challenges

**Multi-Touch Reality**: B2B buyers interact with 7-20 touchpoints before purchasing

**Long Sales Cycles**: Enterprise deals can take 6-18 months

**Multiple Stakeholders**: 5-10 decision makers per deal

**Cross-Channel Journey**: Seamless movement between channels

## Core Marketing Metrics

### 1. Traffic and Awareness Metrics

**Website Traffic Analysis**:
```sql
-- Multi-channel traffic trends
WITH traffic_summary AS (
  SELECT 
    DATE_TRUNC('week', visit_date) as week,
    traffic_source,
    traffic_medium,
    COUNT(DISTINCT visitor_id) as unique_visitors,
    COUNT(*) as sessions,
    SUM(page_views) as total_page_views,
    AVG(session_duration_seconds) as avg_session_duration,
    AVG(CASE WHEN bounce = 1 THEN 1 ELSE 0 END) * 100 as bounce_rate
  FROM web_analytics
  WHERE visit_date >= CURRENT_DATE - INTERVAL '90 days'
  GROUP BY week, traffic_source, traffic_medium
)SELECT 
  week,
  CASE 
    WHEN traffic_source IN ('google', 'bing', 'duckduckgo') AND traffic_medium = 'organic' THEN 'Organic Search'
    WHEN traffic_source IN ('google', 'bing', 'facebook', 'linkedin') AND traffic_medium = 'cpc' THEN 'Paid Search/Social'
    WHEN traffic_source IN ('facebook', 'twitter', 'linkedin') AND traffic_medium = 'organic' THEN 'Organic Social'
    WHEN traffic_medium = 'email' THEN 'Email'
    WHEN traffic_source = 'direct' THEN 'Direct'
    ELSE 'Other'
  END as channel,
  SUM(unique_visitors) as visitors,
  SUM(sessions) as sessions,
  ROUND(AVG(avg_session_duration), 0) as avg_session_seconds,
  ROUND(AVG(bounce_rate), 1) as bounce_rate_pct
FROM traffic_summary
GROUP BY week, channel
ORDER BY week DESC, visitors DESC;

### 2. Lead Generation Metrics

**Lead Scoring and Quality**:
```sql
-- Lead quality by source
WITH lead_scoring AS (
  SELECT 
    l.lead_id,
    l.created_date,
    l.lead_source,
    l.lead_score,
    CASE 
      WHEN l.company_size >= 1000 THEN 20
      WHEN l.company_size >= 100 THEN 10
      ELSE 5
    END as size_score,
    CASE 
      WHEN l.intent_signals >= 5 THEN 20
      WHEN l.intent_signals >= 3 THEN 10
      ELSE 5
    END as intent_score,
    CASE WHEN c.customer_id IS NOT NULL THEN 1 ELSE 0 END as converted
  FROM leads l
  LEFT JOIN customers c ON l.lead_id = c.lead_id
  WHERE l.created_date >= CURRENT_DATE - INTERVAL '180 days'
)SELECT 
  lead_source,
  COUNT(*) as total_leads,
  SUM(converted) as converted_leads,
  ROUND(100.0 * SUM(converted) / COUNT(*), 1) as conversion_rate,
  AVG(lead_score + size_score + intent_score) as avg_quality_score,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lead_score + size_score + intent_score) as median_quality_score
FROM lead_scoring
GROUP BY lead_source
HAVING COUNT(*) >= 10
ORDER BY conversion_rate DESC;

**Cost Per Lead (CPL)**:
```sql
-- Channel-specific lead costs
WITH channel_spend AS (
  SELECT 
    DATE_TRUNC('month', spend_date) as month,
    channel,
    SUM(spend_amount) as total_spend
  FROM marketing_spend
  GROUP BY month, channel
),
channel_leads AS (
  SELECT 
    DATE_TRUNC('month', created_date) as month,
    lead_source as channel,
    COUNT(*) as leads_generated,
    SUM(CASE WHEN qualified = 1 THEN 1 ELSE 0 END) as qualified_leads
  FROM leads
  GROUP BY month, channel
)
SELECT 
  cs.month,
  cs.channel,
  cs.total_spend,
  cl.leads_generated,
  cl.qualified_leads,
  ROUND(cs.total_spend / NULLIF(cl.leads_generated, 0), 2) as cost_per_lead,
  ROUND(cs.total_spend / NULLIF(cl.qualified_leads, 0), 2) as cost_per_qualified_lead
FROM channel_spend cs
JOIN channel_leads cl ON cs.month = cl.month AND cs.channel = cl.channel
WHERE cs.month >= CURRENT_DATE - INTERVAL '6 months'
ORDER BY cs.month DESC, cs.channel;
```
### 3. Conversion Metrics

**Marketing Qualified Leads (MQL) to Sales Qualified Leads (SQL)**:
```sql
-- Lead progression funnel
WITH lead_stages AS (
  SELECT 
    lead_id,
    created_date,
    lead_source,
    mql_date,
    sql_date,
    opportunity_date,
    closed_won_date,
    DATEDIFF('day', created_date, mql_date) as days_to_mql,
    DATEDIFF('day', mql_date, sql_date) as days_mql_to_sql,
    DATEDIFF('day', sql_date, opportunity_date) as days_sql_to_opp,
    DATEDIFF('day', opportunity_date, closed_won_date) as days_to_close
  FROM lead_lifecycle
)
SELECT 
  lead_source,
  COUNT(*) as total_leads,
  COUNT(mql_date) as mqls,
  COUNT(sql_date) as sqls,
  COUNT(opportunity_date) as opportunities,
  COUNT(closed_won_date) as customers,
  ROUND(100.0 * COUNT(mql_date) / COUNT(*), 1) as lead_to_mql_rate,
  ROUND(100.0 * COUNT(sql_date) / NULLIF(COUNT(mql_date), 0), 1) as mql_to_sql_rate,
  ROUND(100.0 * COUNT(opportunity_date) / NULLIF(COUNT(sql_date), 0), 1) as sql_to_opp_rate,
  ROUND(100.0 * COUNT(closed_won_date) / NULLIF(COUNT(opportunity_date), 0), 1) as close_rate,
  AVG(days_to_mql) as avg_days_to_mql,
  AVG(days_mql_to_sql) as avg_days_mql_to_sql
FROM lead_stages
GROUP BY lead_source
ORDER BY customers DESC;
```
### 4. Campaign Performance Metrics

**Return on Ad Spend (ROAS)**:
```sql
-- Campaign ROI analysis
WITH campaign_performance AS (
  SELECT 
    c.campaign_id,
    c.campaign_name,
    c.campaign_type,
    c.start_date,
    c.end_date,
    SUM(c.spend) as total_spend,
    COUNT(DISTINCT l.lead_id) as leads_generated,
    COUNT(DISTINCT o.opportunity_id) as opportunities_created,
    COUNT(DISTINCT cust.customer_id) as customers_acquired,
    SUM(cust.first_year_acv) as total_acv,
    SUM(cust.ltv) as total_ltv
  FROM campaigns c
  LEFT JOIN leads l ON c.campaign_id = l.campaign_id
  LEFT JOIN opportunities o ON l.lead_id = o.lead_id
  LEFT JOIN customers cust ON o.opportunity_id = cust.opportunity_id
  WHERE c.start_date >= CURRENT_DATE - INTERVAL '12 months'
  GROUP BY c.campaign_id, c.campaign_name, c.campaign_type, c.start_date, c.end_date
)
SELECT 
  campaign_name,
  campaign_type,
  total_spend,
  leads_generated,
  customers_acquired,
  ROUND(total_spend / NULLIF(leads_generated, 0), 2) as cost_per_lead,
  ROUND(total_spend / NULLIF(customers_acquired, 0), 2) as cac,
  ROUND(total_acv / NULLIF(total_spend, 0), 2) as first_year_roas,
  ROUND(total_ltv / NULLIF(total_spend, 0), 2) as ltv_roas,
  ROUND(total_spend / NULLIF(total_acv/12, 0), 1) as payback_months
FROM campaign_performance
WHERE total_spend > 0
ORDER BY ltv_roas DESC;
```
### 5. Attribution Metrics

**Multi-Touch Attribution**:
```sql
-- Attribution model comparison
WITH touchpoint_data AS (
  SELECT 
    t.visitor_id,
    t.touchpoint_date,
    t.channel,
    t.campaign_id,
    c.customer_id,
    c.first_purchase_date,
    c.first_year_acv,
    ROW_NUMBER() OVER (PARTITION BY t.visitor_id ORDER BY t.touchpoint_date) as touch_number,
    ROW_NUMBER() OVER (PARTITION BY t.visitor_id ORDER BY t.touchpoint_date DESC) as reverse_touch_number,
    COUNT(*) OVER (PARTITION BY t.visitor_id) as total_touches
  FROM marketing_touchpoints t
  INNER JOIN customers c ON t.visitor_id = c.visitor_id
  WHERE t.touchpoint_date <= c.first_purchase_date
)
SELECT 
  channel,
  -- First Touch Attribution
  SUM(CASE WHEN touch_number = 1 THEN first_year_acv ELSE 0 END) as first_touch_revenue,
  -- Last Touch Attribution
  SUM(CASE WHEN reverse_touch_number = 1 THEN first_year_acv ELSE 0 END) as last_touch_revenue,
  -- Linear Attribution (equal credit)
  SUM(first_year_acv / total_touches) as linear_revenue,
  -- Position Based (40% first, 40% last, 20% middle)
  SUM(CASE 
    WHEN touch_number = 1 THEN first_year_acv * 0.4
    WHEN reverse_touch_number = 1 THEN first_year_acv * 0.4
    ELSE first_year_acv * 0.2 / GREATEST(total_touches - 2, 1)
  END) as position_based_revenue,
  COUNT(DISTINCT visitor_id) as unique_visitors_touched
FROM touchpoint_data
GROUP BY channel
ORDER BY position_based_revenue DESC;
```
### 6. Content Marketing Metrics

**Content Performance Analysis**:
```sql
-- Content engagement and conversion impact
WITH content_metrics AS (
  SELECT 
    c.content_id,
    c.content_title,
    c.content_type,
    c.publish_date,
    COUNT(DISTINCT v.visitor_id) as unique_views,
    SUM(v.time_on_page) as total_time_spent,
    AVG(v.scroll_depth) as avg_scroll_depth,
    COUNT(DISTINCT l.lead_id) as leads_generated,
    COUNT(DISTINCT cust.customer_id) as influenced_customers
  FROM content c
  LEFT JOIN content_views v ON c.content_id = v.content_id
  LEFT JOIN leads l ON v.visitor_id = l.visitor_id 
    AND l.created_date BETWEEN v.view_date AND v.view_date + INTERVAL '30 days'
  LEFT JOIN customers cust ON l.lead_id = cust.lead_id
  WHERE c.publish_date >= CURRENT_DATE - INTERVAL '12 months'
  GROUP BY c.content_id, c.content_title, c.content_type, c.publish_date
)
SELECT 
  content_type,
  COUNT(*) as pieces_published,
  SUM(unique_views) as total_views,
  AVG(unique_views) as avg_views_per_piece,
  ROUND(AVG(total_time_spent / NULLIF(unique_views, 0)), 0) as avg_time_per_view,
  SUM(leads_generated) as total_leads,
  ROUND(AVG(leads_generated), 2) as avg_leads_per_piece,
  SUM(influenced_customers) as total_influenced_customers
FROM content_metrics
GROUP BY content_type
ORDER BY total_leads DESC;
```
## Common Stakeholder Questions

### From CMO/Marketing Leadership
1. "What's our overall CAC and how is it trending?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How much does it cost to acquire customers and is it getting better or worse? | Calculate total marketing spend divided by new customers: `SUM(marketing_costs) / COUNT(new_customers)` by month |

2. "Which channels deliver the highest quality leads?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What marketing sources generate leads that actually become customers? | Compare conversion rates and LTV by channel from `lead_source` to `customer_outcomes` |

3. "What's the ROI on our content marketing efforts?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are our blogs, whitepapers, and content paying off? | Track content costs vs attributed revenue from `content_attribution` and `revenue_influence` |

4. "How effective are our nurture campaigns?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do our email sequences and follow-ups convert leads? | Measure engagement rates and conversion from `email_campaigns` to `lead_progression` |

5. "What's our brand awareness trend?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are more people discovering and recognizing our brand? | Track organic search volume, direct traffic, brand mention trends from `brand_metrics` |

### From Demand Generation
1. "Which campaigns should we scale up/down?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which marketing efforts should get more or less budget? | Compare campaign ROI, efficiency metrics from `campaign_performance` table |

2. "What's the optimal budget allocation across channels?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How should we split our marketing spend for best results? | Analyze marginal returns by channel from `channel_efficiency` and diminishing returns curves |

3. "How do different attribution models change our view?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Does first-touch vs last-touch attribution change which channels look best? | Compare attribution results from `touchpoint_attribution` using different models |

4. "What content drives the most MQLs?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which blogs, whitepapers, or resources generate qualified leads? | Track content engagement to MQL conversion from `content_mql_attribution` |

5. "What's our cost per SQL by source?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How much does each channel cost to generate sales-qualified leads? | Calculate spend per SQL from `marketing_spend` divided by `sql_attribution` by source |

### From Sales Team
1. "Which marketing sources provide the best leads?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What marketing channels give me leads that actually close? | Compare close rates and deal size by lead source from `lead_outcomes` |

2. "How long do leads stay warm before converting?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How quickly do I need to follow up with leads? | Calculate time between lead creation and conversion from `lead_lifecycle_timing` |

3. "What content helps close deals?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which marketing materials should I share with prospects? | Track content engagement during sales process from `content_sales_influence` |

4. "Which campaigns generate enterprise leads?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What marketing efforts bring in big company prospects? | Filter campaigns by company size of generated leads from `lead_firmographics` |

5. "What's the lead quality score distribution?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How many high-quality vs low-quality leads are we getting? | Analyze lead score distribution and conversion rates from `lead_scoring_analysis` |

### From Finance/Executive Team
1. "What's our marketing efficiency ratio?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How efficiently is marketing generating revenue? | Calculate marketing-influenced revenue divided by marketing spend from `marketing_efficiency_metrics` |

2. "How does marketing contribute to pipeline?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What percentage of our sales pipeline comes from marketing? | Track marketing-sourced opportunities and revenue from `pipeline_attribution` |

3. "What's the payback period on marketing spend?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How many months until marketing investments pay for themselves? | Calculate CAC payback from monthly customer revenue vs acquisition cost |

4. "Are we hitting our CAC targets?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Is our customer acquisition cost within acceptable limits? | Compare actual vs target CAC from `cac_targets` vs `actual_cac_metrics` |

5. "What's driving changes in marketing ROI?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Why is our marketing ROI better or worse than before? | Analyze ROI component changes: spend efficiency, conversion rates, customer value from `roi_variance_analysis` |

## Standard Marketing Reports

### 1. Marketing Performance Dashboard
```sql
-- Executive marketing summary
WITH monthly_metrics AS (
  SELECT 
    DATE_TRUNC('month', date) as month,
    SUM(marketing_spend) as total_spend,
    SUM(leads_generated) as total_leads,
    SUM(mqls_generated) as total_mqls,
    SUM(sqls_generated) as total_sqls,
    SUM(new_customers) as customers_acquired,
    SUM(new_customer_acv) as new_acv
  FROM daily_marketing_metrics
  WHERE date >= CURRENT_DATE - INTERVAL '12 months'
  GROUP BY month
)SELECT 
  month,
  total_spend,
  total_leads,
  ROUND(total_spend / NULLIF(total_leads, 0), 2) as cpl,
  total_mqls,
  ROUND(100.0 * total_mqls / NULLIF(total_leads, 0), 1) as lead_to_mql_rate,
  total_sqls,
  ROUND(100.0 * total_sqls / NULLIF(total_mqls, 0), 1) as mql_to_sql_rate,
  customers_acquired,
  ROUND(total_spend / NULLIF(customers_acquired, 0), 0) as cac,
  ROUND(new_acv / NULLIF(total_spend, 0), 2) as first_year_roas
FROM monthly_metrics
ORDER BY month DESC;

### 2. Channel Mix Analysis
```sql
-- Channel contribution and efficiency
WITH channel_performance AS (
  SELECT 
    channel,
    DATE_TRUNC('quarter', date) as quarter,
    SUM(spend) as channel_spend,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(leads) as leads,
    SUM(customers) as customers,
    SUM(revenue_attributed) as attributed_revenue
  FROM channel_metrics
  WHERE date >= CURRENT_DATE - INTERVAL '4 quarters'
  GROUP BY channel, quarter
)
SELECT 
  quarter,
  channel,
  channel_spend,
  ROUND(100.0 * channel_spend / SUM(channel_spend) OVER (PARTITION BY quarter), 1) as spend_share,
  ROUND(clicks::NUMERIC / NULLIF(impressions, 0) * 100, 2) as ctr,
  ROUND(leads::NUMERIC / NULLIF(clicks, 0) * 100, 1) as conversion_rate,
  ROUND(channel_spend / NULLIF(leads, 0), 2) as cpl,
  ROUND(channel_spend / NULLIF(customers, 0), 0) as cac,
  ROUND(attributed_revenue / NULLIF(channel_spend, 0), 2) as roas
FROM channel_performance
ORDER BY quarter DESC, channel_spend DESC;
```
### 3. Lead Velocity Report
```sql
-- Lead flow and velocity metrics
WITH lead_velocity AS (
  SELECT 
    DATE_TRUNC('week', created_date) as week,
    COUNT(*) as new_leads,
    AVG(COUNT(*)) OVER (ORDER BY DATE_TRUNC('week', created_date) ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) as four_week_avg,
    COUNT(*) - LAG(COUNT(*), 1) OVER (ORDER BY DATE_TRUNC('week', created_date)) as week_over_week_change
  FROM leads
  WHERE created_date >= CURRENT_DATE - INTERVAL '6 months'
  GROUP BY week
),
stage_velocity AS (
  SELECT 
    DATE_TRUNC('week', stage_date) as week,
    stage_name,
    COUNT(*) as stage_entries,
    AVG(days_in_stage) as avg_days_in_stage
  FROM lead_stage_history
  WHERE stage_date >= CURRENT_DATE - INTERVAL '6 months'
  GROUP BY week, stage_name
)
SELECT 
  lv.week,
  lv.new_leads,
  ROUND(lv.four_week_avg, 0) as four_week_avg_leads,
  lv.week_over_week_change,
  ROUND(100.0 * lv.week_over_week_change / NULLIF(LAG(lv.new_leads, 1) OVER (ORDER BY lv.week), 0), 1) as wow_growth_rate,
  MAX(CASE WHEN sv.stage_name = 'MQL' THEN sv.stage_entries END) as new_mqls,
  MAX(CASE WHEN sv.stage_name = 'SQL' THEN sv.stage_entries END) as new_sqls,
  MAX(CASE WHEN sv.stage_name = 'MQL' THEN sv.avg_days_in_stage END) as avg_days_as_mql
FROM lead_velocity lv
LEFT JOIN stage_velocity sv ON lv.week = sv.week
GROUP BY lv.week, lv.new_leads, lv.four_week_avg, lv.week_over_week_change
ORDER BY lv.week DESC;
```
## Advanced Marketing Analytics Techniques

### 1. Marketing Mix Modeling
```sql
-- Analyze interaction effects between channels
WITH channel_combinations AS (
  SELECT 
    c.customer_id,
    c.first_purchase_date,
    STRING_AGG(DISTINCT mt.channel, ' + ' ORDER BY mt.channel) as channel_mix,
    COUNT(DISTINCT mt.channel) as channels_touched,
    SUM(ms.spend) / COUNT(DISTINCT mt.channel) as avg_spend_per_channel,
    c.first_year_acv
  FROM customers c
  JOIN marketing_touchpoints mt ON c.visitor_id = mt.visitor_id
  JOIN marketing_spend ms ON mt.campaign_id = ms.campaign_id
  WHERE mt.touchpoint_date <= c.first_purchase_date
  GROUP BY c.customer_id, c.first_purchase_date, c.first_year_acv
)
SELECT 
  channel_mix,
  channels_touched,
  COUNT(*) as customers,
  AVG(first_year_acv) as avg_acv,
  AVG(avg_spend_per_channel) as avg_spend_per_channel,
  AVG(first_year_acv) / NULLIF(AVG(avg_spend_per_channel), 0) as efficiency_ratio
FROM channel_combinations
GROUP BY channel_mix, channels_touched
HAVING COUNT(*) >= 5
ORDER BY customers DESC
LIMIT 20;
```
### 2. Predictive Lead Scoring
```sql
-- Build features for lead scoring model
WITH lead_features AS (
  SELECT 
    l.lead_id,
    l.company_size,
    l.industry,
    -- Behavioral features
    COUNT(DISTINCT wa.session_id) as website_sessions,
    SUM(wa.page_views) as total_page_views,
    MAX(CASE WHEN wa.page_path LIKE '%pricing%' THEN 1 ELSE 0 END) as viewed_pricing,
    MAX(CASE WHEN wa.page_path LIKE '%demo%' THEN 1 ELSE 0 END) as viewed_demo,
    COUNT(DISTINCT ce.email_id) as emails_opened,
    COUNT(DISTINCT CASE WHEN ce.clicked = 1 THEN ce.email_id END) as emails_clicked,
    -- Engagement recency
    DATEDIFF('day', MAX(wa.visit_date), CURRENT_DATE) as days_since_last_visit,
    -- Outcome
    CASE WHEN c.customer_id IS NOT NULL THEN 1 ELSE 0 END as converted
  FROM leads l
  LEFT JOIN web_analytics wa ON l.email = wa.email
  LEFT JOIN campaign_emails ce ON l.email = ce.recipient_email
  LEFT JOIN customers c ON l.lead_id = c.lead_id
  WHERE l.created_date >= CURRENT_DATE - INTERVAL '12 months'
  GROUP BY l.lead_id, l.company_size, l.industry, c.customer_id
)
SELECT 
  CASE 
    WHEN converted = 1 THEN 'Converted'
    ELSE 'Not Converted'
  END as outcome,
  AVG(website_sessions) as avg_sessions,
  AVG(total_page_views) as avg_page_views,
  AVG(viewed_pricing) * 100 as pct_viewed_pricing,
  AVG(viewed_demo) * 100 as pct_viewed_demo,
  AVG(emails_opened) as avg_emails_opened,
  AVG(days_since_last_visit) as avg_days_since_visit
FROM lead_features
GROUP BY converted
ORDER BY converted DESC;
```
### 3. Campaign Optimization Analysis
```sql
-- A/B test results for campaign optimization
WITH campaign_variants AS (
  SELECT 
    campaign_id,
    variant,
    COUNT(DISTINCT recipient_id) as recipients,
    COUNT(DISTINCT CASE WHEN opened = 1 THEN recipient_id END) as openers,
    COUNT(DISTINCT CASE WHEN clicked = 1 THEN recipient_id END) as clickers,
    COUNT(DISTINCT CASE WHEN converted = 1 THEN recipient_id END) as converters,
    SUM(revenue_attributed) as total_revenue
  FROM campaign_test_results
  WHERE test_end_date <= CURRENT_DATE
  GROUP BY campaign_id, variant
),
statistical_significance AS (
  SELECT 
    campaign_id,
    MAX(CASE WHEN variant = 'Control' THEN clickers::FLOAT / recipients END) as control_ctr,
    MAX(CASE WHEN variant = 'Test' THEN clickers::FLOAT / recipients END) as test_ctr,
    MAX(CASE WHEN variant = 'Control' THEN recipients END) as control_size,
    MAX(CASE WHEN variant = 'Test' THEN recipients END) as test_size
  FROM campaign_variants
  GROUP BY campaign_id
)
SELECT 
  cv.campaign_id,
  cv.variant,
  cv.recipients,
  ROUND(100.0 * cv.openers / cv.recipients, 1) as open_rate,
  ROUND(100.0 * cv.clickers / cv.recipients, 1) as click_rate,
  ROUND(100.0 * cv.converters / cv.recipients, 2) as conversion_rate,
  ROUND(cv.total_revenue / NULLIF(cv.recipients, 0), 2) as revenue_per_recipient,
  CASE 
    WHEN cv.variant = 'Test' AND 
         ABS(ss.test_ctr - ss.control_ctr) > 1.96 * SQRT(ss.control_ctr * (1 - ss.control_ctr) / ss.control_size + 
                                                         ss.test_ctr * (1 - ss.test_ctr) / ss.test_size)
    THEN 'Significant'
    ELSE 'Not Significant'
  END as statistical_significance
FROM campaign_variants cv
JOIN statistical_significance ss ON cv.campaign_id = ss.campaign_id
ORDER BY cv.campaign_id, cv.variant;
```