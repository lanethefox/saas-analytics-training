# Module 1: SaaS Business Fundamentals

## 🎯 Module Overview

This foundational module bridges the gap between academic statistical training and practical business analytics. You'll learn how your statistical knowledge directly applies to real SaaS business problems while mastering the Entity-Centric Modeling approach that makes complex analytics accessible.

**Duration**: 3-4 hours  
**Prerequisites**: Basic SQL knowledge, understanding of statistical concepts  
**Outcome**: Ability to answer complex SaaS business questions with simple queries

## 📚 Learning Objectives

By the end of this module, you will:

1. **Understand Core SaaS Metrics**: Master MRR, ARR, churn, CAC, LTV, and other essential metrics
2. **Apply Statistical Knowledge**: See how regression, experimental design, and time series translate to business
3. **Query Entity Tables**: Write single-table queries that answer complex multi-dimensional questions
4. **Think Like a Business Analyst**: Frame technical insights in business terms that drive action
5. **Leverage Entity-Centric Modeling**: Understand why ECM revolutionizes analytical accessibility

## 🏗️ Module Structure

### Part 1: SaaS Business Model Foundation (45 minutes)
- Understanding subscription economics
- Key stakeholders and their analytical needs
- The bar management platform business context
- Mapping academic concepts to business applications

### Part 2: Entity-Centric Modeling Introduction (45 minutes)
- Traditional dimensional modeling challenges
- ECM philosophy and benefits
- The three-table pattern explained
- Hands-on exploration of entity tables

### Part 3: Core SaaS Metrics Deep Dive (60 minutes)
- Revenue metrics: MRR, ARR, expansion, contraction
- Customer metrics: CAC, LTV, payback period
- Engagement metrics: MAU, DAU, feature adoption
- Operational metrics: uptime, usage, quality

### Part 4: Practical Query Exercises (60 minutes)
- Writing your first entity queries
- Building a customer health dashboard
- Identifying expansion opportunities
- Creating executive-ready insights

## 🎓 Part 1: SaaS Business Model Foundation

### The Bar Management Platform Context

Our platform serves bars and restaurants with IoT-enabled tap systems that track pours, monitor inventory, and optimize operations. This creates a rich data environment:

- **Customers**: 20,000+ accounts ranging from single locations to enterprise chains
- **Devices**: 100,000+ smart taps generating millions of events monthly
- **Users**: Staff members using mobile apps for operations
- **Locations**: 30,000+ venues across different markets
- **Subscriptions**: Tiered pricing from Starter ($99) to Enterprise ($999+)

### Key Business Questions We Answer

1. **Sales**: "Which prospects are most likely to convert to Enterprise?"
2. **Customer Success**: "Which customers need intervention to prevent churn?"
3. **Product**: "What features drive the highest engagement and expansion?"
4. **Operations**: "Which locations have device issues affecting revenue?"
5. **Executive**: "What's our path to $100M ARR?"

### Mapping Your Statistical Knowledge

| Academic Concept | Business Application | Platform Example |
|-----------------|---------------------|------------------|
| Regression Analysis | Marketing Mix Modeling | "Which channels drive Enterprise conversions?" |
| Experimental Design | A/B Testing | "Does the new onboarding flow reduce churn?" |
| Time Series | Revenue Forecasting | "Project Q4 ARR based on current trends" |
| Clustering | Customer Segmentation | "Identify behavioral cohorts for targeting" |
| Survival Analysis | Churn Prediction | "When do customers typically churn?" |
| Hypothesis Testing | Feature Impact | "Does multi-location feature increase LTV?" |

## 🏛️ Part 2: Entity-Centric Modeling Introduction

### The Traditional Approach Problem

In traditional dimensional modeling, answering "Show me at-risk Enterprise customers" requires:

```sql
-- Traditional approach - Complex and slow!
SELECT 
    c.company_name,
    s.mrr,
    cs.health_score,
    COUNT(DISTINCT u.user_id) as active_users,
    COUNT(DISTINCT d.device_id) as devices,
    SUM(e.event_count) as total_events
FROM customers c
JOIN subscriptions s ON c.customer_id = s.customer_id
JOIN customer_scores cs ON c.customer_id = cs.customer_id  
JOIN users u ON c.customer_id = u.customer_id
JOIN devices d ON c.customer_id = d.customer_id
JOIN events e ON d.device_id = e.device_id
WHERE s.plan_tier = 'Enterprise'
  AND cs.churn_risk > 60
  AND s.status = 'active'
  AND e.event_date >= CURRENT_DATE - 30
GROUP BY c.company_name, s.mrr, cs.health_score;
```

### The Entity-Centric Solution

With ECM, the same question becomes:

```sql
-- Entity-Centric approach - Simple and fast!
SELECT 
    company_name,
    monthly_recurring_revenue,
    customer_health_score,
    active_users_30d,
    total_devices,
    device_events_30d
FROM entity.entity_customers
WHERE customer_tier = 3  -- Enterprise
  AND churn_risk_score > 60
  AND customer_status = 'active';
```

### The Three-Table Pattern

Each entity implements three complementary tables:

1. **Atomic Table** (`entity_customers`)
   - Current state with real-time metrics
   - Optimized for dashboards and operational queries
   - Updated every 15 minutes

2. **History Table** (`entity_customers_history`)
   - Complete change history for temporal analysis
   - Enables trend detection and attribution
   - Captures every state change

3. **Grain Table** (`entity_customers_daily`)
   - Pre-aggregated for time-series analysis
   - Optimized for executive reporting
   - Enables fast period-over-period comparisons

## 📊 Part 3: Core SaaS Metrics Deep Dive

### Revenue Metrics in Entity Tables

```sql
-- MRR Analysis by Segment
SELECT 
    customer_tier,
    COUNT(*) as customer_count,
    SUM(monthly_recurring_revenue) as total_mrr,
    AVG(monthly_recurring_revenue) as avg_mrr,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_recurring_revenue) as median_mrr
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY customer_tier;

-- MRR Movement Analysis  
SELECT
    company_name,
    monthly_recurring_revenue as current_mrr,
    previous_mrr,
    monthly_recurring_revenue - previous_mrr as mrr_change,
    CASE 
        WHEN previous_mrr IS NULL THEN 'New'
        WHEN monthly_recurring_revenue > previous_mrr THEN 'Expansion'
        WHEN monthly_recurring_revenue < previous_mrr THEN 'Contraction'
        ELSE 'Stable'
    END as movement_type
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND ABS(monthly_recurring_revenue - COALESCE(previous_mrr, 0)) > 0;
```

### Customer Health Metrics

```sql
-- Health Score Distribution
SELECT 
    CASE 
        WHEN customer_health_score >= 80 THEN 'Healthy (80-100)'
        WHEN customer_health_score >= 60 THEN 'Stable (60-79)'
        WHEN customer_health_score >= 40 THEN 'At Risk (40-59)'
        ELSE 'Critical (0-39)'
    END as health_category,
    COUNT(*) as customer_count,
    SUM(monthly_recurring_revenue) as mrr_at_risk,
    AVG(churn_risk_score) as avg_churn_risk
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY health_category
ORDER BY 
    CASE health_category
        WHEN 'Critical (0-39)' THEN 1
        WHEN 'At Risk (40-59)' THEN 2
        WHEN 'Stable (60-79)' THEN 3
        ELSE 4
    END;
```

### Engagement Metrics

```sql
-- User Engagement Analysis
SELECT 
    company_name,
    total_users,
    active_users_30d,
    active_users_7d,
    ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as mau_rate,
    ROUND(active_users_7d::numeric / NULLIF(active_users_30d, 0) * 100, 1) as wau_mau_ratio,
    avg_user_engagement_score,
    CASE 
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) > 0.8 THEN 'Highly Engaged'
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) > 0.5 THEN 'Moderately Engaged'
        WHEN active_users_30d::numeric / NULLIF(total_users, 0) > 0.2 THEN 'Low Engagement'
        ELSE 'Disengaged'
    END as engagement_tier
FROM entity.entity_customers
WHERE customer_status = 'active'
  AND total_users > 0
ORDER BY mau_rate DESC;
```

## 🛠️ Part 4: Practical Query Exercises

### Exercise 1: Build a Customer Health Dashboard

Create a comprehensive view for Customer Success teams:

```sql
-- Customer Success Dashboard
SELECT 
    -- Customer Identity
    company_name,
    customer_tier,
    DATE_PART('day', CURRENT_DATE - created_at) as customer_age_days,
    
    -- Financial Health
    monthly_recurring_revenue as mrr,
    CASE 
        WHEN customer_tier = 1 THEN 999 - monthly_recurring_revenue
        WHEN customer_tier = 2 THEN 4999 - monthly_recurring_revenue  
        ELSE 0
    END as expansion_potential,
    
    -- Risk Indicators
    customer_health_score,
    churn_risk_score,
    CASE 
        WHEN churn_risk_score >= 70 THEN '🔴 Critical'
        WHEN churn_risk_score >= 50 THEN '🟡 Warning'
        ELSE '🟢 Healthy'
    END as risk_status,
    
    -- Usage Health
    device_events_30d,
    active_users_30d,
    ROUND(active_users_30d::numeric / NULLIF(total_users, 0) * 100, 1) as user_adoption_pct,
    
    -- Engagement Signals  
    DATE_PART('day', CURRENT_DATE - last_user_activity) as days_since_login,
    DATE_PART('day', CURRENT_DATE - last_device_activity) as days_since_usage,
    
    -- Action Priority
    CASE 
        WHEN churn_risk_score >= 70 OR device_events_30d = 0 THEN 1
        WHEN churn_risk_score >= 50 OR days_since_login > 7 THEN 2
        WHEN customer_health_score < 60 THEN 3
        ELSE 4
    END as priority_rank
    
FROM entity.entity_customers
WHERE customer_status = 'active'
ORDER BY priority_rank, monthly_recurring_revenue DESC
LIMIT 50;
```

### Exercise 2: Identify Expansion Opportunities

Find customers ready for upsell:

```sql
-- Expansion Opportunity Analysis
WITH usage_benchmarks AS (
    SELECT 
        customer_tier,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_devices) as p75_devices,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY active_users_30d) as p75_users,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY device_events_30d) as p75_events
    FROM entity.entity_customers
    WHERE customer_status = 'active'
    GROUP BY customer_tier
)
SELECT 
    c.company_name,
    c.customer_tier,
    c.monthly_recurring_revenue,
    
    -- Usage vs Tier Benchmarks
    c.total_devices,
    b.p75_devices as tier_typical_devices,
    c.active_users_30d,
    b.p75_users as tier_typical_users,
    
    -- Expansion Signals
    CASE 
        WHEN c.customer_tier = 1 AND c.total_devices > b.p75_devices THEN 'Outgrown Starter'
        WHEN c.customer_tier = 2 AND c.total_devices > b.p75_devices THEN 'Ready for Enterprise'
        WHEN c.customer_tier = 1 AND c.active_users_30d > b.p75_users THEN 'High User Growth'
        WHEN c.customer_health_score > 80 AND c.customer_tier < 3 THEN 'Happy Customer - Upsell'
        ELSE 'Monitor'
    END as expansion_signal,
    
    -- Revenue Opportunity  
    CASE 
        WHEN c.customer_tier = 1 AND (c.total_devices > b.p75_devices OR c.active_users_30d > b.p75_users)
            THEN 999 - c.monthly_recurring_revenue  -- Business tier pricing
        WHEN c.customer_tier = 2 AND (c.total_devices > b.p75_devices OR c.active_users_30d > b.p75_users)
            THEN 4999 - c.monthly_recurring_revenue  -- Enterprise tier pricing
        ELSE 0
    END as potential_mrr_increase,
    
    -- Readiness Check
    c.customer_health_score,
    c.churn_risk_score,
    c.days_since_creation as customer_age
    
FROM entity.entity_customers c
JOIN usage_benchmarks b ON c.customer_tier = b.customer_tier
WHERE c.customer_status = 'active'
  AND c.customer_health_score > 70  -- Only healthy customers
  AND c.churn_risk_score < 40       -- Low churn risk
  AND c.days_since_creation > 90    -- Established customers
  AND (c.total_devices > b.p75_devices OR c.active_users_30d > b.p75_users)
ORDER BY potential_mrr_increase DESC
LIMIT 25;
```

### Exercise 3: Executive MRR Waterfall

Build a revenue movement analysis:

```sql
-- MRR Waterfall Analysis
WITH mrr_movements AS (
    SELECT 
        DATE_TRUNC('month', created_at) as cohort_month,
        customer_status,
        SUM(CASE WHEN previous_mrr IS NULL THEN monthly_recurring_revenue ELSE 0 END) as new_mrr,
        SUM(CASE WHEN previous_mrr < monthly_recurring_revenue THEN monthly_recurring_revenue - previous_mrr ELSE 0 END) as expansion_mrr,
        SUM(CASE WHEN previous_mrr > monthly_recurring_revenue THEN previous_mrr - monthly_recurring_revenue ELSE 0 END) as contraction_mrr,
        SUM(CASE WHEN customer_status != 'active' AND previous_mrr IS NOT NULL THEN previous_mrr ELSE 0 END) as churned_mrr,
        COUNT(CASE WHEN previous_mrr IS NULL THEN 1 END) as new_customers,
        COUNT(CASE WHEN customer_status != 'active' AND previous_mrr IS NOT NULL THEN 1 END) as churned_customers
    FROM entity.entity_customers
    WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY cohort_month, customer_status
)
SELECT 
    cohort_month,
    new_customers,
    new_mrr,
    expansion_mrr,
    -contraction_mrr as contraction_mrr,
    -churned_mrr as churned_mrr,
    new_mrr + expansion_mrr - contraction_mrr - churned_mrr as net_new_mrr,
    SUM(new_mrr + expansion_mrr - contraction_mrr - churned_mrr) 
        OVER (ORDER BY cohort_month) as cumulative_mrr
FROM mrr_movements
ORDER BY cohort_month DESC;
```

## 🎯 Module Summary

### Key Takeaways

1. **Entity-Centric Modeling transforms complex analytics into simple queries**
   - No more 10-table joins
   - Business users can self-serve
   - Query performance guaranteed

2. **Statistical knowledge directly applies to SaaS metrics**
   - Regression → Marketing attribution
   - Experiments → A/B testing  
   - Time series → Revenue forecasting

3. **The three-table pattern serves different needs**
   - Atomic: Real-time operational dashboards
   - History: Temporal analysis and attribution
   - Grain: Executive reporting and trending

4. **Business impact comes from actionable insights**
   - Always connect metrics to actions
   - Prioritize by revenue impact
   - Speak the language of stakeholders

### Next Steps

1. **Practice Queries**: Work through the exercises with real data
2. **Build Dashboards**: Create views for different stakeholders  
3. **Explore Relationships**: Join entity tables for deeper insights
4. **Share Learnings**: Present findings to practice communication

### Additional Resources

- [Entity Table Documentation](../../docs/entity_tables_documentation.md)
- [Example Queries](../../examples/)
- [Data Model Overview](../../dbt_project/models/entity/)

## 📝 Module Assessment

Complete these challenges to validate your learning:

1. **Query Challenge**: Write a single query that identifies the top 10 customers most likely to churn with their key risk factors

2. **Dashboard Challenge**: Design a 5-metric executive dashboard using only entity_customers table

3. **Business Challenge**: Given a 20% churn rate, calculate the revenue impact and propose three intervention strategies with expected ROI

4. **Communication Challenge**: Prepare a 2-minute explanation of Entity-Centric Modeling for a non-technical executive

---

🎉 Congratulations on completing Module 1! You now have the foundation to tackle complex SaaS analytics with confidence. Ready for Module 2: Advanced Entity-Centric Modeling? →