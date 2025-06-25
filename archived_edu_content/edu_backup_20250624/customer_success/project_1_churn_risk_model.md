# Customer Success Analytics Project 1: Churn Risk Model Development

## Project Overview

As a Customer Success Analyst, you've been tasked with developing a comprehensive churn risk model. The company's gross revenue retention has dropped from 92% to 87% over the past two quarters, and the CCO needs a systematic way to identify and prevent churn before it happens.

## Learning Objectives

Through this project, you will:
1. Build a data-driven churn prediction model
2. Identify key behavioral indicators of churn risk
3. Segment customers by risk level and characteristics
4. Design targeted intervention strategies
5. Create an operational dashboard for CSMs

## Business Context

**Company Situation:**
- 40,000 active customers across SMB, Mid-Market, and Enterprise segments
- Current annual churn rate: 13% (target: <10%)
- 20 Customer Success Managers with 200:1 coverage ratio
- Average customer lifetime: 3.2 years
- No systematic early warning system in place

**Stakeholder Requirements:**
- "We're always surprised by churn - we need to see it coming" - CCO
- "I need to know which customers to focus on each week" - CSM Team Lead
- "What specific actions reduce churn risk?" - VP Customer Success
- "Can we prevent churn or just delay it?" - CFO

## Dataset Description

**Primary Tables:**

**customers**
- customer_id, customer_name, segment, industry, mrr, contract_start_date, employee_count

**customer_health_metrics**
- customer_id, date, health_score, usage_score, feature_adoption_score, support_score

**usage_daily**
- customer_id, date, active_users, api_calls, reports_generated, data_processed

**support_tickets**
- ticket_id, customer_id, created_date, priority, category, resolution_time, satisfaction_score

**customer_events**
- customer_id, event_date, event_type (churned, expanded, contracted, renewed)

**engagement_history**
- customer_id, engagement_date, type (QBR, training, check-in), attendees, outcome

## Part 1: Exploratory Data Analysis

### Task 1.1: Understand Historical Churn Patterns

Analyze churned customers to identify common characteristics.

```sql
-- Starter code: Expand and modify as needed
WITH churned_customers AS (
    SELECT 
        customer_id,
        event_date as churn_date
    FROM customer_events
    WHERE event_type = 'churned'
      AND event_date >= CURRENT_DATE - INTERVAL '12 months'
)
-- Analyze churn by segment, tenure, size, etc.
```

**Key Questions:**
- What's the churn rate by segment?
- How does churn vary by customer tenure?
- Are there seasonal patterns?
- What's the average customer value at churn?

### Task 1.2: Pre-Churn Behavior Analysis

Examine customer behavior in the 90 days before churn.

```sql
-- Analyze usage trends before churn
WITH churn_cohort AS (
    -- Define churned customers and their churn dates
),
usage_trends AS (
    -- Calculate usage metrics for 90 days pre-churn
)
-- Compare to retained customers
```

**Deliverables:**
- Usage decline patterns
- Support ticket trends
- Engagement drop-off rates
- Feature abandonment sequence

### Task 1.3: Survival Analysis

Calculate customer survival curves by cohort.

**Analysis Requirements:**
- Survival rates by month since acquisition
- Hazard rates by customer segment
- Critical risk periods identification

## Part 2: Feature Engineering

### Task 2.1: Create Behavioral Features

Develop features that capture churn risk signals.

```sql
-- Example feature: Usage trend
WITH usage_features AS (
    SELECT 
        customer_id,
        -- 30-day usage trend
        (SUM(CASE WHEN date >= CURRENT_DATE - 30 THEN active_users END) / 30.0) /
        NULLIF(SUM(CASE WHEN date >= CURRENT_DATE - 60 AND date < CURRENT_DATE - 30 THEN active_users END) / 30.0, 0) - 1 as usage_trend_30d,
        -- Add more features
    FROM usage_daily
    WHERE date >= CURRENT_DATE - 60
    GROUP BY customer_id
)
```

**Required Features:**
1. Usage trends (7, 30, 90 day)
2. Support ticket frequency and sentiment
3. Feature adoption velocity
4. Engagement recency and frequency
5. Contract value changes
6. Payment history indicators

### Task 2.2: Create Interaction Features

Some risks emerge from combinations of factors.

**Examples:**
- High support tickets + declining usage
- Near renewal + low engagement
- Price increase + low health score

### Task 2.3: Time-Based Features

Account for seasonality and time-based patterns.

**Consider:**
- Months until renewal
- Seasonality effects
- Days since last engagement
- Account age

## Part 3: Model Development

### Task 3.1: Build Initial Model

Start with a simple, interpretable model.

```python
# Pseudocode for model approach
# 1. Load feature matrix
# 2. Define target (churned within 90 days)
# 3. Split data (time-based split)
# 4. Train initial model (logistic regression or decision tree)
# 5. Evaluate performance
```

**Model Requirements:**
- Predict probability of churn in next 90 days
- Interpretable feature importance
- Minimum 80% recall for high-risk customers
- Actionable risk factors output

### Task 3.2: Model Validation

Validate model performance on holdout period.

**Validation Metrics:**
- Precision and recall by risk tier
- AUC-ROC curve
- Lift chart
- Feature importance stability

### Task 3.3: Risk Scoring Framework

Convert model output to operational risk scores.

```sql
-- Create risk tiers
WITH risk_scores AS (
    -- Your model output
),
risk_tiers AS (
    SELECT 
        customer_id,
        churn_probability,
        CASE 
            WHEN churn_probability >= 0.7 THEN 'Critical'
            WHEN churn_probability >= 0.4 THEN 'High'
            WHEN churn_probability >= 0.2 THEN 'Medium'
            ELSE 'Low'
        END as risk_tier,
        -- Top risk factors for this customer
    FROM risk_scores
)
```

## Part 4: Intervention Strategy Design

### Task 4.1: Risk-Based Playbooks

Design specific interventions for each risk profile.

**Framework:**
| Risk Profile | Characteristics | Intervention | Owner | Success Metrics |
|-------------|----------------|--------------|--------|-----------------|
| Usage Decline | -30% usage, healthy otherwise | Product coaching session | CSM | Usage recovery |
| Support Frustration | High tickets, low CSAT | Executive escalation | VP CS | CSAT improvement |
| Low Adoption | <3 features used | Enablement workshop | CS Ops | Feature activation |
| Renewal Risk | <90 days, low engagement | Business review | CSM | Renewal secured |

### Task 4.2: Prioritization Framework

CSMs can't address all risks simultaneously.

```sql
-- Prioritize interventions by impact and effort
WITH customer_priority AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        r.risk_score,
        c.mrr,
        c.mrr * r.churn_probability as revenue_at_risk,
        CASE 
            WHEN c.segment = 'Enterprise' THEN 1
            WHEN c.segment = 'Mid-Market' THEN 2
            ELSE 3
        END as segment_priority,
        -- Calculate intervention effort score
        CASE 
            WHEN r.primary_risk_factor = 'usage' THEN 2  -- Medium effort
            WHEN r.primary_risk_factor = 'support' THEN 3  -- High effort
            ELSE 1  -- Low effort
        END as effort_score
    FROM customers c
    JOIN risk_scores r ON c.customer_id = r.customer_id
    WHERE r.risk_tier IN ('Critical', 'High')
)
SELECT 
    customer_id,
    customer_name,
    risk_score,
    revenue_at_risk,
    revenue_at_risk / effort_score as impact_efficiency_score
FROM customer_priority
ORDER BY impact_efficiency_score DESC
LIMIT 50;  -- Top 50 for this week
```

### Task 4.3: Intervention Effectiveness Tracking

Design a system to measure what works.

**Requirements:**
- Track intervention execution
- Measure outcome (retained/churned)
- Calculate intervention ROI
- Refine playbooks based on results

## Part 5: Operational Implementation

### Task 5.1: CSM Dashboard Design

Create a daily dashboard for CSMs.

**Dashboard Components:**
1. **My Book of Business Health**
   - Overall health distribution
   - Week-over-week changes
   - Upcoming renewals at risk

2. **Priority Actions This Week**
   - Top 10 at-risk accounts
   - Specific intervention needed
   - Due dates

3. **Success Metrics**
   - Interventions completed
   - Save rate
   - Revenue retained

### Task 5.2: Automated Alerts

Design proactive alerting system.

```sql
-- Example alert logic
WITH alert_triggers AS (
    SELECT 
        customer_id,
        CASE 
            WHEN usage_drop > 50 AND days_since_last_contact > 30 THEN 'Urgent: Severe usage drop with no recent contact'
            WHEN churn_probability > 0.8 AND renewal_date < 60 THEN 'Critical: High churn risk approaching renewal'
            WHEN support_tickets_7d > 5 AND avg_csat < 3 THEN 'Support escalation needed'
        END as alert_message,
        assigned_csm
    FROM customer_risk_metrics
    WHERE [trigger conditions]
)
```

### Task 5.3: Executive Reporting

Design monthly executive dashboard.

**Key Metrics:**
- Churn rate trend
- Revenue retention
- Risk distribution
- Intervention success rate
- CSM efficiency metrics

## Deliverables

1. **Churn Analysis Report** (`churn_analysis.pdf`)
   - Historical patterns
   - Key risk factors identified
   - Model performance metrics
   - Business recommendations

2. **Risk Scoring Model** (`churn_risk_model.sql`)
   - Feature engineering code
   - Scoring logic
   - Validation results
   - Implementation guide

3. **Intervention Playbook** (`intervention_playbook.md`)
   - Risk profiles defined
   - Specific interventions per profile
   - Success metrics
   - CSM training guide

4. **Operational Dashboards**
   - CSM daily dashboard mockup
   - Executive monthly dashboard
   - Alert configuration

5. **ROI Analysis** (`churn_prevention_roi.xlsx`)
   - Cost of interventions
   - Revenue saved
   - Efficiency metrics
   - Resource requirements

## Evaluation Criteria

**Technical Excellence (30%)**
- Model accuracy and validation
- Feature engineering creativity
- Code quality and documentation
- Statistical rigor

**Business Impact (40%)**
- Actionability of insights
- Feasibility of interventions
- Clear prioritization logic
- ROI demonstration

**Operational Readiness (20%)**
- Dashboard usability
- Process documentation
- Training materials
- Scalability consideration

**Communication (10%)**
- Executive summary clarity
- Visual effectiveness
- Stakeholder alignment

## Tips for Success

1. **Start Simple**: Begin with basic features before complex engineering
2. **Talk to CSMs**: Understand their workflow and constraints
3. **Validate Assumptions**: Test your risk factors against actual outcomes
4. **Consider Capacity**: CSMs have limited time - prioritize impact
5. **Measure Everything**: Build measurement into your intervention design

## Bonus Challenges

1. **Uplift Modeling**: Predict which customers will respond to intervention
2. **Optimal Timing**: When is the best time to intervene?
3. **Segmented Models**: Build segment-specific models
4. **NLP on Support Tickets**: Extract risk signals from ticket text
5. **Economic Value**: Calculate CLV impact of prevention

## Timeline

- **Day 1-2**: Data exploration and churn analysis
- **Day 3-4**: Feature engineering and model building
- **Day 5**: Intervention strategy design
- **Day 6**: Dashboard and operational design
- **Day 7**: Documentation and presentation

## Success Story Example

"Using this model, Acme Corp reduced quarterly churn from 3.5% to 2.8%, saving $2.1M in ARR. CSMs report spending 40% less time on account research and more time on proactive customer engagement. The executive team now has visibility into retention risks 90 days in advance."

Remember: The goal isn't just to predict churn - it's to prevent it through actionable, timely interventions that CSMs can realistically execute.