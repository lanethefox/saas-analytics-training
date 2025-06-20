# Sales Analyst - Day in the Life

Welcome to your role as a Sales Analyst at TapFlow Analytics! Today is Monday, and you have several key tasks to complete.

## 🌅 8:00 AM - Morning Dashboard Review

Start your day by checking the key sales metrics:

```sql
-- Check weekend pipeline movements
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_opportunities,
    SUM(deal_value) as pipeline_value,
    AVG(deal_value) as avg_deal_size
FROM entity.entity_customers
WHERE created_at >= CURRENT_DATE - INTERVAL '3 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Your Task**: 
1. Open Superset and navigate to the Sales Pipeline dashboard
2. Note any significant changes from Friday
3. Identify accounts that moved stages over the weekend

## 📧 9:00 AM - Stakeholder Email

The VP of Sales needs an update on Q4 pipeline health.

```sql
-- Q4 Pipeline Analysis
SELECT 
    customer_tier,
    customer_segment,
    COUNT(*) as accounts,
    SUM(monthly_recurring_revenue) as total_mrr,
    AVG(customer_health_score) as avg_health,
    SUM(CASE WHEN days_since_last_activity > 30 THEN 1 ELSE 0 END) as stale_accounts
FROM entity.entity_customers
WHERE customer_status = 'active'
GROUP BY customer_tier, customer_segment
ORDER BY total_mrr DESC;
```

**Your Task**:
1. Run the analysis
2. Create a brief email summary highlighting:
   - Total pipeline value
   - Number of deals at risk (stale > 30 days)
   - Top 3 segments by value
   - Recommended actions

## ☕ 10:30 AM - Territory Performance Deep Dive

The Western region team is underperforming. Investigate why.

```sql
-- Territory Performance Analysis
WITH territory_metrics AS (
    SELECT 
        l.state as territory,
        COUNT(DISTINCT c.customer_id) as total_accounts,
        SUM(c.monthly_recurring_revenue) as mrr,
        AVG(c.expansion_revenue_potential) as avg_expansion_potential,
        AVG(l.revenue_per_location) as avg_location_revenue
    FROM entity.entity_customers c
    JOIN entity.entity_locations l ON c.customer_id = l.customer_id
    WHERE l.region = 'West'
    GROUP BY l.state
)
SELECT 
    territory,
    total_accounts,
    mrr,
    avg_expansion_potential,
    RANK() OVER (ORDER BY mrr DESC) as revenue_rank
FROM territory_metrics
ORDER BY mrr DESC;
```

**Your Task**:
1. Identify underperforming territories
2. Compare against historical performance
3. Look for patterns (industry, company size, etc.)
4. Prepare 3 actionable recommendations

## 🍽️ 12:00 PM - Lunch & Learn Prep

You're presenting "Using Data to Identify Expansion Opportunities" to the sales team.

```sql
-- Expansion Opportunity Finder
SELECT 
    c.company_name,
    c.customer_tier,
    c.monthly_recurring_revenue as current_mrr,
    c.expansion_revenue_potential,
    COUNT(DISTINCT l.location_id) as locations,
    COUNT(DISTINCT d.device_id) as devices,
    AVG(d.utilization_rate) as avg_utilization
FROM entity.entity_customers c
JOIN entity.entity_locations l ON c.customer_id = l.customer_id
JOIN entity.entity_devices d ON l.location_id = d.location_id
WHERE c.customer_status = 'active'
    AND c.expansion_revenue_potential > 1000
    AND d.utilization_rate > 0.8
GROUP BY c.customer_id, c.company_name, c.customer_tier, 
         c.monthly_recurring_revenue, c.expansion_revenue_potential
ORDER BY c.expansion_revenue_potential DESC
LIMIT 20;
```

**Your Task**:
1. Create a simple slide showing top expansion candidates
2. Calculate potential revenue impact
3. Suggest outreach strategy based on utilization

## 📊 2:00 PM - Ad-Hoc Analysis Request

A sales rep asks: "Which of my accounts are most likely to churn?"

```sql
-- Churn Risk Analysis for Sales Rep
SELECT 
    c.company_name,
    c.monthly_recurring_revenue,
    c.churn_risk_score,
    c.customer_health_score,
    c.days_since_last_activity,
    COUNT(DISTINCT ci.invoice_id) as overdue_invoices,
    MAX(ci.days_overdue) as max_days_overdue
FROM entity.entity_customers c
LEFT JOIN entity.entity_customers_daily cd 
    ON c.customer_id = cd.customer_id 
    AND cd.date = CURRENT_DATE - 1
LEFT JOIN raw.stripe_database_invoices ci 
    ON c.customer_id = ci.customer_id 
    AND ci.status = 'overdue'
WHERE c.assigned_sales_rep = 'rep_123' -- Replace with actual rep ID
    AND c.customer_status = 'active'
GROUP BY c.customer_id, c.company_name, c.monthly_recurring_revenue,
         c.churn_risk_score, c.customer_health_score, c.days_since_last_activity
HAVING c.churn_risk_score > 60 OR MAX(ci.days_overdue) > 30
ORDER BY c.churn_risk_score DESC;
```

**Your Task**:
1. Run the analysis for the requesting rep
2. Identify top 5 at-risk accounts
3. Provide specific warning signs for each
4. Suggest retention strategies

## 📈 3:30 PM - Forecast Update

Update the Q4 forecast model with latest actuals.

```sql
-- Current Quarter Performance
WITH monthly_performance AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(new_mrr) as new_mrr,
        SUM(expansion_mrr) as expansion_mrr,
        SUM(churned_mrr) as churned_mrr,
        SUM(net_new_mrr) as net_mrr_change
    FROM entity.entity_customers_daily
    WHERE date >= DATE_TRUNC('quarter', CURRENT_DATE)
    GROUP BY DATE_TRUNC('month', date)
)
SELECT 
    month,
    new_mrr,
    expansion_mrr,
    churned_mrr,
    net_mrr_change,
    SUM(net_mrr_change) OVER (ORDER BY month) as cumulative_mrr_change
FROM monthly_performance
ORDER BY month;
```

**Your Task**:
1. Compare actuals vs. forecast
2. Adjust end-of-quarter projections
3. Identify key risks and opportunities
4. Update the forecast spreadsheet

## 🎯 4:30 PM - Win/Loss Analysis

Analyze why we lost 3 major deals last week.

```sql
-- Lost Deal Analysis
SELECT 
    c.company_name,
    c.industry,
    c.employee_count,
    c.churned_at,
    c.churn_reason,
    c.lifetime_value,
    c.total_revenue_generated,
    cd.competitor_mentioned,
    cd.price_sensitivity_score
FROM entity.entity_customers c
JOIN entity.entity_customers_history ch 
    ON c.customer_id = ch.customer_id
LEFT JOIN calculated.deal_intelligence cd 
    ON c.customer_id = cd.customer_id
WHERE c.churned_at >= CURRENT_DATE - INTERVAL '7 days'
    AND c.lifetime_value > 50000
ORDER BY c.lifetime_value DESC;
```

**Your Task**:
1. Identify common patterns in lost deals
2. Compare against won deals in same period
3. Document competitive intelligence
4. Recommend process improvements

## 📝 5:00 PM - End of Day Wrap-Up

Before leaving, prepare tomorrow's priorities:

1. **Update CRM Notes**: Log all customer insights discovered today
2. **Set Alerts**: Create monitors for accounts showing risk signals
3. **Calendar Review**: Prep data for tomorrow's pipeline review meeting
4. **Quick Win Email**: Send expansion opportunities to account managers

## 🎓 Reflection Questions

At the end of your simulated day, consider:

1. Which analysis provided the most actionable insights?
2. How would you improve the morning dashboard?
3. What additional data would help you be more effective?
4. How did you prioritize competing requests?
5. What patterns did you notice across different analyses?

## 📊 Success Metrics

Track your performance:
- Number of insights discovered: ___
- Stakeholder requests completed: ___/5
- Proactive recommendations made: ___
- Time to complete analyses: ___
- Data quality issues identified: ___

Remember: In real life, you'd collaborate with other teams, attend meetings, and handle interruptions. This simulation focuses on the analytical aspects of the role.