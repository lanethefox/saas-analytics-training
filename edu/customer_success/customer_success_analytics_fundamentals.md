# Customer Success Analytics Fundamentals

## Module Overview

This module covers essential customer success analytics techniques for B2B SaaS companies. You'll learn to predict and prevent churn, measure customer health, optimize support operations, and identify expansion opportunities that drive net revenue retention.

## Learning Objectives

By completing this module, you will be able to:
1. Build comprehensive customer health scoring models
2. Develop churn prediction frameworks using behavioral data
3. Analyze customer journey stages and intervention points
4. Calculate and optimize key CS metrics (NRR, GRR, CLV)
5. Design proactive customer success playbooks
6. Present retention strategies to executive stakeholders

## 1. Introduction to Customer Success Analytics

### The Strategic Role of CS Analytics

In B2B SaaS, customer success analytics drives:
- **Revenue Protection**: Preventing churn saves 5-25x vs. new acquisition
- **Growth Acceleration**: Expansion revenue from existing customers
- **Product Development**: Usage insights inform roadmap
- **Operational Efficiency**: Proactive vs. reactive support

### Key Stakeholders

**Primary Users:**
- Chief Customer Officer
- VP of Customer Success
- Customer Success Managers (CSMs)
- Support Team Leaders

**Secondary Users:**
- Product Team (usage insights)
- Sales (expansion opportunities)
- Finance (revenue forecasting)
- Executive Team (retention strategy)

## 2. Core Customer Success Metrics

### Retention Metrics

**Gross Revenue Retention (GRR)**
- Definition: % of revenue retained excluding expansion
- Formula: (Starting MRR - Churned MRR - Contraction MRR) / Starting MRR
- Benchmark: 90%+ for best-in-class B2B SaaS

```sql
WITH mrr_changes AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(CASE WHEN change_type = 'churn' THEN -amount ELSE 0 END) as churned_mrr,
        SUM(CASE WHEN change_type = 'contraction' THEN -amount ELSE 0 END) as contraction_mrr
    FROM mrr_movements
    WHERE date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', date)
),
starting_mrr AS (
    SELECT 
        month,
        LAG(total_mrr) OVER (ORDER BY month) as starting_mrr
    FROM monthly_mrr
)
SELECT 
    m.month,
    s.starting_mrr,
    m.churned_mrr,
    m.contraction_mrr,
    (s.starting_mrr + m.churned_mrr + m.contraction_mrr) / s.starting_mrr * 100 as grr_percentage
FROM mrr_changes m
JOIN starting_mrr s ON m.month = s.month
WHERE s.starting_mrr > 0;
```

**Net Revenue Retention (NRR)**
- Definition: % of revenue retained including expansion
- Formula: (Starting MRR - Churned MRR - Contraction MRR + Expansion MRR) / Starting MRR
- Benchmark: 110%+ indicates healthy growth

**Logo Retention**
- Definition: % of customers retained
- Important for customer count focused businesses
- Often lower than revenue retention (land-and-expand model)

### Customer Health Metrics

**Health Score Components**
```sql
-- Multi-factor health score calculation
WITH health_factors AS (
    SELECT 
        c.customer_id,
        -- Product usage (40% weight)
        CASE 
            WHEN u.days_active_last_30 >= 25 THEN 100
            WHEN u.days_active_last_30 >= 15 THEN 70
            WHEN u.days_active_last_30 >= 5 THEN 40
            ELSE 0
        END * 0.4 as usage_score,
        
        -- Feature adoption (20% weight)
        u.features_used * 100.0 / 10 * 0.2 as feature_score,  -- Assuming 10 key features
        
        -- Support sentiment (20% weight)
        CASE 
            WHEN s.avg_csat >= 4.5 THEN 100
            WHEN s.avg_csat >= 3.5 THEN 70
            WHEN s.avg_csat >= 2.5 THEN 40
            ELSE 0
        END * 0.2 as support_score,
        
        -- Engagement (20% weight)
        CASE 
            WHEN e.last_business_review <= 30 THEN 100
            WHEN e.last_business_review <= 90 THEN 70
            ELSE 40
        END * 0.2 as engagement_score
        
    FROM customers c
    LEFT JOIN usage_summary u ON c.customer_id = u.customer_id
    LEFT JOIN support_metrics s ON c.customer_id = s.customer_id
    LEFT JOIN engagement_tracking e ON c.customer_id = e.customer_id
)
SELECT 
    customer_id,
    usage_score + feature_score + support_score + engagement_score as health_score,
    CASE 
        WHEN usage_score + feature_score + support_score + engagement_score >= 80 THEN 'Healthy'
        WHEN usage_score + feature_score + support_score + engagement_score >= 60 THEN 'At Risk'
        ELSE 'Critical'
    END as health_category
FROM health_factors;
```

### Engagement Metrics

**Product Usage Indicators**
- Daily/Monthly Active Users (DAU/MAU)
- Feature adoption rate
- Time to value (first key action)
- Depth of usage (power users)

**Relationship Indicators**
- CSM touchpoint frequency
- Business review attendance
- Support ticket patterns
- Training participation

## 3. Churn Prediction and Prevention

### Early Warning Signals

**Behavioral Indicators**
```sql
-- Identify customers showing churn risk signals
WITH usage_trends AS (
    SELECT 
        customer_id,
        -- Usage decline
        AVG(CASE WHEN period = 'current' THEN daily_active_users END) as current_usage,
        AVG(CASE WHEN period = 'previous' THEN daily_active_users END) as previous_usage,
        -- Login frequency drop
        COUNT(DISTINCT CASE WHEN period = 'current' THEN date END) as current_active_days,
        COUNT(DISTINCT CASE WHEN period = 'previous' THEN date END) as previous_active_days
    FROM (
        SELECT 
            customer_id,
            date,
            daily_active_users,
            CASE 
                WHEN date >= CURRENT_DATE - INTERVAL '30 days' THEN 'current'
                WHEN date >= CURRENT_DATE - INTERVAL '60 days' THEN 'previous'
            END as period
        FROM daily_usage
        WHERE date >= CURRENT_DATE - INTERVAL '60 days'
    ) t
    GROUP BY customer_id
),
risk_signals AS (
    SELECT 
        u.customer_id,
        -- Usage decline > 30%
        (u.previous_usage - u.current_usage) / NULLIF(u.previous_usage, 0) > 0.3 as usage_decline,
        -- Support tickets increasing
        s.recent_tickets > s.historical_avg_tickets * 1.5 as support_spike,
        -- No executive engagement
        e.last_exec_meeting > 180 as no_exec_engagement,
        -- Contract renewal approaching
        c.days_until_renewal < 90 as renewal_approaching
    FROM usage_trends u
    LEFT JOIN support_patterns s ON u.customer_id = s.customer_id
    LEFT JOIN engagement_history e ON u.customer_id = e.customer_id
    LEFT JOIN contracts c ON u.customer_id = c.customer_id
)
SELECT 
    customer_id,
    usage_decline::int + support_spike::int + no_exec_engagement::int + renewal_approaching::int as risk_score,
    ARRAY_REMOVE(ARRAY[
        CASE WHEN usage_decline THEN 'Usage Decline' END,
        CASE WHEN support_spike THEN 'Support Issues' END,
        CASE WHEN no_exec_engagement THEN 'Low Engagement' END,
        CASE WHEN renewal_approaching THEN 'Renewal Risk' END
    ], NULL) as risk_factors
FROM risk_signals
WHERE usage_decline OR support_spike OR no_exec_engagement OR renewal_approaching
ORDER BY risk_score DESC;
```

### Churn Prediction Model

**Simple Logistic Regression Features**
1. Usage trend (30-day change)
2. Support ticket trend
3. Feature adoption %
4. Contract value
5. Industry vertical
6. Time since last QBR
7. NPS/CSAT scores
8. Payment history

### Intervention Playbooks

**Risk-Based Interventions**
| Risk Level | Triggers | Actions | Owner | Timeline |
|-----------|----------|---------|--------|-----------|
| Critical | Health < 40, Usage -50% | Executive call, Success plan | VP CS | 48 hours |
| High | Health 40-60, Multiple risks | CSM review, Training offer | CSM | 1 week |
| Medium | Health 60-80, Single risk | Automated tips, Check-in | CS Ops | 2 weeks |
| Low | Health > 80 | Regular cadence | CSM | Monthly |

## 4. Customer Journey Analytics

### Journey Stages

**Typical B2B SaaS Customer Journey**
1. **Onboarding** (0-90 days)
   - First value realization
   - Initial training completion
   - Key integration setup

2. **Adoption** (3-6 months)
   - Increasing usage
   - Feature exploration
   - Process integration

3. **Value Realization** (6-12 months)
   - ROI achievement
   - Business impact
   - Expansion readiness

4. **Growth** (12+ months)
   - Additional use cases
   - Seat expansion
   - Advocacy development

### Time-to-Value Analysis

```sql
-- Analyze time to key milestones
WITH milestone_achievement AS (
    SELECT 
        c.customer_id,
        c.created_date as start_date,
        MIN(CASE WHEN event_type = 'first_integration' THEN event_date END) as first_integration,
        MIN(CASE WHEN event_type = 'first_report_created' THEN event_date END) as first_report,
        MIN(CASE WHEN event_type = 'team_invited' THEN event_date END) as team_expansion,
        MIN(CASE WHEN event_type = 'api_used' THEN event_date END) as api_adoption
    FROM customers c
    LEFT JOIN customer_events e ON c.customer_id = e.customer_id
    GROUP BY c.customer_id, c.created_date
)
SELECT 
    customer_segment,
    AVG(first_integration - start_date) as avg_days_to_integration,
    AVG(first_report - start_date) as avg_days_to_first_report,
    AVG(team_expansion - start_date) as avg_days_to_team_expansion,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY first_integration - start_date) as median_integration_time
FROM milestone_achievement m
JOIN customers c ON m.customer_id = c.customer_id
GROUP BY customer_segment;
```

### Adoption Patterns

**Feature Adoption Funnel**
```sql
WITH feature_adoption AS (
    SELECT 
        cohort_month,
        months_since_start,
        feature_name,
        COUNT(DISTINCT customer_id) as customers_adopted,
        COUNT(DISTINCT customer_id) * 100.0 / 
            FIRST_VALUE(COUNT(DISTINCT customer_id)) OVER (
                PARTITION BY cohort_month, feature_name 
                ORDER BY months_since_start
            ) as adoption_rate
    FROM customer_feature_adoption
    GROUP BY cohort_month, months_since_start, feature_name
)
SELECT * FROM feature_adoption
ORDER BY cohort_month, feature_name, months_since_start;
```

## 5. Support Analytics

### Ticket Analysis

**Support Metrics Dashboard**
```sql
-- Support efficiency metrics
WITH ticket_metrics AS (
    SELECT 
        DATE_TRUNC('week', created_date) as week,
        COUNT(*) as total_tickets,
        AVG(first_response_time) as avg_first_response,
        AVG(resolution_time) as avg_resolution_time,
        COUNT(CASE WHEN priority = 'High' THEN 1 END) as high_priority_tickets,
        AVG(satisfaction_score) as avg_csat
    FROM support_tickets
    WHERE created_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY DATE_TRUNC('week', created_date)
)
SELECT 
    week,
    total_tickets,
    ROUND(avg_first_response::numeric, 2) as avg_first_response_hours,
    ROUND(avg_resolution_time::numeric, 2) as avg_resolution_hours,
    high_priority_tickets,
    ROUND(avg_csat::numeric, 2) as avg_csat,
    CASE 
        WHEN avg_first_response <= 2 AND avg_csat >= 4.5 THEN 'Excellent'
        WHEN avg_first_response <= 4 AND avg_csat >= 4.0 THEN 'Good'
        ELSE 'Needs Improvement'
    END as performance_rating
FROM ticket_metrics
ORDER BY week DESC;
```

### Ticket Categorization and Trends

```sql
-- Identify trending support issues
WITH ticket_categories AS (
    SELECT 
        DATE_TRUNC('month', created_date) as month,
        category,
        sub_category,
        COUNT(*) as ticket_count,
        AVG(resolution_time) as avg_resolution
    FROM support_tickets
    WHERE created_date >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('month', created_date), category, sub_category
),
category_trends AS (
    SELECT 
        category,
        sub_category,
        ticket_count,
        LAG(ticket_count) OVER (PARTITION BY category, sub_category ORDER BY month) as prev_count,
        (ticket_count - LAG(ticket_count) OVER (PARTITION BY category, sub_category ORDER BY month)) * 100.0 / 
            NULLIF(LAG(ticket_count) OVER (PARTITION BY category, sub_category ORDER BY month), 0) as growth_rate
    FROM ticket_categories
    WHERE month = DATE_TRUNC('month', CURRENT_DATE)
)
SELECT 
    category,
    sub_category,
    ticket_count,
    growth_rate,
    CASE 
        WHEN growth_rate > 50 THEN 'Rapidly Increasing'
        WHEN growth_rate > 20 THEN 'Growing'
        WHEN growth_rate < -20 THEN 'Declining'
        ELSE 'Stable'
    END as trend
FROM category_trends
WHERE ticket_count > 10  -- Focus on significant categories
ORDER BY growth_rate DESC;
```

## 6. Expansion Analytics

### Expansion Opportunities

**Account Expansion Scoring**
```sql
WITH expansion_signals AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.current_mrr,
        -- Usage-based signals
        u.users_active / c.contracted_seats as seat_utilization,
        u.api_calls / c.api_limit as api_utilization,
        -- Growth signals
        (c.current_mrr - c.initial_mrr) / c.initial_mrr as historical_growth,
        -- Engagement signals
        h.health_score,
        e.features_adopted / e.total_features as feature_adoption_rate,
        -- Market signals
        m.company_growth_rate,
        m.funding_stage
    FROM customers c
    LEFT JOIN usage_metrics u ON c.customer_id = u.customer_id
    LEFT JOIN health_scores h ON c.customer_id = h.customer_id
    LEFT JOIN engagement_metrics e ON c.customer_id = e.customer_id
    LEFT JOIN market_data m ON c.company_id = m.company_id
    WHERE c.customer_status = 'active'
      AND c.months_since_start > 6
)
SELECT 
    customer_id,
    customer_name,
    current_mrr,
    CASE 
        WHEN seat_utilization > 0.8 THEN 30
        WHEN seat_utilization > 0.6 THEN 20
        ELSE 0
    END +
    CASE 
        WHEN api_utilization > 0.8 THEN 20
        WHEN api_utilization > 0.6 THEN 10
        ELSE 0
    END +
    CASE 
        WHEN health_score > 80 THEN 25
        WHEN health_score > 60 THEN 10
        ELSE 0
    END +
    CASE 
        WHEN feature_adoption_rate < 0.5 THEN 15  -- Room to grow
        ELSE 0
    END +
    CASE 
        WHEN company_growth_rate > 0.5 THEN 10
        ELSE 0
    END as expansion_score,
    
    ARRAY_REMOVE(ARRAY[
        CASE WHEN seat_utilization > 0.8 THEN 'High seat utilization' END,
        CASE WHEN api_utilization > 0.8 THEN 'API limit approaching' END,
        CASE WHEN feature_adoption_rate < 0.5 THEN 'Feature expansion opportunity' END,
        CASE WHEN company_growth_rate > 0.5 THEN 'Company growing fast' END
    ], NULL) as expansion_reasons
    
FROM expansion_signals
WHERE seat_utilization > 0.6 
   OR api_utilization > 0.6 
   OR (health_score > 80 AND feature_adoption_rate < 0.5)
ORDER BY expansion_score DESC;
```

### Upsell Playbooks

**Expansion Motion by Signal**
| Signal | Expansion Type | Playbook | Success Rate |
|--------|---------------|----------|--------------|
| Seat utilization > 80% | Seat expansion | Usage report + ROI | 65% |
| API limit approaching | Plan upgrade | Technical review | 55% |
| Low feature adoption | Feature training | Success workshop | 40% |
| High health + growth | Strategic upsell | Executive briefing | 45% |

## 7. Renewal Analytics

### Renewal Forecasting

```sql
-- Renewal pipeline analysis
WITH renewal_pipeline AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.renewal_date,
        c.contract_value,
        h.health_score,
        h.health_category,
        -- Calculate renewal probability
        CASE 
            WHEN h.health_category = 'Healthy' THEN 0.95
            WHEN h.health_category = 'At Risk' THEN 0.70
            ELSE 0.30
        END as renewal_probability,
        -- Days until renewal
        c.renewal_date - CURRENT_DATE as days_until_renewal
    FROM contracts c
    LEFT JOIN health_scores h ON c.customer_id = h.customer_id
    WHERE c.renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '120 days'
      AND c.status = 'active'
)
SELECT 
    CASE 
        WHEN days_until_renewal <= 30 THEN '0-30 days'
        WHEN days_until_renewal <= 60 THEN '31-60 days'
        WHEN days_until_renewal <= 90 THEN '61-90 days'
        ELSE '91-120 days'
    END as renewal_timeframe,
    COUNT(*) as account_count,
    SUM(contract_value) as total_arr,
    SUM(contract_value * renewal_probability) as weighted_arr,
    AVG(renewal_probability) * 100 as avg_renewal_probability,
    COUNT(CASE WHEN health_category = 'Critical' THEN 1 END) as critical_accounts
FROM renewal_pipeline
GROUP BY 
    CASE 
        WHEN days_until_renewal <= 30 THEN '0-30 days'
        WHEN days_until_renewal <= 60 THEN '31-60 days'
        WHEN days_until_renewal <= 90 THEN '61-90 days'
        ELSE '91-120 days'
    END
ORDER BY 
    CASE 
        WHEN days_until_renewal <= 30 THEN 1
        WHEN days_until_renewal <= 60 THEN 2
        WHEN days_until_renewal <= 90 THEN 3
        ELSE 4
    END;
```

## 8. Customer Segmentation

### Value-Based Segmentation

```sql
-- Segment customers by value and behavior
WITH customer_metrics AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.mrr,
        c.lifetime_value,
        h.health_score,
        u.product_usage_score,
        s.support_tickets_per_month,
        e.expansion_revenue
    FROM customers c
    LEFT JOIN health_scores h ON c.customer_id = h.customer_id
    LEFT JOIN usage_summary u ON c.customer_id = u.customer_id
    LEFT JOIN support_summary s ON c.customer_id = s.customer_id
    LEFT JOIN expansion_history e ON c.customer_id = e.customer_id
),
customer_segments AS (
    SELECT 
        customer_id,
        customer_name,
        mrr,
        CASE 
            WHEN mrr >= 10000 AND health_score >= 80 THEN 'Strategic'
            WHEN mrr >= 10000 AND health_score < 80 THEN 'At-Risk Strategic'
            WHEN mrr < 10000 AND health_score >= 80 AND expansion_revenue > 0 THEN 'Growth'
            WHEN mrr < 10000 AND health_score >= 80 THEN 'Stable'
            WHEN health_score < 60 THEN 'Churn Risk'
            ELSE 'Monitor'
        END as segment,
        health_score,
        product_usage_score
    FROM customer_metrics
)
SELECT 
    segment,
    COUNT(*) as customer_count,
    SUM(mrr) as total_mrr,
    AVG(mrr) as avg_mrr,
    AVG(health_score) as avg_health_score,
    SUM(mrr) * 100.0 / SUM(SUM(mrr)) OVER () as mrr_percentage
FROM customer_segments
GROUP BY segment
ORDER BY total_mrr DESC;
```

## 9. Practical Exercises

### Exercise 1: Churn Risk Model Development
Build a churn prediction model using:
1. Historical churn data
2. Usage patterns
3. Support interactions
4. Engagement metrics

Deliverable: Ranked list of at-risk accounts with intervention recommendations

### Exercise 2: Health Score Optimization
Current health score has 60% correlation with retention. Improve it by:
1. Analyzing which factors best predict churn
2. Adjusting weights
3. Adding new signals
4. Validating with historical data

### Exercise 3: Support Efficiency Analysis
Support costs are rising faster than revenue. Analyze:
1. Ticket categorization
2. Resolution time by type
3. Self-service opportunities
4. Automation potential

## 10. Key Takeaways

1. **Proactive > Reactive**: Identify risks before they become problems
2. **Multi-dimensional Health**: No single metric captures customer health
3. **Segmentation Matters**: Different customers need different strategies
4. **Data + Relationships**: Combine quantitative and qualitative insights
5. **Continuous Iteration**: Refine models based on outcomes

## Next Steps

- Project 1: Churn Risk Model Development
- Project 2: Retention Campaign Design (follow-up)
- Advanced Topics: Machine learning for CS
- Cross-functional: CS-Product analytics alignment