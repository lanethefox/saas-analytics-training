# Module 1: SaaS Business Fundamentals

## Overview

Software as a Service (SaaS) businesses operate on fundamentally different economics than traditional software companies. Understanding these core metrics is essential for any business analyst in the modern tech ecosystem.

## The SaaS Business Model

### Subscription Economics
- **Recurring Revenue**: Predictable monthly/annual income streams
- **Customer Lifetime**: Multi-year relationships vs one-time purchases
- **Growth Compounds**: Each customer adds to a growing revenue base
- **Churn Impact**: Lost customers reduce future revenue permanently

### Key Characteristics
1. **High Upfront Costs**: Customer acquisition often exceeds first-year revenue
2. **Economies of Scale**: Marginal cost near zero for additional users
3. **Network Effects**: Product value increases with more users
4. **Sticky Relationships**: High switching costs reduce churn

## Core SaaS Metrics

### 1. Monthly Recurring Revenue (MRR)

**Definition**: Predictable revenue generated each month from subscriptions

**Components**:
```
MRR = Σ(Active Subscriptions × Monthly Price)
```

**Breakdown**:
- **New MRR**: Revenue from new customers
- **Expansion MRR**: Upgrades and add-ons from existing customers
- **Contraction MRR**: Downgrades from existing customers
- **Churn MRR**: Lost revenue from cancellations
- **Net New MRR**: New + Expansion - Contraction - Churn
**Business Applications**:
- **Revenue Forecasting**: Predict future revenue based on MRR trends
- **Growth Tracking**: Monitor month-over-month growth rates
- **Segment Analysis**: Compare MRR by customer segment, plan type, or region

### 2. Annual Recurring Revenue (ARR)

**Definition**: Annualized value of recurring revenue
```
ARR = MRR × 12
```

**Use Cases**:
- **Valuation Metrics**: Companies often valued at multiples of ARR
- **Enterprise Deals**: Annual contracts reported as ARR
- **Board Reporting**: Strategic metric for long-term planning

### 3. Customer Churn Rate

**Definition**: Percentage of customers who cancel in a given period

**Logo Churn**:
```
Logo Churn Rate = (Customers Lost / Starting Customers) × 100
```

**Revenue Churn**:
```
Revenue Churn Rate = (MRR Lost / Starting MRR) × 100
```

**Critical Insights**:
- **Negative Revenue Churn**: When expansion exceeds churn (ideal state)
- **Cohort Analysis**: Track churn by customer acquisition month
- **Early Indicators**: Usage decline often precedes churn
### 4. Customer Acquisition Cost (CAC)

**Definition**: Total cost to acquire a new customer

```
CAC = (Sales Costs + Marketing Costs) / New Customers Acquired
```

**Components**:
- **Paid Marketing**: Ad spend, campaigns, events
- **Sales Salaries**: SDR, AE compensation and overhead
- **Tools & Systems**: CRM, marketing automation costs
- **Content & Creative**: Production costs for marketing materials

**Blended vs Channel CAC**:
- **Blended CAC**: Average across all channels
- **Channel CAC**: Specific to each acquisition source
- **Payback Period**: Months to recover CAC from customer revenue

### 5. Customer Lifetime Value (CLV/LTV)

**Definition**: Total revenue expected from a customer relationship

**Simple Formula**:
```
CLV = (Average Revenue per Customer × Gross Margin %) / Churn Rate
```

**Advanced Formula**:
```
CLV = Σ(t=0 to n) [(Revenue_t - Costs_t) / (1 + Discount Rate)^t]
```

**LTV:CAC Ratio**:
- **<1:1**: Losing money on each customer
- **3:1**: Healthy SaaS benchmark
- **>5:1**: May be under-investing in growth
### 6. Net Revenue Retention (NRR)

**Definition**: Revenue growth from existing customers including expansions and churn

```
NRR = (Starting MRR + Expansion - Contraction - Churn) / Starting MRR × 100
```

**Benchmarks**:
- **<100%**: Shrinking revenue base
- **100-110%**: Stable with modest growth
- **>120%**: Best-in-class expansion
- **>140%**: Exceptional (often usage-based pricing)

### 7. Gross Margin

**Definition**: Revenue remaining after direct service costs

```
Gross Margin = (Revenue - Cost of Goods Sold) / Revenue × 100
```

**SaaS COGS Includes**:
- **Infrastructure**: Cloud hosting, data storage
- **Support Costs**: Customer success, technical support
- **Third-Party Licenses**: Embedded software costs
- **DevOps**: Service delivery engineering

**Benchmarks**:
- **<70%**: Infrastructure-heavy or high-touch service
- **70-80%**: Typical SaaS range
- **>80%**: Highly efficient operations

## Common Stakeholder Questions

### From the CEO/Board
1. "What's our current ARR and growth rate?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Show me our recurring revenue and how fast we're growing | `SELECT sum(mrr) FROM subscriptions WHERE status = 'active'` + month-over-month growth calculation |

2. "How does our unit economics compare to industry benchmarks?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are we making money efficiently compared to competitors? | Calculate LTV:CAC ratio from `customers` table, compare CAC from `marketing_spend` + `sales_costs` |

3. "What's driving the change in churn rate?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Why are we losing customers differently than before? | Analyze `churn_events` by segment, time period, usage patterns from `product_events` |

4. "Are we efficiently converting our TAM into revenue?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How much of our market opportunity are we capturing? | Compare current ARR to addressable market size, filter `leads` by target segments |
### From the CFO
1. "What's our CAC payback period by channel?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How long until each marketing channel pays for itself? | Join `customer_acquisition_costs` with `subscriptions`, group by acquisition_channel, calculate months to recover CAC |

2. "How is gross margin trending with scale?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are we becoming more profitable as we grow? | Calculate (revenue - cogs) / revenue from `financial_statements` over time, correlate with customer count |

3. "What's the revenue impact of our pricing changes?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Did our price adjustments increase or decrease total revenue? | Compare MRR before/after price change dates from `pricing_changes` and `subscriptions` tables |

4. "Can you model different growth scenarios for next year?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Show me optimistic, realistic, and conservative revenue projections | Use historical growth rates from `mrr_movements`, apply different acquisition and churn scenarios to forecast |

### From Sales Leadership
1. "Which customer segments have the highest LTV?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which types of customers are most valuable long-term? | Group `customers` by segment, calculate average LTV using revenue and churn data by segment |

2. "What's our average deal size trend?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are our new customers buying more or less over time? | Calculate average contract value from `deals` or initial MRR from `subscriptions` by month |

3. "How does time-to-close impact customer lifetime value?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do deals that close faster/slower perform differently? | Join `deals` (close duration) with `customers` (LTV), analyze correlation and segment performance |

4. "What percentage of customers expand in year one?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How many customers increase their spending in their first year? | Filter `mrr_movements` for expansion events within 12 months of `first_payment_date` |

### From Marketing
1. "What's the ROI on our marketing spend by channel?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Which marketing channels give us the best return on investment? | Join `marketing_spend` by channel with resulting `customer_acquisitions` and their LTV |

2. "How do different campaigns impact long-term retention?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Do customers from certain campaigns stay longer? | Connect `utm_source` from `customers` to retention rates from `subscription_events` |

3. "Which content pieces correlate with higher conversion rates?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What content leads to more sales? | Track content engagement from `page_views` to conversion events in `deals` or `subscriptions` |

4. "What's our cost per qualified lead by source?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How much does each channel cost per quality prospect? | Calculate spend per channel divided by qualified leads from `leads` WHERE status = 'qualified' |

## Standard SaaS Reports

### 1. MRR Movement Report
```sql
-- Monthly MRR movement waterfall
WITH mrr_movement AS (
  SELECT 
    DATE_TRUNC('month', date) as month,
    SUM(CASE WHEN movement_type = 'new' THEN mrr_amount ELSE 0 END) as new_mrr,
    SUM(CASE WHEN movement_type = 'expansion' THEN mrr_amount ELSE 0 END) as expansion_mrr,
    SUM(CASE WHEN movement_type = 'contraction' THEN mrr_amount ELSE 0 END) as contraction_mrr,
    SUM(CASE WHEN movement_type = 'churn' THEN mrr_amount ELSE 0 END) as churned_mrr
  FROM mrr_changes
  GROUP BY 1
)
SELECT 
  month,
  new_mrr,
  expansion_mrr,
  -contraction_mrr as contraction_mrr,
  -churned_mrr as churned_mrr,
  new_mrr + expansion_mrr - contraction_mrr - churned_mrr as net_new_mrr
FROM mrr_movement
ORDER BY month;
```
### 2. Cohort Retention Analysis
```sql
-- Customer retention by monthly cohort
WITH cohort_data AS (
  SELECT 
    c.customer_id,
    DATE_TRUNC('month', c.first_payment_date) as cohort_month,
    DATE_TRUNC('month', s.date) as activity_month,
    s.mrr
  FROM customers c
  JOIN subscriptions s ON c.customer_id = s.customer_id
  WHERE s.status = 'active'
),
cohort_size AS (
  SELECT 
    cohort_month,
    COUNT(DISTINCT customer_id) as cohort_customers
  FROM cohort_data
  GROUP BY 1
),
retention_table AS (
  SELECT 
    cd.cohort_month,
    DATEDIFF('month', cd.cohort_month, cd.activity_month) as months_since_start,
    COUNT(DISTINCT cd.customer_id) as retained_customers
  FROM cohort_data cd
  GROUP BY 1, 2
)
SELECT 
  r.cohort_month,
  r.months_since_start,
  r.retained_customers,
  ROUND(100.0 * r.retained_customers / c.cohort_customers, 1) as retention_rate
FROM retention_table r
JOIN cohort_size c ON r.cohort_month = c.cohort_month
ORDER BY 1, 2;
```
### 3. Unit Economics Dashboard
```sql
-- Key unit economics metrics by customer segment
WITH customer_metrics AS (
  SELECT 
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) as customers,
    AVG(c.total_revenue) as avg_revenue,
    AVG(c.customer_lifetime_months) as avg_lifetime_months,
    AVG(c.acquisition_cost) as avg_cac
  FROM customers c
  WHERE c.first_payment_date >= DATEADD('month', -12, CURRENT_DATE)
  GROUP BY 1
)
SELECT 
  customer_segment,
  customers,
  ROUND(avg_revenue, 2) as avg_customer_revenue,
  ROUND(avg_lifetime_months, 1) as avg_lifetime_months,
  ROUND(avg_cac, 2) as avg_cac,
  ROUND(avg_revenue / avg_cac, 2) as ltv_cac_ratio,
  ROUND(avg_cac / (avg_revenue / avg_lifetime_months), 1) as payback_months
FROM customer_metrics
ORDER BY ltv_cac_ratio DESC;
```

## Key Takeaways

1. **Recurring Revenue is King**: MRR/ARR drive valuation and planning
2. **Retention > Acquisition**: Keeping customers is cheaper than finding new ones
3. **Unit Economics Matter**: LTV:CAC determines sustainable growth
4. **Compound Growth**: Small improvements in retention have massive long-term impact
5. **Segmentation is Critical**: Different customer types have different economics

## Action Items for Analysts

1. **Build a MRR Movement Model**: Track all revenue changes daily
2. **Create Cohort Dashboards**: Monitor retention patterns over time
3. **Calculate True CAC**: Include all costs, not just ad spend
4. **Segment Everything**: Always analyze metrics by customer characteristics
5. **Automate Reporting**: These metrics need constant monitoring

---

*Next: [Module 2 - Customer Analytics](02-customer-analytics.md)*