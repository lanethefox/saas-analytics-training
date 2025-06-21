# Module 3: Revenue Analytics

## Overview

Revenue analytics is the financial heartbeat of any SaaS business. It goes beyond simple bookkeeping to provide insights into growth dynamics, customer economics, and business sustainability. Understanding these metrics enables data-driven decisions about pricing, sales strategies, and resource allocation.

## Revenue Recognition in SaaS

### Key Principles

**Accrual vs Cash Basis**:
- **Accrual**: Revenue recognized when earned (GAAP standard)
- **Cash**: Revenue recognized when payment received
- **Deferred Revenue**: Money collected but not yet earned

**SaaS Revenue Timing**:
```
Monthly Subscription: $1,200 annual contract
- Cash Collected: $1,200 on day 1
- Monthly Revenue Recognition: $100/month for 12 months
- Deferred Revenue: Decreases by $100 monthly
```

### Revenue Types

1. **Recurring Revenue**: Predictable subscription fees
2. **Non-Recurring Revenue**: One-time fees (setup, training)
3. **Usage-Based Revenue**: Consumption-driven charges
4. **Professional Services**: Implementation and consulting

## Core Revenue Metrics

### 1. Bookings

**Definition**: Total value of signed contracts

**Types**:
- **New Bookings**: First-time customer contracts
- **Renewal Bookings**: Existing customer renewals
- **Expansion Bookings**: Upsells and add-ons
**Calculation**:
```sql
-- Monthly bookings analysis
WITH bookings_detail AS (
  SELECT 
    DATE_TRUNC('month', contract_date) as booking_month,
    CASE 
      WHEN contract_type = 'new' THEN 'New'
      WHEN contract_type = 'renewal' THEN 'Renewal'
      WHEN contract_type = 'expansion' THEN 'Expansion'
    END as booking_type,
    SUM(total_contract_value) as tcv,
    SUM(annual_contract_value) as acv,
    COUNT(*) as deals
  FROM contracts
  GROUP BY 1, 2
)
SELECT 
  booking_month,
  booking_type,
  tcv,
  acv,
  deals,
  ROUND(tcv / NULLIF(deals, 0), 0) as avg_deal_size
FROM bookings_detail
ORDER BY booking_month DESC, booking_type;
```

### 2. Annual Contract Value (ACV) vs Total Contract Value (TCV)

**ACV**: Annual value of a contract
```
ACV = Total Contract Value / Contract Length in Years
```

**TCV**: Total value over entire contract term
```
TCV = Monthly Recurring Revenue × Contract Months + One-Time Fees
```

**Example**:
- 3-year contract at $10,000/month + $5,000 setup
- TCV = ($10,000 × 36) + $5,000 = $365,000
- ACV = $360,000 / 3 = $120,000
### 3. Revenue Growth Metrics

**Year-over-Year (YoY) Growth**:
```sql
-- YoY revenue growth analysis
WITH revenue_comparison AS (
  SELECT 
    DATE_TRUNC('month', revenue_date) as month,
    SUM(revenue_amount) as monthly_revenue,
    LAG(SUM(revenue_amount), 12) OVER (ORDER BY DATE_TRUNC('month', revenue_date)) as prior_year_revenue
  FROM revenue_recognition
  GROUP BY 1
)
SELECT 
  month,
  monthly_revenue,
  prior_year_revenue,
  ROUND((monthly_revenue - prior_year_revenue) / NULLIF(prior_year_revenue, 0) * 100, 1) as yoy_growth_pct,
  monthly_revenue - prior_year_revenue as yoy_growth_absolute
FROM revenue_comparison
WHERE prior_year_revenue IS NOT NULL
ORDER BY month DESC;
```

**Compound Monthly Growth Rate (CMGR)**:
```
CMGR = (Ending MRR / Beginning MRR)^(1/months) - 1
```

### 4. Revenue Expansion Metrics

**Net Dollar Retention (NDR)**:
```sql
-- Calculate NDR by cohort
WITH cohort_revenue AS (
  SELECT 
    DATE_TRUNC('month', first_payment_date) as cohort_month,
    DATE_TRUNC('month', revenue_date) as revenue_month,
    SUM(CASE WHEN revenue_date = first_payment_date THEN revenue_amount END) as starting_mrr,
    SUM(revenue_amount) as current_mrr
  FROM customer_revenue
  GROUP BY 1, 2
)SELECT 
  cohort_month,
  revenue_month,
  starting_mrr,
  current_mrr,
  ROUND(100.0 * current_mrr / NULLIF(starting_mrr, 0), 1) as net_dollar_retention
FROM cohort_revenue
WHERE DATEDIFF('month', cohort_month, revenue_month) = 12 -- 12-month NDR
ORDER BY cohort_month DESC;

**Gross Dollar Retention (GDR)**:
- NDR without expansion revenue
- Shows pure retention without growth
- Always ≤ 100%

### 5. Revenue per Account Metrics

**Average Revenue Per Account (ARPA)**:
```
ARPA = Total MRR / Active Customers
```

**Average Selling Price (ASP)**:
```
ASP = Total New Bookings / Number of New Deals
```

**Land and Expand Analysis**:
```sql
-- Customer expansion patterns
WITH customer_revenue_history AS (
  SELECT 
    customer_id,
    MIN(mrr) as initial_mrr,
    MAX(mrr) as peak_mrr,
    LAST_VALUE(mrr) OVER (PARTITION BY customer_id ORDER BY month) as current_mrr,
    DATEDIFF('month', MIN(month), MAX(month)) as customer_months
  FROM monthly_customer_revenue
  GROUP BY customer_id
)SELECT 
  CASE 
    WHEN current_mrr / initial_mrr >= 2 THEN '2x+ Expansion'
    WHEN current_mrr / initial_mrr >= 1.5 THEN '1.5-2x Expansion'
    WHEN current_mrr / initial_mrr >= 1.1 THEN '1.1-1.5x Expansion'
    WHEN current_mrr / initial_mrr >= 1 THEN 'Flat'
    ELSE 'Contraction'
  END as expansion_category,
  COUNT(*) as customers,
  AVG(initial_mrr) as avg_initial_mrr,
  AVG(current_mrr) as avg_current_mrr,
  AVG(customer_months) as avg_tenure_months
FROM customer_revenue_history
WHERE customer_months >= 12 -- At least 1 year tenure
GROUP BY 1
ORDER BY 
  CASE expansion_category
    WHEN '2x+ Expansion' THEN 1
    WHEN '1.5-2x Expansion' THEN 2
    WHEN '1.1-1.5x Expansion' THEN 3
    WHEN 'Flat' THEN 4
    WHEN 'Contraction' THEN 5
  END;

### 6. Pricing Metrics

**Price Realization Rate**:
```
Realization Rate = Actual Price Paid / List Price
```

**Discount Analysis**:
```sql
-- Discount impact on customer value
WITH deal_metrics AS (
  SELECT 
    CASE 
      WHEN discount_percentage = 0 THEN 'No Discount'
      WHEN discount_percentage <= 10 THEN '1-10% Discount'
      WHEN discount_percentage <= 20 THEN '11-20% Discount'
      WHEN discount_percentage <= 30 THEN '21-30% Discount'
      ELSE '30%+ Discount'
    END as discount_tier,
    COUNT(*) as deals,
    AVG(acv) as avg_acv,
    AVG(customer_lifetime_months) as avg_retention,
    AVG(ltv) as avg_ltv
  FROM deals d
  JOIN customer_metrics cm ON d.customer_id = cm.customer_id
  GROUP BY 1
)SELECT 
  discount_tier,
  deals,
  ROUND(avg_acv, 0) as avg_acv,
  ROUND(avg_retention, 1) as avg_retention_months,
  ROUND(avg_ltv, 0) as avg_ltv,
  ROUND(avg_ltv / avg_acv, 2) as ltv_to_acv_ratio
FROM deal_metrics
ORDER BY 
  CASE discount_tier
    WHEN 'No Discount' THEN 1
    WHEN '1-10% Discount' THEN 2
    WHEN '11-20% Discount' THEN 3
    WHEN '21-30% Discount' THEN 4
    WHEN '30%+ Discount' THEN 5
  END;

## Common Stakeholder Questions

### From the CFO/Finance Team
1. "What's our revenue forecast for next quarter?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Show me projected revenue for the next three months | Use MRR trends + pipeline data from `revenue_forecasts` and `deal_pipeline` |

2. "How much deferred revenue is on the balance sheet?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What revenue have we collected but not yet recognized? | Sum unrecognized portion from `deferred_revenue` table by contract terms |

3. "What's driving the variance from our revenue plan?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Why are we above or below our revenue targets? | Compare actual vs plan from `revenue_actuals` vs `revenue_plan`, break down by component |

4. "How does revenue concentration look across customers?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What percentage of revenue comes from our biggest customers? | Calculate cumulative revenue distribution from `customer_revenue` ranked by size |

5. "What's our collections efficiency?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How quickly are we collecting payment from customers? | Calculate days sales outstanding from `invoices` and `payments` tables |

### From Sales Leadership
1. "What's our average deal size trending?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are our new deals getting bigger or smaller over time? | Calculate average ACV from `deals` by month, compare to historical trends |

2. "How does discount level impact customer lifetime value?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do discounted customers stay longer or churn faster? | Join `deals` (discount_percentage) with `customer_ltv` and analyze correlation |

3. "Which segments have the highest expansion rates?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What types of customers grow their spending most? | Group expansion events from `mrr_movements` by customer segment |

4. "What's our win rate by deal size?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do we close larger or smaller deals more successfully? | Calculate win rate from `opportunities` by deal_value buckets |

5. "How long does it take to expand accounts?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How many months until customers buy more? | Calculate time between initial purchase and first expansion from `customer_expansions` |

### From the CEO/Board
1. "What's our path to $100M ARR?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How do we reach $100M annual recurring revenue? | Model growth scenarios using current MRR + acquisition rates + expansion rates from `revenue_projections` |

2. "How efficient is our growth (Rule of 40)?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are we balancing growth and profitability effectively? | Calculate revenue growth rate + EBITDA margin from `financial_metrics` (should sum to >40%) |

3. "What's our revenue predictability?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How much of next quarter's revenue is already locked in? | Sum committed revenue from existing subscriptions + signed but not started deals |

4. "How concentrated is our revenue risk?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What percentage of revenue comes from our biggest customers? | Calculate revenue concentration: top 5, 10, 20 customers as % of total from `customer_revenue_rankings` |

5. "What's driving net dollar retention?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Why is our existing customer revenue growing or shrinking? | Break down NDR components: expansion, contraction, churn by cohort from `ndr_analysis` |
## Standard Revenue Reports

### 1. Revenue Waterfall
```sql
-- Monthly revenue walk from beginning to end
WITH revenue_movements AS (
  SELECT 
    DATE_TRUNC('month', movement_date) as month,
    SUM(CASE WHEN movement_type = 'starting_mrr' THEN amount END) as starting_mrr,
    SUM(CASE WHEN movement_type = 'new' THEN amount END) as new_mrr,
    SUM(CASE WHEN movement_type = 'expansion' THEN amount END) as expansion_mrr,
    SUM(CASE WHEN movement_type = 'contraction' THEN amount END) as contraction_mrr,
    SUM(CASE WHEN movement_type = 'churn' THEN amount END) as churn_mrr,
    SUM(CASE WHEN movement_type = 'reactivation' THEN amount END) as reactivation_mrr
  FROM mrr_movements
  GROUP BY 1
)
SELECT 
  month,
  starting_mrr,
  new_mrr,
  expansion_mrr,
  reactivation_mrr,
  -contraction_mrr as contraction_mrr,
  -churn_mrr as churn_mrr,
  starting_mrr + new_mrr + expansion_mrr + reactivation_mrr - contraction_mrr - churn_mrr as ending_mrr,
  ROUND((new_mrr + expansion_mrr + reactivation_mrr - contraction_mrr - churn_mrr) / NULLIF(starting_mrr, 0) * 100, 1) as net_growth_rate
FROM revenue_movements
ORDER BY month DESC;
```
### 2. Revenue Concentration Analysis
```sql
-- Customer revenue concentration (for investor risk assessment)
WITH customer_revenue_ranked AS (
  SELECT 
    customer_name,
    SUM(mrr) as total_mrr,
    RANK() OVER (ORDER BY SUM(mrr) DESC) as revenue_rank,
    SUM(SUM(mrr)) OVER (ORDER BY SUM(mrr) DESC) as cumulative_mrr,
    SUM(SUM(mrr)) OVER () as total_company_mrr
  FROM customer_revenue
  WHERE status = 'active'
  GROUP BY customer_name
)
SELECT 
  CASE 
    WHEN revenue_rank <= 10 THEN 'Top 10'
    WHEN revenue_rank <= 20 THEN 'Top 11-20'
    WHEN revenue_rank <= 50 THEN 'Top 21-50'
    WHEN revenue_rank <= 100 THEN 'Top 51-100'
    ELSE 'Rest'
  END as customer_tier,
  COUNT(*) as customer_count,
  SUM(total_mrr) as tier_mrr,
  ROUND(100.0 * SUM(total_mrr) / MAX(total_company_mrr), 1) as pct_of_total_mrr,
  ROUND(AVG(total_mrr), 0) as avg_customer_mrr
FROM customer_revenue_ranked
GROUP BY 1
ORDER BY 
  CASE customer_tier
    WHEN 'Top 10' THEN 1
    WHEN 'Top 11-20' THEN 2
    WHEN 'Top 21-50' THEN 3
    WHEN 'Top 51-100' THEN 4
    ELSE 5
  END;
```
### 3. Cohort Revenue Retention
```sql
-- Revenue retention by monthly cohort
WITH cohort_base AS (
  SELECT 
    DATE_TRUNC('month', first_payment_date) as cohort_month,
    customer_id,
    first_month_mrr
  FROM customer_first_payment
),
monthly_revenue AS (
  SELECT 
    c.cohort_month,
    DATE_TRUNC('month', r.revenue_date) as revenue_month,
    DATEDIFF('month', c.cohort_month, DATE_TRUNC('month', r.revenue_date)) as months_since_start,
    SUM(r.mrr) as cohort_mrr,
    SUM(c.first_month_mrr) as initial_cohort_mrr
  FROM cohort_base c
  LEFT JOIN revenue r ON c.customer_id = r.customer_id
  GROUP BY 1, 2, 3
)
SELECT 
  cohort_month,
  months_since_start,
  cohort_mrr,
  initial_cohort_mrr,
  ROUND(100.0 * cohort_mrr / initial_cohort_mrr, 1) as revenue_retention_pct
FROM monthly_revenue
WHERE months_since_start <= 24 -- Show 2 years
ORDER BY cohort_month DESC, months_since_start;
```

### 4. Revenue per Employee (Efficiency Metric)
```sql
-- Revenue efficiency metrics
WITH company_metrics AS (
  SELECT 
    DATE_TRUNC('quarter', date) as quarter,
    SUM(mrr) * 3 as quarterly_revenue, -- Convert MRR to quarterly
    AVG(employee_count) as avg_employees,
    AVG(sales_employee_count) as avg_sales_employees,
    AVG(engineering_employee_count) as avg_eng_employees
  FROM daily_company_metrics
  GROUP BY 1
)SELECT 
  quarter,
  quarterly_revenue,
  avg_employees,
  ROUND(quarterly_revenue / NULLIF(avg_employees, 0), 0) as revenue_per_employee,
  ROUND(quarterly_revenue / NULLIF(avg_sales_employees, 0), 0) as revenue_per_sales_employee,
  ROUND(avg_sales_employees / NULLIF(avg_employees, 0) * 100, 1) as sales_employee_pct
FROM company_metrics
ORDER BY quarter DESC;

## Advanced Revenue Analytics

### 1. Pricing Optimization Analysis
```sql
-- Price elasticity by segment
WITH pricing_cohorts AS (
  SELECT 
    customer_segment,
    price_point,
    COUNT(*) as customers,
    AVG(conversion_rate) as avg_conversion,
    AVG(mrr) as avg_mrr,
    AVG(churn_rate) as avg_churn,
    AVG(ltv) as avg_ltv
  FROM pricing_experiments
  GROUP BY customer_segment, price_point
)
SELECT 
  customer_segment,
  price_point,
  customers,
  ROUND(avg_conversion * 100, 1) as conversion_rate_pct,
  ROUND(avg_mrr, 0) as avg_mrr,
  ROUND(avg_churn * 100, 1) as monthly_churn_pct,
  ROUND(avg_ltv, 0) as avg_ltv,
  ROUND(avg_ltv * avg_conversion, 0) as expected_value_per_lead
FROM pricing_cohorts
ORDER BY customer_segment, price_point;
```
### 2. Revenue Forecast Model
```sql
-- Simple revenue forecast based on cohort trends
WITH historical_growth AS (
  SELECT 
    DATE_TRUNC('month', revenue_date) as month,
    SUM(mrr) as total_mrr,
    LAG(SUM(mrr), 1) OVER (ORDER BY DATE_TRUNC('month', revenue_date)) as prev_month_mrr,
    LAG(SUM(mrr), 3) OVER (ORDER BY DATE_TRUNC('month', revenue_date)) as prev_quarter_mrr
  FROM revenue
  WHERE revenue_date >= DATEADD('month', -12, CURRENT_DATE)
  GROUP BY 1
),
growth_rates AS (
  SELECT 
    AVG((total_mrr - prev_month_mrr) / NULLIF(prev_month_mrr, 0)) as avg_monthly_growth,
    AVG((total_mrr - prev_quarter_mrr) / NULLIF(prev_quarter_mrr, 0)) as avg_quarterly_growth
  FROM historical_growth
  WHERE prev_month_mrr IS NOT NULL
),
current_mrr AS (
  SELECT SUM(mrr) as current_total_mrr
  FROM revenue
  WHERE DATE_TRUNC('month', revenue_date) = DATE_TRUNC('month', CURRENT_DATE)
)
SELECT 
  DATEADD('month', month_offset, DATE_TRUNC('month', CURRENT_DATE)) as forecast_month,
  ROUND(
    current_total_mrr * POWER(1 + avg_monthly_growth, month_offset), 0
  ) as forecast_mrr,
  ROUND(
    current_total_mrr * POWER(1 + avg_monthly_growth, month_offset) * 12, 0
  ) as forecast_arr
FROM current_mrr
CROSS JOIN growth_rates
CROSS JOIN (SELECT 1 as month_offset UNION SELECT 2 UNION SELECT 3 
            UNION SELECT 4 UNION SELECT 5 UNION SELECT 6) as months
ORDER BY forecast_month;
```d Accrual**: Keep these separate and clearly labeled
2. **Ignoring Seasonality**: Many B2B businesses have Q4 spikes
3. **Over-Aggregation**: Segment analysis reveals hidden trends
4. **Point-in-Time Bias**: Always consider full customer lifecycle
5. **Manual Processes**: Automation reduces errors and saves time

## Key Takeaways

1. **Revenue ≠ Cash**: Understanding timing differences is crucial
2. **Retention Drives Growth**: NDR > 100% enables efficient scaling
3. **Segmentation Reveals Insights**: Aggregate metrics hide important patterns
4. **Leading Indicators Matter**: Bookings and pipeline predict future revenue
5. **Efficiency Metrics Scale**: Revenue per employee indicates operational leverage

---

*Next: [Module 4 - Product Analytics](04-product-analytics.md)*