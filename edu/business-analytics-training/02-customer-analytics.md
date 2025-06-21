# Module 2: Customer Analytics

## Overview

Customer analytics focuses on understanding customer behavior, health, and value throughout their lifecycle. In SaaS businesses, customer success directly drives revenue retention and expansion, making these metrics critical for sustainable growth.

## The Customer Lifecycle

### Stages of Customer Journey

1. **Acquisition**: First touch to closed deal
2. **Onboarding**: Contract signing to first value
3. **Adoption**: Initial usage to regular engagement
4. **Expansion**: Growing usage and spend
5. **Renewal**: Subscription continuation decisions
6. **Advocacy**: Referrals and testimonials

### Customer Segmentation Strategies

**Firmographic Segmentation**:
- Company size (employees, revenue)
- Industry vertical
- Geographic location
- Technology stack

**Behavioral Segmentation**:
- Usage patterns
- Feature adoption
- Engagement frequency
- Support interactions

**Value-Based Segmentation**:
- Revenue tier
- Growth potential
- Strategic importance
- Profitability

## Core Customer Metrics

### 1. Customer Health Score

**Definition**: Composite metric predicting customer retention likelihood
**Common Components**:
```
Health Score = W1×Usage + W2×Engagement + W3×Support + W4×Growth + W5×Satisfaction
```

**Scoring Factors**:
- **Usage Metrics**: Login frequency, feature utilization, data volume
- **Engagement**: User activity, feature adoption rate, API calls
- **Support Health**: Ticket volume, resolution satisfaction, escalations
- **Growth Indicators**: User additions, usage expansion, feature requests
- **Satisfaction**: NPS scores, survey responses, feedback sentiment

**Implementation Example**:
```sql
-- Calculate customer health score
WITH usage_score AS (
  SELECT 
    customer_id,
    CASE 
      WHEN days_active_last_30 >= 25 THEN 100
      WHEN days_active_last_30 >= 20 THEN 80
      WHEN days_active_last_30 >= 15 THEN 60
      WHEN days_active_last_30 >= 10 THEN 40
      ELSE 20
    END as usage_score
  FROM customer_usage_summary
),
feature_score AS (
  SELECT 
    customer_id,
    (features_used::FLOAT / total_features) * 100 as feature_adoption_score
  FROM customer_feature_adoption
)
SELECT 
  c.customer_id,
  c.customer_name,
  ROUND(
    (u.usage_score * 0.35) + 
    (f.feature_adoption_score * 0.25) + 
    (c.nps_score * 0.20) + 
    (c.support_satisfaction * 0.10) +
    (CASE WHEN c.is_growing THEN 100 ELSE 50 END * 0.10)
  ) as health_score
FROM customers c
JOIN usage_score u ON c.customer_id = u.customer_id
JOIN feature_score f ON c.customer_id = f.customer_id;
```
### 2. Net Promoter Score (NPS)

**Definition**: Likelihood of customer recommendation

**Calculation**:
```
NPS = % Promoters (9-10) - % Detractors (0-6)
```

**Categories**:
- **Promoters (9-10)**: Enthusiastic advocates
- **Passives (7-8)**: Satisfied but vulnerable
- **Detractors (0-6)**: Unhappy, churn risk

**Business Applications**:
- **Benchmark Performance**: Compare against industry standards
- **Identify Champions**: Find customers for case studies
- **Risk Detection**: Prioritize detractor outreach
- **Product Feedback**: Correlate scores with feature usage

### 3. Customer Effort Score (CES)

**Definition**: Ease of accomplishing tasks with your product

**Common Question**: "How easy was it to [complete specific task]?"

**Scale**: 1 (Very Difficult) to 7 (Very Easy)

**Use Cases**:
- **Onboarding Optimization**: Identify friction points
- **Support Improvement**: Measure resolution difficulty
- **Feature Usability**: Assess new feature adoption
- **Process Efficiency**: Streamline customer workflows

### 4. Time to Value (TTV)

**Definition**: Duration from purchase to achieving first meaningful outcome
**Measurement Approaches**:
```sql
-- Calculate time to first value
WITH first_value_events AS (
  SELECT 
    c.customer_id,
    c.contract_start_date,
    MIN(e.event_date) as first_value_date,
    e.value_type
  FROM customers c
  JOIN value_events e ON c.customer_id = e.customer_id
  WHERE e.event_type IN ('first_report_created', 'first_integration_complete', 'first_roi_achieved')
  GROUP BY c.customer_id, c.contract_start_date, e.value_type
)
SELECT 
  value_type,
  AVG(DATEDIFF('day', contract_start_date, first_value_date)) as avg_days_to_value,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF('day', contract_start_date, first_value_date)) as median_days_to_value,
  COUNT(*) as customers_achieved
FROM first_value_events
GROUP BY value_type;
```

### 5. Product Adoption Metrics

**Feature Adoption Rate**:
```
Adoption Rate = (Users Using Feature / Total Users) × 100
```

**Adoption Depth**:
- **Breadth**: Number of features used
- **Depth**: Intensity of feature usage
- **Frequency**: How often features are accessed
- **Stickiness**: Daily Active / Monthly Active Users
### 6. Customer Engagement Metrics

**Daily/Monthly Active Users (DAU/MAU)**:
```sql
-- Calculate DAU/MAU ratio (stickiness)
WITH daily_active AS (
  SELECT 
    DATE_TRUNC('day', activity_date) as day,
    COUNT(DISTINCT user_id) as dau
  FROM user_activities
  WHERE activity_date >= DATEADD('day', -30, CURRENT_DATE)
  GROUP BY 1
),
monthly_active AS (
  SELECT 
    DATE_TRUNC('month', activity_date) as month,
    COUNT(DISTINCT user_id) as mau
  FROM user_activities
  WHERE activity_date >= DATEADD('month', -1, CURRENT_DATE)
  GROUP BY 1
)
SELECT 
  d.day,
  d.dau,
  m.mau,
  ROUND(100.0 * d.dau / m.mau, 1) as stickiness_ratio
FROM daily_active d
JOIN monthly_active m ON DATE_TRUNC('month', d.day) = m.month
ORDER BY d.day DESC;
```

**Session Metrics**:
- **Session Duration**: Average time per visit
- **Session Frequency**: Visits per user per time period
- **Pages/Actions per Session**: Engagement depth
- **Bounce Rate**: Single-action sessions
### 7. Churn Risk Indicators

**Early Warning Signals**:
- Declining login frequency
- Reduced feature usage
- Increasing support tickets
- Failed payment attempts
- Key user departures
- Contract non-renewal discussions

**Churn Prediction Model**:
```sql
-- Identify at-risk customers
WITH usage_trends AS (
  SELECT 
    customer_id,
    AVG(CASE WHEN week_num <= 4 THEN weekly_logins ELSE NULL END) as recent_avg_logins,
    AVG(CASE WHEN week_num BETWEEN 5 AND 8 THEN weekly_logins ELSE NULL END) as previous_avg_logins,
    AVG(CASE WHEN week_num <= 4 THEN features_used ELSE NULL END) as recent_features,
    AVG(CASE WHEN week_num BETWEEN 5 AND 8 THEN features_used ELSE NULL END) as previous_features
  FROM (
    SELECT 
      customer_id,
      WEEK(activity_date) as week_num,
      COUNT(DISTINCT user_id) as weekly_logins,
      COUNT(DISTINCT feature_name) as features_used
    FROM user_activities
    WHERE activity_date >= DATEADD('week', -8, CURRENT_DATE)
    GROUP BY 1, 2
  ) weekly_stats
  GROUP BY customer_id
),
support_trends AS (
  SELECT 
    customer_id,
    COUNT(*) as recent_tickets,
    AVG(satisfaction_score) as avg_satisfaction
  FROM support_tickets
  WHERE created_date >= DATEADD('month', -1, CURRENT_DATE)
  GROUP BY customer_id
)SELECT 
  c.customer_id,
  c.customer_name,
  c.mrr,
  CASE 
    WHEN ut.recent_avg_logins < ut.previous_avg_logins * 0.5 THEN 'High'
    WHEN ut.recent_avg_logins < ut.previous_avg_logins * 0.75 THEN 'Medium'
    WHEN st.recent_tickets > 5 AND st.avg_satisfaction < 3 THEN 'Medium'
    ELSE 'Low'
  END as churn_risk_level,
  ROUND((ut.recent_avg_logins - ut.previous_avg_logins) / NULLIF(ut.previous_avg_logins, 0) * 100, 1) as login_change_pct,
  st.recent_tickets,
  st.avg_satisfaction
FROM customers c
LEFT JOIN usage_trends ut ON c.customer_id = ut.customer_id
LEFT JOIN support_trends st ON c.customer_id = st.customer_id
WHERE c.status = 'active'
ORDER BY churn_risk_level DESC, c.mrr DESC;

## Common Stakeholder Questions

### From Customer Success Leadership
1. "Which customers need immediate attention?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Show me customers at highest risk of churning | `SELECT * FROM customer_health_scores WHERE health_score < 50 ORDER BY mrr DESC` |

2. "What's driving the change in customer health scores?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Why are customer satisfaction metrics changing? | Compare health score components over time: usage trends, support tickets, NPS changes from `health_score_history` |

3. "How effective are our onboarding programs?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are new customers becoming successful faster? | Measure time-to-value by onboarding type, compare activation rates from `onboarding_completions` |

4. "Which customers are expansion candidates?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Who should we approach for upsells? | Filter `customers` for high health scores + usage growth + recent feature adoption |

5. "What's our coverage model efficiency?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are our customer success managers productive? | Calculate customers per CSM, health score improvements, retention rates by CSM from `cs_assignments` |

### From Product Management
1. "Which features drive the most engagement?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What product capabilities keep users most active? | Analyze `feature_usage` events by frequency, duration, return visits |

2. "How quickly do users adopt new features?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How fast do users start using new functionality? | Calculate time between feature release and first usage from `feature_adoption_events` |

3. "What's the correlation between feature usage and retention?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do certain features predict if customers will stay? | Join `feature_usage` with `customer_churn_events`, run correlation analysis |

4. "Which user personas are most successful?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What types of users get the most value from our product? | Segment users by behavior patterns, compare success metrics by segment |

5. "Where do users struggle in the product?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What features or workflows cause problems? | Analyze support tickets, session recordings, feature abandonment from `user_struggles` |
### From Executive Team
1. "What percentage of our revenue is at risk?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How much of our revenue could we lose? | Sum MRR from customers with health scores below threshold: `SELECT sum(mrr) FROM customers WHERE health_score < 60` |

2. "How are we performing against customer satisfaction targets?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are we meeting our customer happiness goals? | Compare current vs target NPS, CSAT scores from `customer_satisfaction_metrics` |

3. "What's the ROI of our customer success investments?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are our customer success efforts paying off? | Calculate retained revenue vs CS costs, measure expansion driven by CS activities |

4. "Which segments have the highest lifetime value?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What types of customers are most valuable? | Group customers by segment, calculate average LTV from `customer_ltv_by_segment` |

5. "How does customer health correlate with revenue growth?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do healthier customers grow their spending more? | Correlate health score changes with MRR growth from `customer_health_revenue_trends` |

### From Sales Team
1. "Which customers are ready for upsell conversations?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Who should we approach for expansion deals? | Filter `customers` WHERE health_score > 70 AND usage_growth > 0.15 AND feature_adoption > 0.6 |

2. "What usage patterns indicate expansion potential?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What behaviors suggest customers will buy more? | Look for increasing API calls, user additions, feature adoption from `usage_expansion_signals` |

3. "How do different onboarding approaches impact retention?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which onboarding methods lead to better customer success? | Compare retention rates by onboarding_type from `customer_onboarding_outcomes` |

4. "Which customer segments should we target?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What types of companies convert best and stay longest? | Analyze conversion rates and LTV by segment from `segment_performance_metrics` |

5. "What features resonate most with prospects?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which capabilities drive the most interest in sales? | Track demo requests, trial usage, and feature questions from `prospect_engagement` |

## Standard Customer Analytics Reports

### 1. Customer Health Dashboard
```sql
-- Executive customer health summary
WITH health_summary AS (
  SELECT 
    CASE 
      WHEN health_score >= 80 THEN 'Healthy'
      WHEN health_score >= 60 THEN 'Neutral'
      ELSE 'At Risk'
    END as health_category,
    COUNT(*) as customer_count,
    SUM(mrr) as total_mrr,
    AVG(health_score) as avg_score
  FROM customer_health_scores
  WHERE status = 'active'
  GROUP BY 1
)
SELECT 
  health_category,
  customer_count,
  ROUND(total_mrr, 0) as total_mrr,
  ROUND(100.0 * total_mrr / SUM(total_mrr) OVER (), 1) as mrr_percentage,
  ROUND(avg_score, 1) as avg_health_score
FROM health_summary
ORDER BY 
  CASE health_category
    WHEN 'Healthy' THEN 1
    WHEN 'Neutral' THEN 2
    WHEN 'At Risk' THEN 3
  END;
```
### 2. Feature Adoption Report
```sql
-- Feature adoption trends and impact
WITH feature_cohorts AS (
  SELECT 
    f.feature_name,
    f.launch_date,
    COUNT(DISTINCT u.customer_id) as adopting_customers,
    COUNT(DISTINCT CASE WHEN u.first_use_date <= f.launch_date + INTERVAL '30 days' 
          THEN u.customer_id END) as early_adopters,
    AVG(DATEDIFF('day', f.launch_date, u.first_use_date)) as avg_days_to_adopt
  FROM features f
  LEFT JOIN feature_usage u ON f.feature_id = u.feature_id
  GROUP BY f.feature_name, f.launch_date
),
retention_impact AS (
  SELECT 
    u.feature_id,
    AVG(CASE WHEN u.customer_id IN (SELECT customer_id FROM churned_customers) 
        THEN 0 ELSE 1 END) as retention_rate
  FROM feature_usage u
  GROUP BY u.feature_id
)
SELECT 
  fc.feature_name,
  fc.launch_date,
  fc.adopting_customers,
  ROUND(100.0 * fc.early_adopters / NULLIF(fc.adopting_customers, 0), 1) as early_adoption_rate,
  fc.avg_days_to_adopt,
  ROUND(r.retention_rate * 100, 1) as user_retention_rate
FROM feature_cohorts fc
LEFT JOIN retention_impact r ON fc.feature_name = r.feature_id
ORDER BY fc.launch_date DESC;
```
### 3. Customer Journey Analysis
```sql
-- Customer lifecycle stage progression
WITH stage_transitions AS (
  SELECT 
    customer_id,
    lifecycle_stage,
    stage_start_date,
    LEAD(lifecycle_stage) OVER (PARTITION BY customer_id ORDER BY stage_start_date) as next_stage,
    LEAD(stage_start_date) OVER (PARTITION BY customer_id ORDER BY stage_start_date) as next_stage_date
  FROM customer_lifecycle_history
),
stage_metrics AS (
  SELECT 
    lifecycle_stage,
    next_stage,
    COUNT(*) as transitions,
    AVG(DATEDIFF('day', stage_start_date, next_stage_date)) as avg_days_in_stage,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF('day', stage_start_date, next_stage_date)) as median_days
  FROM stage_transitions
  WHERE next_stage IS NOT NULL
  GROUP BY lifecycle_stage, next_stage
)
SELECT 
  lifecycle_stage as from_stage,
  next_stage as to_stage,
  transitions,
  ROUND(avg_days_in_stage, 1) as avg_days,
  ROUND(median_days, 1) as median_days,
  ROUND(100.0 * transitions / SUM(transitions) OVER (PARTITION BY lifecycle_stage), 1) as transition_rate
FROM stage_metrics
ORDER BY lifecycle_stage, transitions DESC;
```

## Advanced Customer Analytics Techniques

### 1. Cohort Analysis
- **Acquisition Cohorts**: Group by sign-up month
- **Behavioral Cohorts**: Group by first action taken
- **Revenue Cohorts**: Group by initial contract value
- **Product Cohorts**: Group by initial plan type
### 2. Predictive Analytics
```sql
-- Customer expansion prediction based on usage patterns
WITH usage_growth AS (
  SELECT 
    customer_id,
    current_month_usage,
    prev_month_usage,
    (current_month_usage - prev_month_usage) / NULLIF(prev_month_usage, 0) as usage_growth_rate,
    current_users,
    max_users_allowed,
    features_adopted,
    total_features_available
  FROM customer_usage_summary
),
expansion_indicators AS (
  SELECT 
    customer_id,
    CASE 
      WHEN usage_growth_rate > 0.2 THEN 1 ELSE 0 
    END as high_usage_growth,
    CASE 
      WHEN current_users::FLOAT / max_users_allowed > 0.8 THEN 1 ELSE 0 
    END as near_user_limit,
    CASE 
      WHEN features_adopted::FLOAT / total_features_available > 0.7 THEN 1 ELSE 0 
    END as high_feature_adoption,
    usage_growth_rate,
    current_users::FLOAT / max_users_allowed as user_utilization,
    features_adopted::FLOAT / total_features_available as feature_utilization
  FROM usage_growth
)
SELECT 
  customer_id,
  high_usage_growth + near_user_limit + high_feature_adoption as expansion_score,
  usage_growth_rate,
  ROUND(user_utilization * 100, 1) as user_utilization_pct,
  ROUND(feature_utilization * 100, 1) as feature_adoption_pct,
  CASE 
    WHEN high_usage_growth + near_user_limit + high_feature_adoption >= 2 THEN 'High'
    WHEN high_usage_growth + near_user_limit + high_feature_adoption = 1 THEN 'Medium'
    ELSE 'Low'
  END as expansion_likelihood
FROM expansion_indicators
ORDER BY expansion_score DESC, usage_growth_rate DESC;
```
### 3. Customer Lifetime Value Modeling
```sql
-- Advanced CLV calculation with cohort-based retention
WITH cohort_retention AS (
  SELECT 
    cohort_month,
    months_since_start,
    retention_rate
  FROM monthly_cohort_retention
),
revenue_per_customer AS (
  SELECT 
    cohort_month,
    months_since_start,
    AVG(mrr) as avg_mrr,
    AVG(gross_margin_pct) as avg_margin
  FROM cohort_revenue_summary
  GROUP BY cohort_month, months_since_start
),
clv_calculation AS (
  SELECT 
    r.cohort_month,
    SUM(
      r.avg_mrr * 
      r.avg_margin * 
      c.retention_rate * 
      POWER(1 + 0.10, -r.months_since_start) -- 10% annual discount rate
    ) as cohort_clv
  FROM revenue_per_customer r
  JOIN cohort_retention c 
    ON r.cohort_month = c.cohort_month 
    AND r.months_since_start = c.months_since_start
  WHERE r.months_since_start <= 60 -- 5-year window
  GROUP BY r.cohort_month
)
SELECT 
  cohort_month,
  ROUND(cohort_clv, 2) as customer_lifetime_value,
  RANK() OVER (ORDER BY cohort_clv DESC) as clv_rank
FROM clv_calculation
ORDER BY cohort_month DESC;
```

## Key Takeaways

1. **Health Scores are Composite**: No single metric tells the full story
2. **Engagement Predicts Retention**: Usage patterns reveal future behavior
3. **Segmentation is Critical**: Different customers need different strategies
4. **Early Intervention Matters**: Catching issues early dramatically improves outcomes
5. **Value Realization is Key**: Time to first value strongly correlates with long-term success

---

*Next: [Module 3 - Revenue Analytics](03-revenue-analytics.md)*