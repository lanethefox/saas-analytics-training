# Module 6: Sales Analytics

## Overview

Sales analytics transforms raw sales data into actionable insights that drive revenue growth. In SaaS businesses, where sales cycles are complex and deal values vary significantly, sophisticated analytics help optimize sales processes, improve forecasting accuracy, and maximize revenue potential.

## The Sales Analytics Framework

### Sales Process Stages

1. **Prospecting**: Identifying potential customers
2. **Qualification**: Determining fit and budget
3. **Discovery**: Understanding needs and pain points
4. **Proposal**: Presenting solution and pricing
5. **Negotiation**: Finalizing terms and conditions
6. **Closing**: Securing the contract
7. **Expansion**: Growing the account post-sale

### Key Sales Metrics Categories

- **Activity Metrics**: Calls, emails, meetings
- **Pipeline Metrics**: Opportunities, stages, velocity
- **Performance Metrics**: Quota attainment, win rates
- **Efficiency Metrics**: Sales cycle, productivity
- **Revenue Metrics**: Bookings, ASP, expansion

## Core Sales Metrics

### 1. Pipeline Metrics

**Pipeline Coverage Ratio**:
```sql
-- Pipeline coverage by quarter
WITH pipeline_summary AS (
  SELECT 
    sales_rep,
    sales_segment,
    CASE 
      WHEN close_date BETWEEN CURRENT_DATE AND DATEADD('month', 3, CURRENT_DATE) THEN 'Q_Current'
      WHEN close_date BETWEEN DATEADD('month', 3, CURRENT_DATE) AND DATEADD('month', 6, CURRENT_DATE) THEN 'Q_Next'
      ELSE 'Q_Future'
    END as close_quarter,
    opportunity_stage,
    SUM(opportunity_amount) as pipeline_value,
    COUNT(*) as opportunity_count
  FROM opportunities
  WHERE status = 'open'
  GROUP BY sales_rep, sales_segment, close_quarter, opportunity_stage
),
quota_targets AS (
  SELECT 
    sales_rep,
    quarter,
    quota_amount
  FROM sales_quotas
  WHERE quarter IN ('Q_Current', 'Q_Next')
)
SELECT 
  ps.sales_segment,
  ps.close_quarter,
  SUM(ps.pipeline_value) as total_pipeline,
  SUM(qt.quota_amount) as total_quota,
  ROUND(SUM(ps.pipeline_value) / NULLIF(SUM(qt.quota_amount), 0), 2) as coverage_ratio,
  SUM(ps.opportunity_count) as total_opportunities,
  ROUND(SUM(ps.pipeline_value) / NULLIF(SUM(ps.opportunity_count), 0), 0) as avg_deal_size
FROM pipeline_summary ps
LEFT JOIN quota_targets qt 
  ON ps.sales_rep = qt.sales_rep 
  AND ps.close_quarter = qt.quarter
GROUP BY ps.sales_segment, ps.close_quarter
ORDER BY ps.sales_segment, ps.close_quarter;

**Sales Velocity**:
```sql
-- Calculate sales velocity components
WITH velocity_metrics AS (
  SELECT 
    sales_segment,
    DATE_TRUNC('month', close_date) as month,
    COUNT(*) as opportunities,
    AVG(opportunity_amount) as avg_deal_value,
    AVG(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as win_rate,
    AVG(DATEDIFF('day', created_date, close_date)) as avg_cycle_length
  FROM opportunities
  WHERE status IN ('won', 'lost')
    AND close_date >= DATEADD('month', -6, CURRENT_DATE)
  GROUP BY sales_segment, month
)
SELECT 
  sales_segment,
  month,
  opportunities,
  ROUND(avg_deal_value, 0) as avg_deal_value,
  ROUND(win_rate * 100, 1) as win_rate_pct,
  ROUND(avg_cycle_length, 0) as avg_cycle_days,
  ROUND((opportunities * avg_deal_value * win_rate) / NULLIF(avg_cycle_length, 0), 0) as sales_velocity
FROM velocity_metrics
ORDER BY month DESC, sales_velocity DESC;
```
### 2. Sales Activity Metrics

**Activity Effectiveness**:
```sql
-- Analyze activity conversion rates
WITH activity_summary AS (
  SELECT 
    sa.sales_rep,
    sa.activity_type,
    DATE_TRUNC('week', sa.activity_date) as week,
    COUNT(*) as activity_count,
    COUNT(DISTINCT sa.account_id) as accounts_touched,
    COUNT(DISTINCT o.opportunity_id) as opportunities_created,
    SUM(o.opportunity_amount) as pipeline_generated
  FROM sales_activities sa
  LEFT JOIN opportunities o 
    ON sa.account_id = o.account_id
    AND o.created_date BETWEEN sa.activity_date AND sa.activity_date + INTERVAL '30 days'
  WHERE sa.activity_date >= DATEADD('month', -3, CURRENT_DATE)
  GROUP BY sa.sales_rep, sa.activity_type, week
)
SELECT 
  activity_type,
  SUM(activity_count) as total_activities,
  SUM(accounts_touched) as unique_accounts,
  SUM(opportunities_created) as opps_created,
  ROUND(100.0 * SUM(opportunities_created) / NULLIF(SUM(activity_count), 0), 2) as opp_conversion_rate,
  ROUND(SUM(pipeline_generated) / NULLIF(SUM(activity_count), 0), 0) as pipeline_per_activity,
  ROUND(AVG(activity_count), 1) as avg_activities_per_rep_week
FROM activity_summary
GROUP BY activity_type
ORDER BY pipeline_per_activity DESC;
```
### 3. Win/Loss Analytics

**Win Rate Analysis**:
```sql
-- Detailed win rate breakdown
WITH opportunity_analysis AS (
  SELECT 
    o.opportunity_id,
    o.sales_rep,
    o.sales_segment,
    o.lead_source,
    o.competitor_involved,
    o.opportunity_amount,
    CASE 
      WHEN o.opportunity_amount < 10000 THEN 'Small (<$10K)'
      WHEN o.opportunity_amount < 50000 THEN 'Medium ($10-50K)'
      WHEN o.opportunity_amount < 100000 THEN 'Large ($50-100K)'
      ELSE 'Enterprise ($100K+)'
    END as deal_size_tier,
    o.status,
    o.loss_reason,
    DATEDIFF('day', o.created_date, o.close_date) as cycle_length
  FROM opportunities o
  WHERE o.status IN ('won', 'lost')
    AND o.close_date >= DATEADD('month', -12, CURRENT_DATE)
)
SELECT 
  sales_segment,
  deal_size_tier,
  COUNT(*) as total_opportunities,
  SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won_deals,
  ROUND(100.0 * SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
  ROUND(AVG(CASE WHEN status = 'won' THEN opportunity_amount END), 0) as avg_won_deal_size,
  ROUND(AVG(CASE WHEN status = 'won' THEN cycle_length END), 0) as avg_won_cycle_days,
  COUNT(DISTINCT CASE WHEN competitor_involved = 1 THEN opportunity_id END) as competitive_deals,
  ROUND(100.0 * SUM(CASE WHEN status = 'won' AND competitor_involved = 1 THEN 1 ELSE 0 END) / 
        NULLIF(COUNT(CASE WHEN competitor_involved = 1 THEN 1 END), 0), 1) as competitive_win_rate
FROM opportunity_analysis
GROUP BY sales_segment, deal_size_tier
ORDER BY sales_segment, 
  CASE deal_size_tier
    WHEN 'Small (<$10K)' THEN 1
    WHEN 'Medium ($10-50K)' THEN 2
    WHEN 'Large ($50-100K)' THEN 3
    WHEN 'Enterprise ($100K+)' THEN 4
  END;
```
**Loss Reason Analysis**:
```sql
-- Understand why deals are lost
WITH loss_analysis AS (
  SELECT 
    loss_reason,
    sales_segment,
    COUNT(*) as lost_deals,
    SUM(opportunity_amount) as lost_revenue,
    AVG(opportunity_amount) as avg_lost_deal_size,
    AVG(DATEDIFF('day', created_date, close_date)) as avg_cycle_to_loss
  FROM opportunities
  WHERE status = 'lost'
    AND close_date >= DATEADD('month', -6, CURRENT_DATE)
  GROUP BY loss_reason, sales_segment
)
SELECT 
  loss_reason,
  SUM(lost_deals) as total_lost_deals,
  ROUND(100.0 * SUM(lost_deals) / SUM(SUM(lost_deals)) OVER (), 1) as pct_of_losses,
  ROUND(SUM(lost_revenue), 0) as total_lost_revenue,
  ROUND(AVG(avg_lost_deal_size), 0) as avg_deal_size,
  ROUND(AVG(avg_cycle_to_loss), 0) as avg_days_to_loss
FROM loss_analysis
GROUP BY loss_reason
ORDER BY total_lost_deals DESC;
```

### 4. Sales Performance Metrics

**Quota Attainment**:
```sql
-- Individual and team quota performance
WITH performance_summary AS (
  SELECT 
    sr.sales_rep,
    sr.sales_team,
    sr.sales_segment,
    DATE_TRUNC('quarter', o.close_date) as quarter,
    SUM(CASE WHEN o.status = 'won' THEN o.opportunity_amount ELSE 0 END) as closed_won,
    sq.quota_amount,
    COUNT(DISTINCT CASE WHEN o.status = 'won' THEN o.opportunity_id END) as deals_won
  FROM sales_reps sr
  LEFT JOIN opportunities o ON sr.sales_rep = o.sales_rep
  LEFT JOIN sales_quotas sq ON sr.sales_rep = sq.sales_rep 
    AND DATE_TRUNC('quarter', o.close_date) = sq.quarter
  WHERE o.close_date >= DATEADD('quarter', -4, CURRENT_DATE)
  GROUP BY sr.sales_rep, sr.sales_team, sr.sales_segment, quarter, sq.quota_amount
)SELECT 
  quarter,
  sales_segment,
  COUNT(DISTINCT sales_rep) as rep_count,
  SUM(closed_won) as total_closed_won,
  SUM(quota_amount) as total_quota,
  ROUND(100.0 * SUM(closed_won) / NULLIF(SUM(quota_amount), 0), 1) as team_attainment_pct,
  COUNT(DISTINCT CASE WHEN closed_won >= quota_amount THEN sales_rep END) as reps_at_quota,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN closed_won >= quota_amount THEN sales_rep END) / 
        NULLIF(COUNT(DISTINCT sales_rep), 0), 1) as pct_reps_at_quota,
  ROUND(AVG(closed_won), 0) as avg_rep_bookings,
  SUM(deals_won) as total_deals_won
FROM performance_summary
GROUP BY quarter, sales_segment
ORDER BY quarter DESC, sales_segment;

### 5. Sales Efficiency Metrics

**Ramp Time Analysis**:
```sql
-- New rep productivity ramp
WITH rep_monthly_performance AS (
  SELECT 
    sr.sales_rep,
    sr.start_date,
    DATE_TRUNC('month', o.close_date) as month,
    DATEDIFF('month', sr.start_date, DATE_TRUNC('month', o.close_date)) as months_since_start,
    SUM(CASE WHEN o.status = 'won' THEN o.opportunity_amount ELSE 0 END) as monthly_bookings,
    COUNT(DISTINCT CASE WHEN o.status = 'won' THEN o.opportunity_id END) as deals_closed
  FROM sales_reps sr
  LEFT JOIN opportunities o ON sr.sales_rep = o.sales_rep
  WHERE sr.start_date >= DATEADD('month', -18, CURRENT_DATE)
  GROUP BY sr.sales_rep, sr.start_date, month
)
SELECT 
  months_since_start,
  COUNT(DISTINCT sales_rep) as rep_count,
  AVG(monthly_bookings) as avg_monthly_bookings,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_bookings) as median_monthly_bookings,
  AVG(deals_closed) as avg_deals_closed,
  SUM(CASE WHEN monthly_bookings > 0 THEN 1 ELSE 0 END) as productive_reps,
  ROUND(100.0 * SUM(CASE WHEN monthly_bookings > 0 THEN 1 ELSE 0 END) / 
        COUNT(DISTINCT sales_rep), 1) as pct_productive
FROM rep_monthly_performance
WHERE months_since_start >= 0 AND months_since_start <= 12
GROUP BY months_since_start
ORDER BY months_since_start;
```
### 6. Territory and Account Analytics

**Territory Performance**:
```sql
-- Territory coverage and penetration
WITH territory_metrics AS (
  SELECT 
    t.territory_id,
    t.territory_name,
    t.assigned_rep,
    COUNT(DISTINCT a.account_id) as total_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'customer' THEN a.account_id END) as customer_accounts,
    COUNT(DISTINCT CASE WHEN o.opportunity_id IS NOT NULL THEN a.account_id END) as accounts_with_opps,
    SUM(a.potential_value) as total_tam,
    SUM(CASE WHEN a.status = 'customer' THEN a.annual_revenue END) as captured_revenue,
    SUM(o.opportunity_amount) as open_pipeline
  FROM territories t
  LEFT JOIN accounts a ON t.territory_id = a.territory_id
  LEFT JOIN opportunities o ON a.account_id = o.account_id AND o.status = 'open'
  GROUP BY t.territory_id, t.territory_name, t.assigned_rep
)
SELECT 
  territory_name,
  assigned_rep,
  total_accounts,
  customer_accounts,
  ROUND(100.0 * customer_accounts / NULLIF(total_accounts, 0), 1) as penetration_rate,
  accounts_with_opps,
  ROUND(100.0 * accounts_with_opps / NULLIF(total_accounts - customer_accounts, 0), 1) as prospect_coverage,
  ROUND(total_tam / 1000000, 1) as tam_millions,
  ROUND(captured_revenue / 1000000, 1) as captured_revenue_millions,
  ROUND(100.0 * captured_revenue / NULLIF(total_tam, 0), 1) as tam_capture_pct,
  ROUND(open_pipeline / 1000000, 1) as pipeline_millions
FROM territory_metrics
ORDER BY total_tam DESC;
```
## Common Stakeholder Questions

### From Sales Leadership
1. "Which reps are at risk of missing quota?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which salespeople might not hit their targets this quarter? | Compare YTD performance vs quota from `sales_rep_performance` and `quota_targets` |

2. "What's our pipeline coverage for next quarter?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do we have enough deals in the pipeline to hit our revenue targets? | Calculate pipeline value vs quarterly target, factor in win rates from `pipeline_coverage_analysis` |

3. "Where are deals getting stuck in the sales process?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which sales stages have the longest delays or highest drop-off? | Analyze time spent and conversion rates by stage from `deal_stage_progression` |

4. "Which activities drive the most pipeline?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What sales actions lead to the most opportunities? | Correlate activities (calls, emails, demos) with opportunity creation from `activity_pipeline_attribution` |

5. "How effective are we at competitive deals?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What's our win rate when competing against other vendors? | Compare win rates and deal characteristics for competitive vs non-competitive deals from `competitive_analysis` |

### From Sales Operations
1. "What's the optimal territory distribution?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How should we divide up accounts among sales reps? | Analyze account value, rep capacity, and geographic factors from `territory_optimization_model` |

2. "How long does rep ramp take by segment?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How many months until new salespeople become productive? | Track bookings progression from hire date by segment from `rep_ramp_analysis` |

3. "Which tools improve sales productivity?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What sales software is actually helping reps close more deals? | Correlate tool usage with sales performance metrics from `tool_adoption_impact` |

4. "What's causing forecast inaccuracy?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Why are our sales predictions wrong? | Compare forecasted vs actual results, identify bias patterns from `forecast_variance_analysis` |

5. "How should we set quotas next year?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What are realistic and motivating sales targets? | Analyze historical performance, market growth, and capacity from `quota_modeling` |

### From Finance
1. "What's our sales efficiency ratio?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How much revenue do we generate per dollar of sales investment? | Calculate bookings divided by sales costs from `sales_efficiency_metrics` |

2. "How predictable is our bookings forecast?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How accurate are our sales predictions? | Compare forecasted vs actual bookings from `forecast_accuracy_analysis` |

3. "What's the ROI on sales headcount?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are additional salespeople paying for themselves? | Calculate incremental revenue vs cost of new hires from `sales_headcount_roi` |

4. "How does discounting impact deal size?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do discounts help or hurt our average deal value? | Analyze discount levels vs deal size and margins from `discount_impact_analysis` |

5. "What's driving commission expense variance?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Why are commission costs different than expected? | Break down commission variance by rep performance and plan changes from `commission_variance_analysis` |

### From Executive Team
1. "Can we hit our revenue targets?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Will we achieve our quarterly and annual revenue goals? | Analyze pipeline coverage, win rates, and seasonality from `revenue_forecast_model` |

2. "Where should we invest in sales?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What sales areas need more resources or attention? | Compare performance and ROI across territories, segments, and rep types from `sales_investment_analysis` |

3. "How productive is our sales team?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are our salespeople generating good returns on investment? | Calculate revenue per rep, quota attainment trends from `sales_productivity_metrics` |

4. "What's our competitive win rate?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How often do we beat competitors in deals? | Compare win rates for competitive vs non-competitive deals from `competitive_win_analysis` |

5. "Are we improving sales efficiency?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Is our sales team getting better at closing deals faster and bigger? | Track sales velocity, cycle time trends, and efficiency ratios over time from `sales_efficiency_trends` |

## Standard Sales Reports

### 1. Sales Dashboard
```sql
-- Executive sales summary
WITH current_metrics AS (
  SELECT 
    COUNT(DISTINCT CASE WHEN o.status = 'open' THEN o.opportunity_id END) as open_opportunities,
    SUM(CASE WHEN o.status = 'open' THEN o.opportunity_amount END) as total_pipeline,
    SUM(CASE WHEN o.status = 'won' AND DATE_TRUNC('month', o.close_date) = DATE_TRUNC('month', CURRENT_DATE) 
        THEN o.opportunity_amount END) as mtd_bookings,
    SUM(CASE WHEN o.status = 'won' AND DATE_TRUNC('quarter', o.close_date) = DATE_TRUNC('quarter', CURRENT_DATE) 
        THEN o.opportunity_amount END) as qtd_bookings,
    COUNT(DISTINCT o.sales_rep) as active_reps
  FROM opportunities o
  WHERE o.created_date >= DATEADD('month', -12, CURRENT_DATE)
),
targets AS (
  SELECT 
    SUM(CASE WHEN period = 'month' THEN target_amount END) as monthly_target,
    SUM(CASE WHEN period = 'quarter' THEN target_amount END) as quarterly_target
  FROM sales_targets
  WHERE period_date = DATE_TRUNC('month', CURRENT_DATE)
     OR period_date = DATE_TRUNC('quarter', CURRENT_DATE)
)
SELECT 
  cm.open_opportunities,
  ROUND(cm.total_pipeline / 1000000, 1) as pipeline_millions,
  ROUND(cm.mtd_bookings / 1000000, 1) as mtd_bookings_millions,
  ROUND(cm.qtd_bookings / 1000000, 1) as qtd_bookings_millions,
  ROUND(100.0 * cm.mtd_bookings / NULLIF(t.monthly_target, 0), 1) as mtd_attainment_pct,
  ROUND(100.0 * cm.qtd_bookings / NULLIF(t.quarterly_target, 0), 1) as qtd_attainment_pct,
  cm.active_reps,
  ROUND(cm.total_pipeline / NULLIF(cm.active_reps, 0) / 1000, 0) as pipeline_per_rep_thousands
FROM current_metrics cm
CROSS JOIN targets t;

### 2. Pipeline Movement Report
```sql
-- Week-over-week pipeline changes
WITH pipeline_snapshots AS (
  SELECT 
    DATE_TRUNC('week', snapshot_date) as week,
    stage_name,
    SUM(opportunity_amount) as stage_value,
    COUNT(*) as opportunity_count
  FROM opportunity_history
  WHERE snapshot_date >= DATEADD('week', -8, CURRENT_DATE)
  GROUP BY week, stage_name
),
pipeline_flow AS (
  SELECT 
    p1.week,
    p1.stage_name,
    p1.stage_value as current_value,
    p2.stage_value as previous_value,
    p1.stage_value - COALESCE(p2.stage_value, 0) as week_change,
    p1.opportunity_count as current_count,
    p2.opportunity_count as previous_count
  FROM pipeline_snapshots p1
  LEFT JOIN pipeline_snapshots p2 
    ON p1.stage_name = p2.stage_name 
    AND p2.week = DATEADD('week', -1, p1.week)
)SELECT 
  week,
  stage_name,
  ROUND(current_value / 1000000, 1) as current_value_millions,
  ROUND(week_change / 1000000, 1) as change_millions,
  ROUND(100.0 * week_change / NULLIF(previous_value, 0), 1) as pct_change,
  current_count as opportunities,
  current_count - COALESCE(previous_count, 0) as count_change
FROM pipeline_flow
WHERE week = DATE_TRUNC('week', CURRENT_DATE)
ORDER BY 
  CASE stage_name
    WHEN 'Prospecting' THEN 1
    WHEN 'Qualification' THEN 2
    WHEN 'Discovery' THEN 3
    WHEN 'Proposal' THEN 4
    WHEN 'Negotiation' THEN 5
    WHEN 'Closing' THEN 6
  END;

### 3. Sales Forecast Accuracy
```sql
-- Compare forecasts to actuals
WITH forecast_comparison AS (
  SELECT 
    f.forecast_date,
    f.forecast_period,
    f.sales_segment,
    f.forecast_category,
    SUM(f.forecast_amount) as forecasted,
    SUM(a.actual_amount) as actual,
    COUNT(DISTINCT f.opportunity_id) as forecasted_deals,
    COUNT(DISTINCT a.opportunity_id) as actual_deals
  FROM sales_forecasts f
  LEFT JOIN (
    SELECT 
      opportunity_id,
      close_date,
      opportunity_amount as actual_amount
    FROM opportunities
    WHERE status = 'won'
  ) a ON f.opportunity_id = a.opportunity_id 
    AND DATE_TRUNC('month', a.close_date) = f.forecast_period
  WHERE f.forecast_date >= DATEADD('month', -6, CURRENT_DATE)
    AND f.forecast_period < DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY f.forecast_date, f.forecast_period, f.sales_segment, f.forecast_category
)SELECT 
  forecast_period,
  sales_segment,
  forecast_category,
  ROUND(SUM(forecasted) / 1000000, 1) as forecasted_millions,
  ROUND(SUM(actual) / 1000000, 1) as actual_millions,
  ROUND(100.0 * (SUM(actual) - SUM(forecasted)) / NULLIF(SUM(forecasted), 0), 1) as variance_pct,
  ROUND(100.0 * SUM(actual) / NULLIF(SUM(forecasted), 0), 1) as accuracy_pct,
  SUM(forecasted_deals) as forecasted_deals,
  SUM(actual_deals) as closed_deals
FROM forecast_comparison
WHERE forecast_category IN ('Commit', 'Best Case', 'Pipeline')
GROUP BY forecast_period, sales_segment, forecast_category
ORDER BY forecast_period DESC, sales_segment, forecast_category;

## Advanced Sales Analytics Techniques

### 1. Predictive Deal Scoring
```sql
-- Score deals based on historical patterns
WITH deal_characteristics AS (
  SELECT 
    o.opportunity_id,
    o.status,
    o.opportunity_amount,
    o.sales_segment,
    -- Deal features
    DATEDIFF('day', o.created_date, CURRENT_DATE) as age_days,
    o.stage_duration_days,
    sa.activity_count_30d,
    sa.unique_contacts_engaged,
    o.executive_engaged,
    o.champion_identified,
    o.budget_confirmed,
    o.decision_criteria_understood,
    -- Outcome
    CASE WHEN o.status = 'won' THEN 1 ELSE 0 END as won
  FROM opportunities o
  LEFT JOIN (
    SELECT 
      opportunity_id,
      COUNT(*) as activity_count_30d,
      COUNT(DISTINCT contact_id) as unique_contacts_engaged
    FROM sales_activities
    WHERE activity_date >= DATEADD('day', -30, CURRENT_DATE)
    GROUP BY opportunity_id
  ) sa ON o.opportunity_id = sa.opportunity_id
  WHERE o.status IN ('won', 'lost')
    AND o.close_date >= DATEADD('month', -12, CURRENT_DATE)
)SELECT 
  CASE 
    WHEN executive_engaged + champion_identified + budget_confirmed + decision_criteria_understood >= 3 THEN 'High'
    WHEN executive_engaged + champion_identified + budget_confirmed + decision_criteria_understood >= 2 THEN 'Medium'
    ELSE 'Low'
  END as deal_score,
  COUNT(*) as deal_count,
  AVG(won) * 100 as historical_win_rate,
  AVG(opportunity_amount) as avg_deal_size,
  AVG(age_days) as avg_age_at_close,
  AVG(activity_count_30d) as avg_activities,
  AVG(unique_contacts_engaged) as avg_contacts
FROM deal_characteristics
GROUP BY deal_score
ORDER BY historical_win_rate DESC;

### 2. Sales Team Optimization
```sql
-- Analyze optimal team composition
WITH team_performance AS (
  SELECT 
    t.team_name,
    t.team_size,
    t.avg_tenure_months,
    t.sdr_ae_ratio,
    COUNT(DISTINCT o.opportunity_id) as opportunities_created,
    SUM(CASE WHEN o.status = 'won' THEN o.opportunity_amount END) as revenue_closed,
    AVG(CASE WHEN o.status IN ('won', 'lost') THEN 
        DATEDIFF('day', o.created_date, o.close_date) END) as avg_cycle_time,
    AVG(CASE WHEN o.status = 'won' THEN 1 ELSE 0 END) as win_rate
  FROM sales_teams t
  JOIN sales_reps sr ON t.team_id = sr.team_id
  JOIN opportunities o ON sr.sales_rep = o.sales_rep
  WHERE o.close_date >= DATEADD('month', -6, CURRENT_DATE)
  GROUP BY t.team_name, t.team_size, t.avg_tenure_months, t.sdr_ae_ratio
)
SELECT 
  team_name,
  team_size,
  avg_tenure_months,
  sdr_ae_ratio,
  opportunities_created,
  ROUND(revenue_closed / 1000000, 1) as revenue_millions,
  ROUND(revenue_closed / team_size / 1000000, 2) as revenue_per_rep_millions,
  ROUND(avg_cycle_time, 0) as avg_cycle_days,
  ROUND(win_rate * 100, 1) as win_rate_pct
FROM team_performance
ORDER BY revenue_per_rep_millions DESC;
```
### 3. Account Prioritization Model
```sql
-- Identify high-value account opportunities
WITH account_scoring AS (
  SELECT 
    a.account_id,
    a.account_name,
    a.industry,
    a.employee_count,
    a.annual_revenue,
    -- Fit scores
    CASE 
      WHEN a.industry IN ('Technology', 'Finance', 'Healthcare') THEN 20
      ELSE 10
    END as industry_fit_score,
    CASE 
      WHEN a.employee_count >= 1000 THEN 20
      WHEN a.employee_count >= 100 THEN 15
      ELSE 5
    END as size_fit_score,
    -- Engagement scores
    COALESCE(e.engagement_score, 0) as engagement_score,
    COALESCE(e.exec_meetings_count, 0) as exec_engagement,
    -- Revenue potential
    a.annual_revenue * 0.05 as potential_deal_size, -- Assume 5% wallet share
    COALESCE(h.historical_spend, 0) as historical_spend
  FROM accounts a
  LEFT JOIN (
    SELECT 
      account_id,
      SUM(activity_score) as engagement_score,
      COUNT(DISTINCT CASE WHEN contact_title LIKE '%VP%' OR contact_title LIKE '%Chief%' 
            THEN activity_id END) as exec_meetings_count
    FROM account_engagement
    WHERE activity_date >= DATEADD('month', -3, CURRENT_DATE)
    GROUP BY account_id
  ) e ON a.account_id = e.account_id
  LEFT JOIN (
    SELECT 
      account_id,
      SUM(opportunity_amount) as historical_spend
    FROM opportunities
    WHERE status = 'won'
    GROUP BY account_id
  ) h ON a.account_id = h.account_id
  WHERE a.status = 'prospect'
)SELECT 
  account_name,
  industry,
  employee_count,
  industry_fit_score + size_fit_score + engagement_score as total_score,
  ROUND(potential_deal_size / 1000, 0) as potential_deal_thousands,
  exec_engagement as exec_meetings,
  CASE 
    WHEN industry_fit_score + size_fit_score + engagement_score >= 60 THEN 'Tier 1'
    WHEN industry_fit_score + size_fit_score + engagement_score >= 40 THEN 'Tier 2'
    ELSE 'Tier 3'
  END as account_tier
FROM account_scoring
WHERE potential_deal_size > 50000
ORDER BY total_score DESC, potential_deal_size DESC
LIMIT 50;

## Sales Analytics Best Practices

### 1. Data Quality Standards
- **CRM Hygiene**: Enforce consistent data entry
- **Stage Definitions**: Clear criteria for each stage
- **Activity Tracking**: Comprehensive logging
- **Regular Updates**: Daily opportunity reviews

### 2. Forecasting Excellence
- **Multiple Methods**: Bottom-up and top-down
- **Historical Calibration**: Adjust for bias
- **Scenario Planning**: Best/expected/worst cases
- **Weekly Reviews**: Regular forecast updates

### 3. Performance Management
- **Balanced Metrics**: Activity + outcomes
- **Fair Territories**: Equal opportunity distribution
- **Regular Coaching**: Data-driven feedback
- **Recognition Systems**: Celebrate wins

### 4. Process Optimization
- **Bottleneck Analysis**: Where deals stall
- **A/B Testing**: Sales methodology experiments
- **Tool Adoption**: Measure tool effectiveness
- **Continuous Improvement**: Regular process reviews
## Common Pitfalls to Avoid

1. **Sandbagging**: Reps hiding deals for future quarters
2. **Happy Ears**: Over-optimistic deal assessment
3. **Activity Vanity**: Volume without quality
4. **Forecast Padding**: Artificial pipeline inflation
5. **Territory Conflicts**: Unclear account ownership

## Key Takeaways

1. **Pipeline Predicts Revenue**: Maintain 3-4x coverage
2. **Velocity Matters**: Faster cycles = more revenue
3. **Quality > Quantity**: Better opportunities beat more opportunities
4. **Early Engagement**: Executive involvement predicts success
5. **Data Discipline**: Clean CRM data enables insights

---

*Next: [Module 7 - Operations Analytics](07-operations-analytics.md)*