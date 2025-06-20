# Customer Experience Analytics Guide

Welcome to the Customer Experience Analytics guide for the SaaS Analytics Platform. This guide will help you monitor customer health, predict churn, optimize support operations, and drive customer success initiatives.

## 🎯 Overview

As a Customer Experience Analyst, you have access to comprehensive metrics across the entire customer journey. Our platform provides real-time insights into:

- Customer health and satisfaction
- Churn risk identification
- Support ticket analytics
- User engagement patterns
- Product adoption tracking
- Success metric monitoring

## 📊 Key Tables & Metrics

### Primary CX Tables

1. **`metrics.customer_success`** - Your main analytics table
   - Pre-calculated customer health KPIs
   - Support metrics and SLAs
   - Engagement and adoption scores
   - Updated daily with 30/60/90 day windows

2. **`entity.entity_customers`** - Customer master data
   - Current health scores and risk indicators
   - Subscription and revenue data
   - Device and user counts
   - Historical tracking available

3. **`entity.entity_users`** - User-level analytics
   - Individual engagement scores
   - Feature adoption metrics
   - Last activity tracking
   - Usage patterns

4. **`entity.entity_devices`** - IoT device monitoring
   - Device health and uptime
   - Usage volume metrics
   - Maintenance indicators
   - Revenue contribution

### Essential Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| `customer_health_score` | Composite health (0-100) | Overall account health |
| `churn_risk_score` | Churn probability (0-100) | Retention prioritization |
| `composite_success_score` | Success indicator | Success benchmarking |
| `user_activation_rate` | % users activated | Onboarding effectiveness |
| `avg_engagement_score` | User engagement level | Usage monitoring |
| `support_tickets_30d` | Recent ticket volume | Support load |
| `ticket_resolution_rate` | % tickets resolved | Support efficiency |
| `nps_score` | Net Promoter Score | Satisfaction tracking |
| `device_health_avg` | Average device health | Operational health |

## 🚀 Common Reports & Queries

### 1. Customer Health Dashboard
```sql
-- Customer health overview with risk segments
WITH health_segments AS (
    SELECT 
        CASE 
            WHEN customer_health_score >= 80 THEN 'Healthy'
            WHEN customer_health_score >= 60 THEN 'Neutral'
            WHEN customer_health_score >= 40 THEN 'At Risk'
            ELSE 'Critical'
        END as health_segment,
        CASE 
            WHEN churn_risk_score >= 70 THEN 'High Risk'
            WHEN churn_risk_score >= 40 THEN 'Medium Risk'
            ELSE 'Low Risk'
        END as churn_segment,
        COUNT(DISTINCT customer_id) as customer_count,
        SUM(monthly_recurring_revenue) as total_mrr,
        AVG(customer_health_score) as avg_health,
        AVG(churn_risk_score) as avg_churn_risk
    FROM entity.entity_customers
    WHERE is_active = true
    GROUP BY health_segment, churn_segment
)
SELECT 
    health_segment,
    churn_segment,
    customer_count,
    total_mrr,
    ROUND(100.0 * customer_count / SUM(customer_count) OVER (), 1) as pct_of_customers,
    ROUND(100.0 * total_mrr / SUM(total_mrr) OVER (), 1) as pct_of_revenue,
    avg_health,
    avg_churn_risk
FROM health_segments
ORDER BY 
    CASE health_segment
        WHEN 'Critical' THEN 1
        WHEN 'At Risk' THEN 2
        WHEN 'Neutral' THEN 3
        WHEN 'Healthy' THEN 4
    END;
```

### 2. Churn Risk Analysis
```sql
-- High-risk customers with contributing factors
WITH risk_factors AS (
    SELECT 
        c.customer_id,
        c.company_name,
        c.customer_tier,
        c.monthly_recurring_revenue,
        c.churn_risk_score,
        cs.health_trend_30d,
        cs.support_tickets_30d,
        cs.days_since_last_login,
        cs.feature_adoption_rate,
        cs.user_activation_rate,
        -- Risk factor flags
        CASE WHEN cs.health_trend_30d < -10 THEN 1 ELSE 0 END as declining_health,
        CASE WHEN cs.support_tickets_30d > 5 THEN 1 ELSE 0 END as high_support_volume,
        CASE WHEN cs.days_since_last_login > 14 THEN 1 ELSE 0 END as low_engagement,
        CASE WHEN cs.feature_adoption_rate < 0.3 THEN 1 ELSE 0 END as low_adoption,
        CASE WHEN cs.user_activation_rate < 0.5 THEN 1 ELSE 0 END as low_activation
    FROM entity.entity_customers c
    JOIN metrics.customer_success cs ON c.customer_id = cs.customer_id
    WHERE c.churn_risk_score >= 60
      AND c.is_active = true
)
SELECT 
    customer_id,
    company_name,
    customer_tier,
    monthly_recurring_revenue,
    churn_risk_score,
    declining_health + high_support_volume + low_engagement + low_adoption + low_activation as risk_factor_count,
    ARRAY_REMOVE(ARRAY[
        CASE WHEN declining_health = 1 THEN 'Declining Health' END,
        CASE WHEN high_support_volume = 1 THEN 'High Support Volume' END,
        CASE WHEN low_engagement = 1 THEN 'Low Engagement' END,
        CASE WHEN low_adoption = 1 THEN 'Low Feature Adoption' END,
        CASE WHEN low_activation = 1 THEN 'Low User Activation' END
    ], NULL) as risk_factors
FROM risk_factors
ORDER BY churn_risk_score DESC, monthly_recurring_revenue DESC
LIMIT 50;
```

### 3. Support Performance Analytics
```sql
-- Support metrics by customer segment
WITH support_metrics AS (
    SELECT 
        c.customer_tier,
        COUNT(DISTINCT c.customer_id) as customer_count,
        SUM(cs.support_tickets_30d) as total_tickets,
        AVG(cs.support_tickets_30d) as avg_tickets_per_customer,
        AVG(cs.ticket_resolution_rate) as avg_resolution_rate,
        AVG(cs.avg_resolution_time_hours) as avg_resolution_hours,
        SUM(CASE WHEN cs.has_escalated_ticket THEN 1 ELSE 0 END) as customers_with_escalations
    FROM entity.entity_customers c
    JOIN metrics.customer_success cs ON c.customer_id = cs.customer_id
    WHERE c.is_active = true
    GROUP BY c.customer_tier
)
SELECT 
    customer_tier,
    customer_count,
    total_tickets,
    ROUND(avg_tickets_per_customer, 2) as avg_tickets_per_customer,
    ROUND(avg_resolution_rate * 100, 1) as resolution_rate_pct,
    ROUND(avg_resolution_hours, 1) as avg_resolution_hours,
    ROUND(100.0 * customers_with_escalations / customer_count, 1) as escalation_rate_pct,
    CASE 
        WHEN avg_resolution_hours <= 4 THEN 'Excellent'
        WHEN avg_resolution_hours <= 8 THEN 'Good'
        WHEN avg_resolution_hours <= 24 THEN 'Acceptable'
        ELSE 'Needs Improvement'
    END as sla_status
FROM support_metrics
ORDER BY 
    CASE customer_tier
        WHEN 'Enterprise' THEN 1
        WHEN 'Mid-Market' THEN 2
        WHEN 'SMB' THEN 3
    END;
```

### 4. User Engagement Analysis
```sql
-- User engagement patterns by customer
WITH user_engagement AS (
    SELECT 
        c.customer_id,
        c.company_name,
        c.total_users,
        COUNT(DISTINCT CASE WHEN u.days_since_last_login <= 7 THEN u.user_id END) as wau,
        COUNT(DISTINCT CASE WHEN u.days_since_last_login <= 30 THEN u.user_id END) as mau,
        AVG(u.engagement_score) as avg_engagement_score,
        AVG(u.total_sessions_30d) as avg_sessions_per_user,
        COUNT(DISTINCT CASE WHEN u.user_engagement_tier = 'Power User' THEN u.user_id END) as power_users
    FROM entity.entity_customers c
    JOIN entity.entity_users u ON c.customer_id = u.customer_id
    WHERE c.is_active = true
      AND u.is_active = true
    GROUP BY c.customer_id, c.company_name, c.total_users
)
SELECT 
    customer_id,
    company_name,
    total_users,
    wau,
    mau,
    ROUND(100.0 * wau / NULLIF(total_users, 0), 1) as wau_rate,
    ROUND(100.0 * mau / NULLIF(total_users, 0), 1) as mau_rate,
    ROUND(100.0 * wau / NULLIF(mau, 0), 1) as stickiness_ratio,
    ROUND(avg_engagement_score, 1) as avg_engagement_score,
    ROUND(avg_sessions_per_user, 1) as avg_sessions_per_user,
    power_users,
    ROUND(100.0 * power_users / NULLIF(total_users, 0), 1) as power_user_rate
FROM user_engagement
WHERE total_users > 0
ORDER BY mau_rate DESC;
```

### 5. Product Adoption Tracking
```sql
-- Feature adoption and usage intensity
WITH feature_adoption AS (
    SELECT 
        f.feature_name,
        f.feature_category,
        COUNT(DISTINCT c.customer_id) as customers_using,
        AVG(f.adoption_rate) as avg_adoption_rate,
        AVG(f.usage_intensity_score) as avg_usage_intensity,
        AVG(f.retention_impact_score) as avg_retention_impact,
        SUM(c.monthly_recurring_revenue) as mrr_using_feature
    FROM entity.entity_features f
    JOIN entity.entity_customers c ON f.customer_id = c.customer_id
    WHERE c.is_active = true
      AND f.adoption_rate > 0
    GROUP BY f.feature_name, f.feature_category
),
totals AS (
    SELECT 
        COUNT(DISTINCT customer_id) as total_customers,
        SUM(monthly_recurring_revenue) as total_mrr
    FROM entity.entity_customers
    WHERE is_active = true
)
SELECT 
    fa.feature_name,
    fa.feature_category,
    fa.customers_using,
    ROUND(100.0 * fa.customers_using / t.total_customers, 1) as adoption_pct,
    ROUND(fa.avg_adoption_rate * 100, 1) as avg_user_adoption_pct,
    ROUND(fa.avg_usage_intensity, 1) as usage_intensity,
    ROUND(fa.avg_retention_impact, 1) as retention_impact,
    ROUND(100.0 * fa.mrr_using_feature / t.total_mrr, 1) as revenue_coverage_pct
FROM feature_adoption fa
CROSS JOIN totals t
ORDER BY fa.adoption_pct DESC;
```

## 📈 Advanced Analytics

### Customer Lifetime Value Analysis
```sql
-- CLV segmentation with health correlation
WITH clv_analysis AS (
    SELECT 
        c.customer_id,
        c.company_name,
        c.customer_health_score,
        c.months_since_first_subscription,
        c.monthly_recurring_revenue,
        c.lifetime_value,
        c.lifetime_value / NULLIF(c.months_since_first_subscription, 0) as monthly_clv_rate,
        cs.expansion_revenue_total,
        cs.contraction_revenue_total,
        (cs.expansion_revenue_total - cs.contraction_revenue_total) as net_expansion
    FROM entity.entity_customers c
    JOIN metrics.customer_success cs ON c.customer_id = cs.customer_id
    WHERE c.is_active = true
      AND c.months_since_first_subscription >= 6
)
SELECT 
    CASE 
        WHEN lifetime_value >= 100000 THEN 'High CLV (>$100k)'
        WHEN lifetime_value >= 50000 THEN 'Medium CLV ($50-100k)'
        WHEN lifetime_value >= 20000 THEN 'Low CLV ($20-50k)'
        ELSE 'Entry CLV (<$20k)'
    END as clv_segment,
    COUNT(DISTINCT customer_id) as customer_count,
    AVG(customer_health_score) as avg_health_score,
    AVG(months_since_first_subscription) as avg_tenure_months,
    AVG(monthly_recurring_revenue) as avg_mrr,
    AVG(lifetime_value) as avg_clv,
    AVG(monthly_clv_rate) as avg_monthly_clv,
    SUM(net_expansion) as total_net_expansion
FROM clv_analysis
GROUP BY clv_segment
ORDER BY avg_clv DESC;
```

### Engagement Cohort Analysis
```sql
-- Monthly cohorts with engagement retention
WITH cohort_base AS (
    SELECT 
        DATE_TRUNC('month', c.first_subscription_date) as cohort_month,
        c.customer_id,
        c.company_name
    FROM entity.entity_customers c
    WHERE c.first_subscription_date >= CURRENT_DATE - INTERVAL '12 months'
),
cohort_activity AS (
    SELECT 
        cb.cohort_month,
        cd.date,
        EXTRACT(MONTH FROM AGE(cd.date, cb.cohort_month)) as months_since_start,
        COUNT(DISTINCT cb.customer_id) as cohort_size,
        COUNT(DISTINCT CASE WHEN cd.daily_active_users > 0 THEN cd.customer_id END) as active_customers,
        AVG(cd.customer_health_score) as avg_health_score
    FROM cohort_base cb
    LEFT JOIN entity.entity_customers_daily cd 
        ON cb.customer_id = cd.customer_id
        AND cd.date >= cb.cohort_month
    WHERE cd.date = DATE_TRUNC('month', cd.date) -- Monthly snapshots only
    GROUP BY cb.cohort_month, cd.date
)
SELECT 
    cohort_month,
    months_since_start,
    cohort_size,
    active_customers,
    ROUND(100.0 * active_customers / NULLIF(cohort_size, 0), 1) as retention_rate,
    ROUND(avg_health_score, 1) as avg_health_score
FROM cohort_activity
WHERE months_since_start <= 12
ORDER BY cohort_month DESC, months_since_start;
```

## 🎯 Best Practices

### 1. **Health Score Interpretation**
- **80-100**: Healthy customers, focus on expansion
- **60-79**: Neutral, maintain engagement
- **40-59**: At risk, intervention needed
- **0-39**: Critical, immediate action required

### 2. **Churn Prevention Workflow**
1. Daily monitoring of churn risk scores
2. Weekly review of high-risk accounts
3. Proactive outreach when scores drop
4. Track intervention effectiveness

### 3. **Support Optimization**
- Monitor ticket volume trends by segment
- Track resolution times against SLAs
- Identify common issues for knowledge base
- Measure support impact on health scores

### 4. **Engagement Monitoring**
Key ratios to track:
- WAU/MAU (Weekly stickiness)
- DAU/MAU (Daily stickiness)
- Power user percentage
- Feature adoption rates

## 🔗 Integration Points

### Support Systems
- HubSpot Tickets → Support metrics
- Ticket resolution → Health scoring
- Escalations → Risk indicators

### Product Usage
- User sessions → Engagement scores
- Feature usage → Adoption metrics
- Device telemetry → Operational health

### Revenue Systems
- Stripe subscriptions → MRR/ARR tracking
- Expansion/contraction → Growth metrics
- Payment failures → Risk indicators

## 📚 Additional Resources

- [Metrics Catalog](../common/metrics-catalog.md) - Complete metrics reference
- [Query Patterns](../common/query-patterns.md) - Reusable SQL templates
- [Health Score Methodology](./health-score-guide.md) - Scoring algorithm details
- [Churn Playbook](./churn-prevention-playbook.md) - Intervention strategies

## 🚦 Getting Started Checklist

- [ ] Review customer health dashboard
- [ ] Identify top 10 at-risk accounts
- [ ] Run engagement analysis query
- [ ] Set up daily health monitoring
- [ ] Join #customer-success Slack channel
- [ ] Meet with CS team lead

Welcome to Customer Experience Analytics! 🎉