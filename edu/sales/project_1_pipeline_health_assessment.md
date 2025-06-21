# Sales Analytics Project 1: Pipeline Health Assessment

## Project Overview

As a Sales Operations Analyst at our B2B SaaS company, you've been asked by the VP of Sales to conduct a comprehensive pipeline health assessment. The sales team has been missing quarterly targets, and leadership needs to understand why and what actions to take.

## Learning Objectives

Through this project, you will:
1. Analyze pipeline coverage and identify gaps
2. Diagnose funnel bottlenecks using conversion analysis
3. Identify at-risk opportunities requiring intervention
4. Create actionable recommendations with measurable impact
5. Present findings to sales leadership

## Business Context

**Company Situation:**
- Q3 target: $5M in new bookings
- Current quarter bookings: $2.8M (8 weeks into quarter)
- Historical quarterly attainment: 85-95%
- Sales team: 20 reps across 3 segments (Enterprise, Mid-Market, SMB)

**Stakeholder Concerns:**
- "Do we have enough pipeline to hit our target?"
- "Where are deals getting stuck?"
- "Which opportunities need immediate attention?"
- "How can we improve our win rate?"

## Dataset Description

You have access to the following tables:

**opportunities**
- opportunity_id, account_id, sales_rep_id, amount, stage, created_date, close_date, last_activity_date

**opportunity_history**
- opportunity_id, stage, changed_date, days_in_stage

**sales_targets**
- sales_rep_id, quarter, target_amount, segment

**accounts**
- account_id, account_name, segment, industry, employee_count

**sales_activities**
- activity_id, opportunity_id, activity_type, activity_date

## Part 1: Pipeline Coverage Analysis

### Task 1.1: Calculate Pipeline Coverage Ratio

Determine if there's sufficient pipeline to meet Q3 targets.

```sql
-- Starter code: Modify and expand as needed
WITH current_pipeline AS (
    SELECT 
        SUM(amount) as total_pipeline
    FROM opportunities
    WHERE stage NOT IN ('Closed Won', 'Closed Lost')
      AND expected_close_date <= '2024-09-30'
)
-- Add target calculation and coverage ratio
```

**Deliverable**: Pipeline coverage by segment and overall

### Task 1.2: Pipeline Generation Trend

Analyze pipeline creation rate to project end-of-quarter coverage.

**Questions to answer:**
- What's the weekly pipeline generation rate?
- At current rates, will we have enough pipeline?
- Which segments are under-generating pipeline?

### Task 1.3: Pipeline Quality Assessment

Not all pipeline is equal. Assess quality using:
- Age of opportunities
- Engagement level (days since last activity)
- Historical conversion rates by stage

**Deliverable**: Adjusted pipeline value based on quality factors

## Part 2: Funnel Analysis

### Task 2.1: Stage Conversion Rates

Calculate conversion rates between each stage.

```sql
-- Analyze how opportunities flow through stages
WITH stage_transitions AS (
    -- Your code here
)
```

**Key metrics:**
- Conversion rate by stage
- Average days in each stage
- Identification of bottleneck stages

### Task 2.2: Conversion Rate Trends

Compare current conversion rates to historical benchmarks.

**Analysis requirements:**
- Month-over-month conversion trends
- Segment-specific conversion patterns
- Rep performance distribution

### Task 2.3: Lost Opportunity Analysis

Understand why deals are being lost.

**Questions to answer:**
- At which stages do we lose most deals?
- What's the average deal size of lost opportunities?
- Are certain reps/segments losing more deals?

## Part 3: At-Risk Opportunity Identification

### Task 3.1: Stalled Deals

Identify opportunities that need immediate attention.

```sql
-- Find stalled opportunities
-- Consider: time in stage, days since last activity, close date proximity
```

**Criteria for at-risk:**
- In same stage >30 days (varies by stage)
- No activity in last 14 days
- Close date in past or <30 days future
- Deal size >$50K

### Task 3.2: Risk Scoring Model

Create a simple risk score for each opportunity.

**Risk factors to consider:**
- Days in current stage vs. average
- Activity recency
- Number of stakeholders engaged
- Push count (times close date moved)

**Deliverable**: List of top 20 at-risk opportunities with risk scores

### Task 3.3: Intervention Recommendations

For each at-risk opportunity, suggest specific actions.

## Part 4: Win Rate Optimization

### Task 4.1: Win Rate Analysis

Calculate win rates by multiple dimensions.

```sql
-- Analyze win rates by segment, rep, deal size, etc.
```

**Required analysis:**
- Overall win rate and trend
- Win rate by segment
- Win rate by deal size bands
- Rep performance distribution

### Task 4.2: Win Rate Drivers

Identify factors that correlate with higher win rates.

**Factors to analyze:**
- Sales cycle length
- Number of activities
- Multi-threading (stakeholders engaged)
- Lead source

### Task 4.3: Improvement Opportunities

Based on analysis, identify top 3 ways to improve win rate.

## Part 5: Actionable Recommendations

### Task 5.1: Executive Summary

Create a one-page executive summary including:
- Current pipeline health status (Red/Yellow/Green)
- Probability of hitting Q3 target
- Top 3 issues identified
- Top 3 recommended actions

### Task 5.2: Detailed Action Plan

For each recommendation, provide:
- Specific actions to take
- Owner and timeline
- Expected impact (quantified)
- Success metrics

### Task 5.3: Pipeline Review Framework

Design a weekly pipeline review process including:
- Key metrics to track
- Warning indicators
- Review meeting agenda
- Rep coaching topics

## Deliverables

1. **SQL Analysis File** (`pipeline_health_queries.sql`)
   - All queries used in analysis
   - Clear comments explaining logic
   - Results summaries

2. **Executive Presentation** (`pipeline_health_assessment.pdf`)
   - 10-slide deck for VP of Sales
   - Visual pipeline flow diagram
   - Key findings and recommendations
   - Appendix with detailed analysis

3. **At-Risk Opportunity Report** (`at_risk_opportunities.csv`)
   - List of opportunities requiring intervention
   - Risk scores and reasons
   - Recommended actions per opportunity

4. **Pipeline Dashboard Mockup**
   - Sketch of automated dashboard
   - Key metrics to include
   - Update frequency requirements

## Evaluation Criteria

Your project will be evaluated on:

1. **Technical Accuracy (30%)**
   - Correct SQL calculations
   - Appropriate statistical methods
   - Data quality handling

2. **Business Insight (40%)**
   - Depth of analysis
   - Actionability of recommendations
   - Understanding of sales process

3. **Communication (20%)**
   - Clarity of presentation
   - Visual effectiveness
   - Executive-ready insights

4. **Completeness (10%)**
   - All deliverables provided
   - Questions thoroughly answered
   - Professional formatting

## Tips for Success

1. **Start with the big picture**: Understand overall pipeline health before diving into details
2. **Use multiple perspectives**: Same data can tell different stories
3. **Focus on actionability**: Every insight should lead to a specific action
4. **Consider the audience**: VP of Sales needs strategic insights, not technical details
5. **Validate findings**: Cross-check results using different approaches

## Bonus Challenges

For those seeking additional challenge:

1. **Predictive Modeling**: Build a simple model to predict which opportunities will close
2. **Competitive Analysis**: If competitive data available, analyze win/loss by competitor
3. **ROI Calculation**: Estimate ROI of your recommendations
4. **Automation Plan**: Design automated alerts for pipeline health

## Resources

- SQL query templates in `/common_resources/sql_library/sales/`
- Visualization best practices guide
- Sample executive presentation format
- Industry benchmark data for win rates

## Submission Instructions

1. Fork the project repository
2. Create branch: `pipeline-health-[your-name]`
3. Commit all deliverables to `/projects/sales/project_1/`
4. Submit pull request with summary of findings

## Timeline

- **Data Exploration**: 2 days
- **Analysis**: 3 days
- **Recommendations**: 1 day
- **Presentation Prep**: 1 day
- **Total**: 1 week

Good luck! Remember, your analysis could directly impact how the sales team operates and whether they hit their targets.