# Sales Analytics Fundamentals

## Module Overview

This module introduces core sales analytics concepts and techniques used to drive revenue growth in B2B SaaS organizations. You'll learn to analyze sales pipelines, forecast revenue, optimize territories, and identify factors that drive sales success.

## Learning Objectives

By completing this module, you will be able to:
1. Build and analyze sales funnels to identify bottlenecks
2. Calculate and interpret key sales metrics (win rate, sales velocity, CAC)
3. Perform cohort analysis on sales performance
4. Create accurate revenue forecasts using multiple methods
5. Design data-driven territory and quota plans
6. Present sales insights to executive stakeholders

## 1. Introduction to Sales Analytics

### The Role of Sales Analytics

Sales analytics transforms raw sales data into actionable insights that:
- Improve sales team performance
- Optimize resource allocation
- Increase win rates
- Reduce sales cycles
- Maximize revenue growth

### Key Stakeholders

**Primary Users:**
- VP of Sales / Chief Revenue Officer
- Sales Operations Manager
- Sales Team Leaders
- Account Executives

**Secondary Users:**
- Finance (revenue forecasting)
- Marketing (lead quality)
- Customer Success (expansion opportunities)
- Executive Team (growth strategy)

## 2. Essential Sales Metrics

### Pipeline Metrics

**Pipeline Value**
- Definition: Total value of all open opportunities
- Calculation: SUM(opportunity_amount) WHERE stage != 'Closed'
```sql
SELECT 
    SUM(amount) as total_pipeline_value,
    COUNT(*) as opportunity_count
FROM opportunities
WHERE stage NOT IN ('Closed Won', 'Closed Lost');
```

**Pipeline Coverage Ratio**
- Definition: Pipeline value / Quota
- Target: Typically 3-4x for healthy pipeline
- Indicates if you have enough opportunities to hit targets

**Average Deal Size**
- Definition: Average value of closed won deals
- Use: Capacity planning, quota setting
```sql
SELECT 
    AVG(amount) as avg_deal_size,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) as median_deal_size
FROM opportunities
WHERE stage = 'Closed Won'
  AND close_date >= CURRENT_DATE - INTERVAL '12 months';
```

### Conversion Metrics

**Win Rate**
- Definition: Won Deals / (Won + Lost Deals)
- Benchmark: 20-30% for B2B SaaS
```sql
SELECT 
    COUNT(CASE WHEN stage = 'Closed Won' THEN 1 END) * 100.0 / 
    COUNT(*) as win_rate
FROM opportunities
WHERE stage IN ('Closed Won', 'Closed Lost')
  AND close_date >= CURRENT_DATE - INTERVAL '90 days';
```

**Stage Conversion Rates**
- Definition: % of opportunities that progress from stage to stage
- Use: Identify funnel bottlenecks
```sql
WITH stage_progression AS (
    SELECT 
        opportunity_id,
        stage,
        LAG(stage) OVER (PARTITION BY opportunity_id ORDER BY updated_at) as prev_stage
    FROM opportunity_history
)
SELECT 
    prev_stage,
    stage,
    COUNT(*) as transitions,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY prev_stage) as conversion_rate
FROM stage_progression
WHERE prev_stage IS NOT NULL
GROUP BY prev_stage, stage;
```

### Velocity Metrics

**Sales Cycle Length**
- Definition: Average days from opportunity creation to close
- Use: Forecast accuracy, resource planning
```sql
SELECT 
    AVG(close_date - created_date) as avg_sales_cycle,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY close_date - created_date) as median_cycle
FROM opportunities
WHERE stage = 'Closed Won';
```

**Sales Velocity**
- Formula: (Opportunities × Win Rate × Average Deal Size) / Sales Cycle Length
- Measures how fast you're generating revenue
- Key lever for growth optimization

### Activity Metrics

**Activity-to-Opportunity Ratio**
- Calls/emails/meetings required per opportunity
- Helps optimize sales team time allocation

**Response Time**
- Time from lead creation to first contact
- Critical for conversion rates

## 3. Sales Funnel Analysis

### Building the Funnel

```sql
WITH funnel_stages AS (
    SELECT 
        stage,
        COUNT(*) as opportunities,
        SUM(amount) as total_value,
        AVG(amount) as avg_value
    FROM opportunities
    WHERE created_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY stage
),
stage_order AS (
    SELECT 
        stage,
        opportunities,
        total_value,
        CASE stage
            WHEN 'Lead' THEN 1
            WHEN 'Qualified' THEN 2
            WHEN 'Proposal' THEN 3
            WHEN 'Negotiation' THEN 4
            WHEN 'Closed Won' THEN 5
            ELSE 6
        END as stage_order
    FROM funnel_stages
)
SELECT 
    stage,
    opportunities,
    total_value,
    opportunities * 100.0 / FIRST_VALUE(opportunities) OVER (ORDER BY stage_order) as conversion_from_top
FROM stage_order
ORDER BY stage_order;
```

### Funnel Velocity Analysis

Track how long opportunities spend in each stage:
```sql
SELECT 
    stage,
    AVG(days_in_stage) as avg_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_in_stage) as median_days,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY days_in_stage) as p90_days
FROM opportunity_stage_duration
GROUP BY stage;
```

### Bottleneck Identification

Key indicators of bottlenecks:
- Low conversion rate between stages
- High time spent in stage
- Accumulation of opportunities
- High variance in stage duration

## 4. Revenue Forecasting

### Method 1: Pipeline-Based Forecasting

```sql
WITH weighted_pipeline AS (
    SELECT 
        DATE_TRUNC('month', expected_close_date) as month,
        stage,
        SUM(amount * 
            CASE stage
                WHEN 'Negotiation' THEN 0.8
                WHEN 'Proposal' THEN 0.5
                WHEN 'Qualified' THEN 0.2
                ELSE 0.1
            END
        ) as weighted_value
    FROM opportunities
    WHERE stage NOT IN ('Closed Won', 'Closed Lost')
    GROUP BY DATE_TRUNC('month', expected_close_date), stage
)
SELECT 
    month,
    SUM(weighted_value) as forecasted_revenue
FROM weighted_pipeline
GROUP BY month
ORDER BY month;
```

### Method 2: Historical Conversion-Based

```sql
WITH historical_rates AS (
    SELECT 
        stage,
        AVG(CASE WHEN final_stage = 'Closed Won' THEN 1 ELSE 0 END) as win_rate,
        AVG(days_to_close) as avg_days_to_close
    FROM opportunity_history
    WHERE created_date >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY stage
)
SELECT 
    o.opportunity_id,
    o.amount,
    o.stage,
    h.win_rate,
    o.amount * h.win_rate as expected_value,
    o.created_date + (h.avg_days_to_close || ' days')::interval as expected_close_date
FROM opportunities o
JOIN historical_rates h ON o.stage = h.stage
WHERE o.stage NOT IN ('Closed Won', 'Closed Lost');
```

### Method 3: Rep-Level Forecasting

Factor in individual rep performance:
```sql
WITH rep_performance AS (
    SELECT 
        sales_rep_id,
        AVG(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END) as personal_win_rate,
        AVG(amount) as avg_deal_size
    FROM opportunities
    WHERE close_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY sales_rep_id
)
SELECT 
    o.sales_rep_id,
    r.rep_name,
    SUM(o.amount) as total_pipeline,
    SUM(o.amount * p.personal_win_rate) as weighted_forecast,
    COUNT(o.opportunity_id) as opportunity_count
FROM opportunities o
JOIN sales_reps r ON o.sales_rep_id = r.rep_id
JOIN rep_performance p ON o.sales_rep_id = p.sales_rep_id
WHERE o.stage NOT IN ('Closed Won', 'Closed Lost')
GROUP BY o.sales_rep_id, r.rep_name;
```

## 5. Territory and Quota Planning

### Territory Design Principles

**Balanced Territories Consider:**
- Total addressable market (TAM)
- Current customer distribution
- Rep capacity and experience
- Geographic constraints
- Industry verticals

### TAM Analysis by Territory

```sql
WITH territory_tam AS (
    SELECT 
        territory,
        COUNT(DISTINCT company_id) as total_companies,
        SUM(estimated_annual_value) as total_tam,
        COUNT(DISTINCT CASE WHEN is_customer THEN company_id END) as current_customers,
        SUM(CASE WHEN is_customer THEN annual_value END) as current_revenue
    FROM target_accounts
    GROUP BY territory
)
SELECT 
    territory,
    total_tam,
    current_revenue,
    (total_tam - current_revenue) as opportunity_tam,
    current_revenue * 100.0 / total_tam as market_penetration
FROM territory_tam
ORDER BY opportunity_tam DESC;
```

### Quota Setting Framework

```sql
WITH historical_performance AS (
    SELECT 
        sales_rep_id,
        DATE_TRUNC('quarter', close_date) as quarter,
        SUM(amount) as quarterly_bookings
    FROM opportunities
    WHERE stage = 'Closed Won'
    GROUP BY sales_rep_id, DATE_TRUNC('quarter', close_date)
),
rep_metrics AS (
    SELECT 
        sales_rep_id,
        AVG(quarterly_bookings) as avg_quarterly_bookings,
        STDDEV(quarterly_bookings) as stddev_bookings,
        MAX(quarterly_bookings) as max_quarterly_bookings
    FROM historical_performance
    GROUP BY sales_rep_id
)
SELECT 
    r.rep_name,
    m.avg_quarterly_bookings,
    m.avg_quarterly_bookings * 1.2 as growth_quota,  -- 20% growth
    m.max_quarterly_bookings * 0.9 as stretch_quota,  -- 90% of best quarter
    t.total_tam * 0.02 as tam_based_quota  -- 2% of TAM
FROM rep_metrics m
JOIN sales_reps r ON m.sales_rep_id = r.rep_id
JOIN territory_assignments t ON r.territory = t.territory;
```

## 6. Sales Team Performance Analysis

### Individual Rep Scorecard

```sql
WITH rep_metrics AS (
    SELECT 
        sales_rep_id,
        COUNT(CASE WHEN stage = 'Closed Won' THEN 1 END) as deals_won,
        COUNT(CASE WHEN stage IN ('Closed Won', 'Closed Lost') THEN 1 END) as total_closed,
        SUM(CASE WHEN stage = 'Closed Won' THEN amount END) as revenue,
        AVG(CASE WHEN stage = 'Closed Won' THEN close_date - created_date END) as avg_cycle_time,
        COUNT(DISTINCT account_id) as accounts_touched
    FROM opportunities
    WHERE created_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY sales_rep_id
)
SELECT 
    r.rep_name,
    m.deals_won,
    m.revenue,
    m.deals_won * 100.0 / NULLIF(m.total_closed, 0) as win_rate,
    m.avg_cycle_time,
    m.revenue / NULLIF(m.deals_won, 0) as avg_deal_size,
    m.accounts_touched
FROM rep_metrics m
JOIN sales_reps r ON m.sales_rep_id = r.rep_id
ORDER BY m.revenue DESC;
```

### Team Performance Trends

```sql
SELECT 
    DATE_TRUNC('month', close_date) as month,
    COUNT(DISTINCT sales_rep_id) as active_reps,
    COUNT(CASE WHEN stage = 'Closed Won' THEN 1 END) as deals_won,
    SUM(CASE WHEN stage = 'Closed Won' THEN amount END) as total_revenue,
    SUM(CASE WHEN stage = 'Closed Won' THEN amount END) / 
        COUNT(DISTINCT sales_rep_id) as revenue_per_rep
FROM opportunities
WHERE close_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', close_date)
ORDER BY month;
```

## 7. Lead Quality and Source Analysis

### Lead-to-Opportunity Conversion

```sql
WITH lead_outcomes AS (
    SELECT 
        lead_source,
        COUNT(*) as total_leads,
        COUNT(CASE WHEN converted_to_opportunity THEN 1 END) as converted_leads,
        AVG(days_to_conversion) as avg_conversion_time,
        SUM(CASE WHEN converted_to_opportunity THEN opportunity_value END) as total_pipeline
    FROM leads
    WHERE created_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY lead_source
)
SELECT 
    lead_source,
    total_leads,
    converted_leads,
    converted_leads * 100.0 / total_leads as conversion_rate,
    avg_conversion_time,
    total_pipeline / NULLIF(converted_leads, 0) as avg_opportunity_value
FROM lead_outcomes
ORDER BY conversion_rate DESC;
```

### ROI by Lead Source

```sql
WITH source_performance AS (
    SELECT 
        l.lead_source,
        COUNT(DISTINCT l.lead_id) as leads_generated,
        SUM(CASE WHEN o.stage = 'Closed Won' THEN o.amount END) as revenue_generated,
        SUM(l.acquisition_cost) as total_cost
    FROM leads l
    LEFT JOIN opportunities o ON l.lead_id = o.lead_id
    WHERE l.created_date >= CURRENT_DATE - INTERVAL '180 days'
    GROUP BY l.lead_source
)
SELECT 
    lead_source,
    leads_generated,
    revenue_generated,
    total_cost,
    revenue_generated / NULLIF(total_cost, 0) as roi,
    total_cost / NULLIF(leads_generated, 0) as cost_per_lead,
    revenue_generated / NULLIF(leads_generated, 0) as revenue_per_lead
FROM source_performance
ORDER BY roi DESC;
```

## 8. Practical Exercises

### Exercise 1: Pipeline Health Assessment
Using the provided dataset:
1. Calculate current pipeline coverage ratio
2. Identify stages with lowest conversion rates
3. Find opportunities that have been stuck for >30 days
4. Recommend actions to improve pipeline health

### Exercise 2: Sales Forecasting
Create three different revenue forecasts for next quarter:
1. Conservative (based on historical conversion)
2. Realistic (weighted pipeline)
3. Aggressive (assuming improved performance)

### Exercise 3: Territory Optimization
Analyze current territory assignments and:
1. Calculate TAM per territory
2. Assess current penetration rates
3. Identify imbalanced territories
4. Propose redistribution plan

## 9. Key Takeaways

1. **Focus on Leading Indicators**: Pipeline generation and stage progression predict future revenue
2. **Balance Multiple Metrics**: No single metric tells the complete story
3. **Consider Context**: Industry, seasonality, and market conditions affect benchmarks
4. **Enable Action**: Analytics should drive specific sales behaviors
5. **Iterate and Improve**: Continuously refine forecasting models based on actual results

## 10. Additional Resources

- **Templates**: Sales dashboard templates in `/project_templates/sales/`
- **SQL Library**: Common sales queries in `/common_resources/sql_library/sales/`
- **Best Practices**: Sales analytics best practices guide
- **Case Studies**: Real-world sales transformation examples

## Next Steps

After mastering these fundamentals, proceed to:
- Project 1: Pipeline Health Assessment
- Advanced Topics: Predictive lead scoring
- Cross-functional: Sales & Marketing alignment analytics