# Business Analytics Training Index

## Training Modules

### [Introduction](00-introduction.md)
Welcome to the comprehensive business analytics training program designed to bridge technical SQL skills with practical business applications.

### [Module 1: SaaS Business Fundamentals](01-saas-fundamentals.md)
- Understanding subscription economics
- Core metrics: MRR, ARR, CAC, LTV, Churn
- Unit economics and growth dynamics
- Common stakeholder questions and reports

### [Module 2: Customer Analytics](02-customer-analytics.md)
- Customer lifecycle and segmentation
- Health scores and engagement metrics
- Churn prediction and prevention
- Customer journey analytics

### [Module 3: Revenue Analytics](03-revenue-analytics.md)
- Revenue recognition principles
- Growth metrics and expansion tracking
- Pricing and discounting analysis
- Revenue forecasting techniques

### [Module 4: Product Analytics](04-product-analytics.md)
- User engagement and adoption metrics
- Feature usage and value analysis
- Product performance monitoring
- Behavioral analytics and segmentation

### [Module 5: Marketing Analytics](05-marketing-analytics.md)
- Multi-touch attribution models
- Campaign ROI and effectiveness
- Lead generation and conversion
- Content performance tracking

### [Module 6: Sales Analytics](06-sales-analytics.md)
- Pipeline management and velocity
- Win/loss analysis
- Sales performance and productivity
- Territory and quota planning

### [Module 7: Operations Analytics](07-operations-analytics.md)
- Support metrics and efficiency
- Infrastructure reliability and costs
- Implementation and onboarding
- Process optimization

### [Module 8: Executive Reporting](08-executive-reporting.md)
- Strategic KPIs and board metrics
- Competitive intelligence
- Scenario planning
- Value creation measurement

## Quick Reference Guides

### Key Metrics by Function

**Growth Metrics**
- MRR/ARR Growth Rate
- Net Revenue Retention (NRR)
- Customer Acquisition Cost (CAC)
- LTV:CAC Ratio
- Payback Period

**Efficiency Metrics**
- Magic Number
- Rule of 40
- Gross Margin
- Sales Efficiency
- Burn Multiple

**Health Metrics**
- Customer Health Score
- Net Promoter Score (NPS)
- Product Stickiness (DAU/MAU)
- Support CSAT
- Employee Satisfaction

### Common SQL Patterns

**Cohort Analysis**
```sql
WITH cohorts AS (
  SELECT 
    DATE_TRUNC('month', first_payment_date) as cohort_month,
    customer_id
  FROM customers
)
-- Build retention analysis
```

**Period-over-Period Comparison**
```sql
WITH current_period AS (
  SELECT metrics FROM table WHERE period = 'current'
),
prior_period AS (
  SELECT metrics FROM table WHERE period = 'prior'
)
-- Calculate growth rates
```

**Moving Averages**
```sql
AVG(metric) OVER (
  ORDER BY date 
  ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
) as rolling_30_day_avg
```

### Stakeholder Communication Tips

1. **For Executives**: Focus on trends and strategic implications
2. **For Managers**: Provide actionable insights with clear next steps
3. **For Technical Teams**: Include methodology and data quality notes
4. **For Investors**: Emphasize growth, efficiency, and predictability

## Resources for Continued Learning

### Books
- "Lean Analytics" by Croll & Yoskovitz
- "The Hard Thing About Hard Things" by Ben Horowitz
- "Measure What Matters" by John Doerr

### Online Resources
- SaaStr for SaaS metrics benchmarks
- First Round Review for startup analytics
- Mode Analytics SQL Tutorial
- dbt Learn for transformation best practices

### Communities
- LocallyOptimistic Slack
- Analytics Engineering Roundup
- Growth Hackers Community
- Revenue Collective

## Final Thoughts

Business analytics is both an art and a science. While this training provides the foundation, true mastery comes from:

1. **Curiosity**: Always ask "why" behind the numbers
2. **Context**: Understand the business before analyzing data
3. **Communication**: Translate insights into action
4. **Continuous Learning**: Industries and metrics evolve
5. **Impact Focus**: Measure success by decisions influenced

Remember: You're not just an analyst—you're a strategic business partner who happens to be great with data.

---

*Thank you for completing the Business Analytics Training. Now go forth and drive impact through data!*