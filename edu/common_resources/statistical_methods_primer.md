# Statistical Methods Primer for Business Analysts

## Introduction

This primer covers essential statistical concepts and methods used in business analytics. Each concept is explained with practical examples from our B2B SaaS context, making the theory immediately applicable to real-world analysis.

## 1. Descriptive Statistics

### Measures of Central Tendency

**Mean (Average)**
- **Definition**: Sum of all values divided by count
- **When to use**: When data is normally distributed without extreme outliers
- **Business example**: Average Revenue Per User (ARPU)
```sql
SELECT AVG(monthly_recurring_revenue) as arpu
FROM customers
WHERE customer_status = 'active';
```
- **Limitation**: Sensitive to outliers (one enterprise customer can skew results)

**Median**
- **Definition**: Middle value when data is ordered
- **When to use**: When data has outliers or is skewed
- **Business example**: Median deal size shows typical transaction
```sql
SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_recurring_revenue) as median_mrr
FROM customers;
```
- **Advantage**: Not affected by extreme values

**Mode**
- **Definition**: Most frequently occurring value
- **When to use**: For categorical data or finding common patterns
- **Business example**: Most common subscription plan
```sql
SELECT plan_type, COUNT(*) as frequency
FROM subscriptions
GROUP BY plan_type
ORDER BY frequency DESC
LIMIT 1;
```

### Measures of Spread

**Range**
- **Definition**: Difference between maximum and minimum values
- **Business use**: Understanding the span of customer values
```sql
SELECT 
    MAX(monthly_recurring_revenue) - MIN(monthly_recurring_revenue) as mrr_range
FROM customers
WHERE customer_status = 'active';
```

**Standard Deviation**
- **Definition**: Average distance from the mean
- **Business use**: Measuring consistency in metrics
- **Interpretation**: 
  - Low SD = values cluster near mean (consistent)
  - High SD = values spread out (variable)
```sql
SELECT 
    STDDEV(monthly_recurring_revenue) as mrr_stddev,
    AVG(monthly_recurring_revenue) as mrr_mean
FROM customers;
```

**Percentiles and Quartiles**
- **Definition**: Values below which a percentage of data falls
- **Common percentiles**:
  - 25th percentile (Q1): First quartile
  - 50th percentile (Q2): Median
  - 75th percentile (Q3): Third quartile
  - 90th/95th/99th: Often used for SLAs
```sql
SELECT 
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY response_time) as p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY response_time) as median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY response_time) as p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time) as p95
FROM support_tickets;
```

## 2. Probability Distributions

### Normal Distribution
- **Characteristics**: Bell-shaped, symmetric around mean
- **68-95-99.7 Rule**: 
  - 68% of data within 1 SD of mean
  - 95% within 2 SD
  - 99.7% within 3 SD
- **Business application**: Many metrics follow normal distribution (e.g., daily revenue)

### Identifying Outliers
```sql
WITH stats AS (
    SELECT 
        AVG(monthly_recurring_revenue) as mean_mrr,
        STDDEV(monthly_recurring_revenue) as stddev_mrr
    FROM customers
)
SELECT c.*
FROM customers c, stats s
WHERE c.monthly_recurring_revenue > s.mean_mrr + (3 * s.stddev_mrr)
   OR c.monthly_recurring_revenue < s.mean_mrr - (3 * s.stddev_mrr);
```

### Skewed Distributions
- **Right-skewed (Positive)**: Long tail to the right
  - Common in revenue data (few high-value customers)
  - Mean > Median
- **Left-skewed (Negative)**: Long tail to the left
  - Less common in business metrics
  - Mean < Median

## 3. Correlation and Causation

### Correlation Coefficient (r)
- **Range**: -1 to +1
- **Interpretation**:
  - r = 1: Perfect positive correlation
  - r = 0: No linear correlation
  - r = -1: Perfect negative correlation
  - |r| > 0.7: Strong correlation
  - 0.3 < |r| < 0.7: Moderate correlation
  - |r| < 0.3: Weak correlation

**Example: Feature usage vs. retention**
```sql
SELECT 
    CORR(feature_usage_days, retention_months) as correlation
FROM customer_metrics;
```

### Important Distinctions
- **Correlation ≠ Causation**: Two variables moving together doesn't mean one causes the other
- **Confounding variables**: Hidden factors that affect both variables
- **Business example**: Ice cream sales correlate with swimming pool accidents (both caused by summer weather)

## 4. Hypothesis Testing

### Components of Hypothesis Testing
1. **Null Hypothesis (H₀)**: No difference or effect exists
2. **Alternative Hypothesis (H₁)**: Difference or effect exists
3. **Significance Level (α)**: Typically 0.05 (5% chance of false positive)
4. **P-value**: Probability of seeing results if H₀ is true

### Business Applications

**A/B Testing Example**
- H₀: New pricing has no effect on conversion
- H₁: New pricing changes conversion rate
- If p-value < 0.05: Reject H₀ (pricing has effect)
- If p-value ≥ 0.05: Cannot reject H₀ (insufficient evidence)

### Common Tests

**T-Test**: Comparing means of two groups
```sql
-- Compare ARPU between two customer segments
SELECT 
    customer_segment,
    AVG(monthly_recurring_revenue) as avg_mrr,
    COUNT(*) as sample_size,
    STDDEV(monthly_recurring_revenue) as stddev_mrr
FROM customers
WHERE customer_segment IN ('SMB', 'Enterprise')
GROUP BY customer_segment;
```

**Chi-Square Test**: Testing relationships between categorical variables
- Example: Is industry related to churn rate?

## 5. Confidence Intervals

### Definition
- Range likely to contain the true population parameter
- 95% CI: If we repeated sampling 100 times, 95 intervals would contain true value

### Business Example
"We are 95% confident that our true churn rate is between 4.2% and 5.8%"

### Calculating Confidence Intervals
```sql
WITH churn_stats AS (
    SELECT 
        AVG(CASE WHEN churned THEN 1 ELSE 0 END) as churn_rate,
        COUNT(*) as n
    FROM customers
)
SELECT 
    churn_rate,
    churn_rate - 1.96 * SQRT(churn_rate * (1 - churn_rate) / n) as lower_ci,
    churn_rate + 1.96 * SQRT(churn_rate * (1 - churn_rate) / n) as upper_ci
FROM churn_stats;
```

## 6. Time Series Analysis

### Components
1. **Trend**: Long-term direction
2. **Seasonality**: Regular patterns (weekly, monthly, yearly)
3. **Cyclical**: Long-term fluctuations
4. **Irregular**: Random variation

### Moving Averages
- Smooth out short-term fluctuations
- Reveal underlying trends

```sql
SELECT 
    date,
    daily_revenue,
    AVG(daily_revenue) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as ma7_revenue
FROM daily_metrics;
```

### Growth Rates
**Month-over-Month (MoM)**
```sql
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(revenue) as total_revenue
    FROM daily_revenue
    GROUP BY 1
)
SELECT 
    month,
    total_revenue,
    LAG(total_revenue) OVER (ORDER BY month) as prev_month,
    (total_revenue - LAG(total_revenue) OVER (ORDER BY month)) / 
    LAG(total_revenue) OVER (ORDER BY month) * 100 as mom_growth
FROM monthly_revenue;
```

## 7. Segmentation and Cohort Analysis

### RFM Analysis (Recency, Frequency, Monetary)
```sql
WITH rfm_scores AS (
    SELECT 
        customer_id,
        NTILE(5) OVER (ORDER BY last_order_date DESC) as recency_score,
        NTILE(5) OVER (ORDER BY order_count DESC) as frequency_score,
        NTILE(5) OVER (ORDER BY total_revenue DESC) as monetary_score
    FROM customer_summary
)
SELECT 
    recency_score || frequency_score || monetary_score as rfm_segment,
    COUNT(*) as customer_count
FROM rfm_scores
GROUP BY 1
ORDER BY 1;
```

### Cohort Retention
```sql
SELECT 
    DATE_TRUNC('month', first_purchase_date) as cohort_month,
    months_since_first_purchase,
    COUNT(DISTINCT CASE WHEN made_purchase THEN customer_id END) * 100.0 / 
    COUNT(DISTINCT customer_id) as retention_rate
FROM customer_cohorts
GROUP BY 1, 2;
```

## 8. Statistical Significance in Business Context

### Sample Size Considerations
- Larger samples → More reliable results
- Minimum sample size depends on:
  - Expected effect size
  - Desired confidence level
  - Baseline conversion rate

### Practical vs. Statistical Significance
- **Statistical significance**: Result unlikely due to chance
- **Practical significance**: Result meaningful for business
- Example: 0.1% conversion increase might be statistically significant but not worth implementation cost

### Common Pitfalls
1. **Multiple testing**: Testing many hypotheses increases false positive risk
2. **Selection bias**: Non-representative samples
3. **Survivorship bias**: Only analyzing successful outcomes
4. **Simpson's Paradox**: Trend reverses when groups combined

## 9. Forecasting Basics

### Simple Methods
**Naive Forecast**: Next value = Current value
**Moving Average**: Next value = Average of last n periods
**Trend Projection**: Extend historical trend line

### Measuring Forecast Accuracy
- **MAE (Mean Absolute Error)**: Average of absolute errors
- **MAPE (Mean Absolute Percentage Error)**: Percentage terms
- **RMSE (Root Mean Square Error)**: Penalizes large errors

```sql
SELECT 
    AVG(ABS(actual - forecast)) as mae,
    AVG(ABS(actual - forecast) / actual) * 100 as mape,
    SQRT(AVG(POWER(actual - forecast, 2))) as rmse
FROM forecast_results;
```

## 10. Practical Application Framework

### Statistical Analysis Process
1. **Define the question**: What business problem are we solving?
2. **Collect data**: Ensure quality and relevance
3. **Explore data**: Visualize and summarize
4. **Apply appropriate method**: Match technique to question
5. **Validate results**: Check assumptions and limitations
6. **Communicate findings**: Focus on business impact

### Key Questions to Ask
- Is my sample representative?
- Are there confounding variables?
- Is the effect size meaningful?
- How confident am I in the results?
- What are the business implications?

### Tools and Techniques Summary

| Business Question | Statistical Method | Key Metric |
|------------------|-------------------|------------|
| What's our typical customer value? | Median, percentiles | Median MRR |
| Are customers in segment A more valuable? | T-test | P-value, effect size |
| Does feature usage predict retention? | Correlation, regression | Correlation coefficient |
| Is our new flow better? | A/B test | Conversion rate, p-value |
| What will revenue be next quarter? | Time series forecast | MAPE |
| Which customers are similar? | Clustering | Segment profiles |

## Remember
- Statistics support decision-making, not replace it
- Always consider business context
- Communicate uncertainty honestly
- Focus on actionable insights
- Validate with domain expertise