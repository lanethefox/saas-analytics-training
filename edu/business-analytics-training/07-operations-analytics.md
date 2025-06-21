# Module 7: Operations Analytics

## Overview

Operations analytics focuses on optimizing the internal processes that deliver value to customers. In SaaS businesses, operational efficiency directly impacts gross margins, customer satisfaction, and scalability. This module covers metrics across support, infrastructure, implementation, and service delivery.

## The Operations Analytics Framework

### Key Operational Domains

1. **Customer Support**: Ticket resolution, satisfaction
2. **Infrastructure**: Uptime, performance, costs
3. **Implementation**: Onboarding, time to value
4. **Service Delivery**: SLAs, quality metrics
5. **Internal Processes**: Efficiency, automation

### Operational Excellence Goals

- **Scalability**: Handle growth without linear cost increase
- **Reliability**: Consistent service delivery
- **Efficiency**: Maximize output per resource
- **Quality**: Meet or exceed customer expectations
- **Agility**: Adapt quickly to changes

## Core Operations Metrics

### 1. Customer Support Metrics

**Ticket Volume and Resolution**:
```sql
-- Support ticket analytics
WITH ticket_metrics AS (
  SELECT 
    DATE_TRUNC('week', created_date) as week,
    ticket_priority,
    ticket_category,
    COUNT(*) as tickets_created,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as tickets_resolved,
    AVG(CASE WHEN status = 'resolved' THEN 
        DATEDIFF('hour', created_date, resolved_date) END) as avg_resolution_hours,
    AVG(satisfaction_score) as avg_csat,
    COUNT(CASE WHEN first_response_time <= sla_target THEN 1 END) as sla_met,
    COUNT(CASE WHEN escalated = 1 THEN 1 END) as escalated_tickets
  FROM support_tickets
  WHERE created_date >= DATEADD('month', -3, CURRENT_DATE)
  GROUP BY week, ticket_priority, ticket_category
)SELECT 
  week,
  ticket_priority,
  SUM(tickets_created) as total_tickets,
  SUM(tickets_resolved) as resolved_tickets,
  ROUND(100.0 * SUM(tickets_resolved) / NULLIF(SUM(tickets_created), 0), 1) as resolution_rate,
  ROUND(AVG(avg_resolution_hours), 1) as avg_resolution_hours,
  ROUND(AVG(avg_csat), 2) as avg_satisfaction,
  ROUND(100.0 * SUM(sla_met) / NULLIF(SUM(tickets_created), 0), 1) as sla_compliance,
  ROUND(100.0 * SUM(escalated_tickets) / NULLIF(SUM(tickets_created), 0), 1) as escalation_rate
FROM ticket_metrics
GROUP BY week, ticket_priority
ORDER BY week DESC, ticket_priority;

**Support Team Efficiency**:
```sql
-- Agent performance and workload
WITH agent_metrics AS (
  SELECT 
    agent_id,
    agent_name,
    team,
    DATE_TRUNC('month', resolved_date) as month,
    COUNT(*) as tickets_handled,
    AVG(DATEDIFF('hour', assigned_date, resolved_date)) as avg_handle_time,
    AVG(satisfaction_score) as avg_csat,
    COUNT(CASE WHEN satisfaction_score >= 4 THEN 1 END) as satisfied_customers,
    COUNT(CASE WHEN reopened = 1 THEN 1 END) as reopened_tickets
  FROM support_tickets
  WHERE resolved_date >= DATEADD('month', -3, CURRENT_DATE)
  GROUP BY agent_id, agent_name, team, month
)
SELECT 
  team,
  COUNT(DISTINCT agent_id) as agent_count,
  SUM(tickets_handled) as total_tickets,
  ROUND(AVG(tickets_handled), 0) as avg_tickets_per_agent,
  ROUND(AVG(avg_handle_time), 1) as avg_handle_hours,
  ROUND(AVG(avg_csat), 2) as team_avg_csat,
  ROUND(100.0 * SUM(satisfied_customers) / NULLIF(SUM(tickets_handled), 0), 1) as satisfaction_rate,
  ROUND(100.0 * SUM(reopened_tickets) / NULLIF(SUM(tickets_handled), 0), 1) as reopen_rate
FROM agent_metrics
WHERE month = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY team
ORDER BY team_avg_csat DESC;
```
### 2. Infrastructure and Reliability Metrics

**System Uptime and Performance**:
```sql
-- Service availability and performance
WITH uptime_metrics AS (
  SELECT 
    service_name,
    DATE_TRUNC('day', check_timestamp) as day,
    COUNT(*) as total_checks,
    COUNT(CASE WHEN status = 'up' THEN 1 END) as successful_checks,
    AVG(response_time_ms) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
    MAX(response_time_ms) as max_response_time
  FROM infrastructure_monitoring
  WHERE check_timestamp >= DATEADD('day', -30, CURRENT_DATE)
  GROUP BY service_name, day
),
incident_data AS (
  SELECT 
    service_name,
    COUNT(*) as incident_count,
    SUM(duration_minutes) as total_downtime_minutes,
    AVG(duration_minutes) as avg_incident_duration
  FROM incidents
  WHERE incident_date >= DATEADD('day', -30, CURRENT_DATE)
  GROUP BY service_name
)
SELECT 
  u.service_name,
  ROUND(100.0 * SUM(u.successful_checks) / NULLIF(SUM(u.total_checks), 0), 3) as uptime_percentage,
  ROUND(AVG(u.avg_response_time), 0) as avg_response_ms,
  ROUND(AVG(u.p95_response_time), 0) as p95_response_ms,
  COALESCE(i.incident_count, 0) as incidents_30d,
  COALESCE(i.total_downtime_minutes, 0) as total_downtime_minutes,
  ROUND(COALESCE(i.avg_incident_duration, 0), 1) as avg_incident_minutes
FROM uptime_metrics u
LEFT JOIN incident_data i ON u.service_name = i.service_name
GROUP BY u.service_name, i.incident_count, i.total_downtime_minutes, i.avg_incident_duration
ORDER BY uptime_percentage DESC;
```
**Infrastructure Cost Efficiency**:
```sql
-- Cloud infrastructure costs and utilization
WITH resource_metrics AS (
  SELECT 
    resource_type,
    resource_name,
    DATE_TRUNC('week', metric_date) as week,
    AVG(utilization_percent) as avg_utilization,
    AVG(daily_cost) as avg_daily_cost,
    MAX(peak_utilization) as peak_utilization,
    SUM(daily_cost) as total_cost
  FROM cloud_resources
  WHERE metric_date >= DATEADD('month', -3, CURRENT_DATE)
  GROUP BY resource_type, resource_name, week
),
optimization_opportunities AS (
  SELECT 
    resource_type,
    resource_name,
    AVG(avg_utilization) as overall_avg_utilization,
    AVG(avg_daily_cost) as avg_daily_cost,
    CASE 
      WHEN AVG(avg_utilization) < 20 THEN 'Severely Underutilized'
      WHEN AVG(avg_utilization) < 50 THEN 'Underutilized'
      WHEN AVG(avg_utilization) > 90 THEN 'Near Capacity'
      ELSE 'Optimal'
    END as utilization_status,
    AVG(avg_daily_cost) * 30 as monthly_cost
  FROM resource_metrics
  GROUP BY resource_type, resource_name
)
SELECT 
  resource_type,
  utilization_status,
  COUNT(*) as resource_count,
  ROUND(AVG(overall_avg_utilization), 1) as avg_utilization_pct,
  ROUND(SUM(monthly_cost), 0) as total_monthly_cost,
  ROUND(AVG(monthly_cost), 0) as avg_monthly_cost_per_resource,
  ROUND(SUM(CASE WHEN utilization_status IN ('Severely Underutilized', 'Underutilized') 
        THEN monthly_cost * 0.3 ELSE 0 END), 0) as potential_monthly_savings
FROM optimization_opportunities
GROUP BY resource_type, utilization_status
ORDER BY resource_type, utilization_status;
```
### 3. Implementation and Onboarding Metrics

**Customer Onboarding Efficiency**:
```sql
-- Implementation project analytics
WITH implementation_metrics AS (
  SELECT 
    i.project_id,
    i.customer_segment,
    i.implementation_type,
    i.project_value,
    DATEDIFF('day', i.kickoff_date, i.go_live_date) as implementation_days,
    DATEDIFF('day', c.contract_date, i.go_live_date) as total_time_to_value,
    i.implementation_score,
    i.issues_encountered,
    c.first_year_acv
  FROM implementations i
  JOIN customers c ON i.customer_id = c.customer_id
  WHERE i.go_live_date >= DATEADD('month', -6, CURRENT_DATE)
),
segment_benchmarks AS (
  SELECT 
    customer_segment,
    implementation_type,
    COUNT(*) as implementations,
    AVG(implementation_days) as avg_implementation_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY implementation_days) as median_days,
    AVG(total_time_to_value) as avg_time_to_value,
    AVG(implementation_score) as avg_satisfaction,
    AVG(issues_encountered) as avg_issues,
    SUM(CASE WHEN implementation_days <= 30 THEN 1 ELSE 0 END) as on_time_implementations
  FROM implementation_metrics
  GROUP BY customer_segment, implementation_type
)
SELECT 
  customer_segment,
  implementation_type,
  implementations,
  ROUND(avg_implementation_days, 1) as avg_days,
  ROUND(median_days, 1) as median_days,
  ROUND(avg_time_to_value, 1) as avg_ttv_days,
  ROUND(avg_satisfaction, 2) as avg_satisfaction_score,
  ROUND(avg_issues, 1) as avg_issues_per_project,
  ROUND(100.0 * on_time_implementations / implementations, 1) as on_time_pct
FROM segment_benchmarks
ORDER BY customer_segment, implementation_type;
```
### 4. Service Level Agreement (SLA) Metrics

**SLA Performance Tracking**:
```sql
-- SLA compliance across service tiers
WITH sla_performance AS (
  SELECT 
    s.service_tier,
    s.sla_metric,
    s.sla_target,
    DATE_TRUNC('month', m.measurement_date) as month,
    COUNT(*) as measurements,
    COUNT(CASE WHEN m.actual_value <= s.sla_target THEN 1 END) as sla_met,
    AVG(m.actual_value) as avg_actual,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.actual_value) as p95_actual
  FROM sla_definitions s
  JOIN sla_measurements m ON s.sla_id = m.sla_id
  WHERE m.measurement_date >= DATEADD('month', -3, CURRENT_DATE)
  GROUP BY s.service_tier, s.sla_metric, s.sla_target, month
)
SELECT 
  service_tier,
  sla_metric,
  sla_target,
  month,
  measurements,
  ROUND(100.0 * sla_met / measurements, 2) as sla_compliance_pct,
  ROUND(avg_actual, 2) as avg_performance,
  ROUND(p95_actual, 2) as p95_performance,
  CASE 
    WHEN 100.0 * sla_met / measurements >= 99.9 THEN 'Exceeding'
    WHEN 100.0 * sla_met / measurements >= 95 THEN 'Meeting'
    ELSE 'Missing'
  END as sla_status
FROM sla_performance
ORDER BY month DESC, service_tier, sla_metric;
```
### 5. Process Efficiency Metrics

**Automation Impact Analysis**:
```sql
-- Measure automation effectiveness
WITH process_metrics AS (
  SELECT 
    process_name,
    process_category,
    automation_status,
    DATE_TRUNC('month', execution_date) as month,
    COUNT(*) as executions,
    AVG(execution_time_minutes) as avg_execution_time,
    AVG(error_count) as avg_errors,
    AVG(manual_interventions) as avg_interventions,
    SUM(cost_per_execution) as total_cost
  FROM business_processes
  WHERE execution_date >= DATEADD('month', -6, CURRENT_DATE)
  GROUP BY process_name, process_category, automation_status, month
),
automation_comparison AS (
  SELECT 
    process_category,
    month,
    SUM(CASE WHEN automation_status = 'automated' THEN executions ELSE 0 END) as automated_executions,
    SUM(CASE WHEN automation_status = 'manual' THEN executions ELSE 0 END) as manual_executions,
    AVG(CASE WHEN automation_status = 'automated' THEN avg_execution_time END) as automated_avg_time,
    AVG(CASE WHEN automation_status = 'manual' THEN avg_execution_time END) as manual_avg_time,
    SUM(CASE WHEN automation_status = 'automated' THEN total_cost END) as automated_cost,
    SUM(CASE WHEN automation_status = 'manual' THEN total_cost END) as manual_cost
  FROM process_metrics
  GROUP BY process_category, month
)
SELECT 
  process_category,
  month,
  automated_executions + manual_executions as total_executions,
  ROUND(100.0 * automated_executions / NULLIF(automated_executions + manual_executions, 0), 1) as automation_rate,
  ROUND(manual_avg_time - automated_avg_time, 1) as time_saved_per_execution,
  ROUND((manual_avg_time - automated_avg_time) * automated_executions, 0) as total_time_saved,
  ROUND(manual_cost - automated_cost, 0) as cost_savings,
  ROUND((manual_avg_time / NULLIF(automated_avg_time, 0) - 1) * 100, 0) as efficiency_improvement_pct
FROM automation_comparison
WHERE automated_executions > 0 AND manual_executions > 0
ORDER BY month DESC, cost_savings DESC;
```
## Common Stakeholder Questions

### From Operations Leadership
1. "What's our current operational efficiency ratio?"

| Audience View | Analyst Hint |
|---------------|-------------|
| How efficiently are we running our operations? | Calculate output/input ratios from `operational_efficiency_metrics`: revenue per operational dollar spent |

2. "Where are our biggest cost optimization opportunities?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What operational areas are costing us the most unnecessarily? | Analyze cost trends and benchmarks by process from `cost_optimization_analysis` |

3. "How are we performing against SLAs?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are we meeting our service level commitments to customers? | Compare actual vs target performance from `sla_compliance_metrics` |

4. "What's the ROI on our automation investments?"

| Audience View | Analyst Hint |
|---------------|-------------|
| Are our automation projects paying off financially? | Calculate time and cost savings from `automation_impact_analysis` vs investment costs |

5. "Which processes need immediate attention?"

| Audience View | Analyst Hint |
|---------------|-------------|
| What operational workflows are broken or inefficient? | Identify bottlenecks and failure rates from `process_performance_monitoring` |

### From Customer Success
1. "How quickly are we onboarding new customers?"
2. "What's driving support ticket volume?"
3. "Are we meeting customer expectations?"
4. "Which issues cause the most escalations?"
5. "How can we improve time to value?"

### From Engineering/IT
1. "What's our system reliability trending?"
2. "Where should we invest in infrastructure?"
3. "Which services need performance optimization?"
4. "What's our technical debt impact?"
5. "How effective is our monitoring?"

### From Finance
1. "What's our gross margin trajectory?"
2. "How do operational costs scale with growth?"
3. "Where can we reduce operational expenses?"
4. "What's the cost per customer served?"
5. "Are we achieving economies of scale?"

## Standard Operations Reports

### 1. Operations Dashboard
```sql
-- Executive operations summary
WITH ops_summary AS (
  SELECT 
    -- Support metrics
    COUNT(DISTINCT st.ticket_id) as support_tickets,
    AVG(st.resolution_hours) as avg_resolution_time,
    AVG(st.satisfaction_score) as avg_csat,
    -- Infrastructure metrics
    AVG(i.uptime_percentage) as avg_uptime,
    SUM(i.incident_count) as total_incidents,
    -- Implementation metrics
    COUNT(DISTINCT impl.project_id) as active_implementations,
    AVG(impl.days_to_complete) as avg_implementation_days,
    -- Cost metrics
    SUM(c.operational_cost) as total_ops_cost,
    SUM(c.operational_cost) / COUNT(DISTINCT cust.customer_id) as cost_per_customer
  FROM support_tickets st
  CROSS JOIN infrastructure_metrics i
  CROSS JOIN implementations impl
  CROSS JOIN costs c
  CROSS JOIN customers cust
  WHERE st.created_date >= DATEADD('month', -1, CURRENT_DATE)
    AND i.metric_date >= DATEADD('month', -1, CURRENT_DATE)
    AND impl.status = 'active'
    AND c.cost_date >= DATEADD('month', -1, CURRENT_DATE)
    AND cust.status = 'active'
)SELECT 
  support_tickets as monthly_tickets,
  ROUND(avg_resolution_time, 1) as avg_resolution_hours,
  ROUND(avg_csat, 2) as customer_satisfaction,
  ROUND(avg_uptime, 2) as infrastructure_uptime_pct,
  total_incidents as infrastructure_incidents,
  active_implementations,
  ROUND(avg_implementation_days, 1) as avg_implementation_days,
  ROUND(total_ops_cost / 1000000, 1) as ops_cost_millions,
  ROUND(cost_per_customer, 0) as cost_per_customer
FROM ops_summary;

### 2. Support Efficiency Report
```sql
-- Detailed support operations analysis
WITH ticket_categories AS (
  SELECT 
    DATE_TRUNC('week', created_date) as week,
    ticket_category,
    ticket_subcategory,
    COUNT(*) as ticket_count,
    AVG(resolution_hours) as avg_resolution,
    COUNT(CASE WHEN escalated = 1 THEN 1 END) as escalations,
    AVG(agent_touches) as avg_touches,
    COUNT(CASE WHEN self_service_deflected = 1 THEN 1 END) as self_service_resolved
  FROM support_tickets
  WHERE created_date >= DATEADD('month', -3, CURRENT_DATE)
  GROUP BY week, ticket_category, ticket_subcategory
),
deflection_analysis AS (
  SELECT 
    ticket_category,
    SUM(ticket_count) as total_tickets,
    SUM(self_service_resolved) as deflected_tickets,
    AVG(avg_resolution) as category_avg_resolution,
    SUM(escalations) as total_escalations
  FROM ticket_categories
  GROUP BY ticket_category
)SELECT 
  ticket_category,
  total_tickets,
  ROUND(100.0 * deflected_tickets / total_tickets, 1) as self_service_rate,
  ROUND(category_avg_resolution, 1) as avg_resolution_hours,
  total_escalations,
  ROUND(100.0 * total_escalations / total_tickets, 1) as escalation_rate,
  ROUND(total_tickets * category_avg_resolution * 50, 0) as estimated_cost -- $50/hour support cost
FROM deflection_analysis
ORDER BY total_tickets DESC;

### 3. Infrastructure Capacity Planning
```sql
-- Resource utilization and growth projections
WITH utilization_trends AS (
  SELECT 
    resource_type,
    DATE_TRUNC('week', metric_date) as week,
    AVG(utilization_percent) as avg_utilization,
    MAX(utilization_percent) as peak_utilization,
    COUNT(DISTINCT resource_id) as resource_count
  FROM infrastructure_metrics
  WHERE metric_date >= DATEADD('month', -6, CURRENT_DATE)
  GROUP BY resource_type, week
),
growth_projection AS (
  SELECT 
    resource_type,
    -- Calculate linear growth rate
    REGR_SLOPE(avg_utilization, EXTRACT(EPOCH FROM week)) as utilization_growth_rate,
    AVG(avg_utilization) as current_avg_utilization,
    MAX(peak_utilization) as max_peak_utilization
  FROM utilization_trends
  GROUP BY resource_type
) recommended_maintenance_interval * 1.5 THEN 20
      WHEN last_maintenance_days_ago > recommended_maintenance_interval THEN 10
      ELSE 0
    END as maintenance_risk_score
  FROM infrastructure_components
  WHERE status = 'active'
)
SELECT 
  component_type,
  COUNT(*) as total_components,
  COUNT(CASE WHEN error_risk_score + performance_risk_score + maintenance_risk_score >= 40 THEN 1 END) as high_risk,
  COUNT(CASE WHEN error_risk_score + performance_risk_score + maintenance_risk_score >= 20 THEN 1 END) as medium_risk,
  AVG(error_rate_7d) as avg_error_rate,
  AVG(performance_degradation_30d) as avg_performance_degradation,
  AVG(last_maintenance_days_ago) as avg_days_since_maintenance
FROM component_health
GROUP BY component_type
ORDER BY high_risk DESC;

### 2. Customer Impact Analysis
```sql
-- Correlate operational issues with customer experience
WITH operational_events AS (
  SELECT 
    DATE_TRUNC('day', event_timestamp) as event_day,
    affected_service,
    severity,
    duration_minutes,
    customers_impacted
  FROM incidents
  WHERE event_timestamp >= DATEADD('month', -3, CURRENT_DATE)
),
customer_metrics AS (
  SELECT 
    DATE_TRUNC('day', metric_date) as metric_day,
    AVG(nps_score) as daily_nps,
    AVG(usage_minutes) as daily_usage,
    COUNT(DISTINCT CASE WHEN churned = 1 THEN customer_id END) as churned_customers,
    COUNT(DISTINCT customer_id) as active_customers
  FROM customer_daily_metrics
  WHERE metric_date >= DATEADD('month', -3, CURRENT_DATE)
  GROUP BY metric_day
)SELECT 
  cm.metric_day,
  COALESCE(SUM(oe.duration_minutes), 0) as total_incident_minutes,
  COALESCE(SUM(oe.customers_impacted), 0) as customers_affected,
  cm.daily_nps,
  cm.daily_usage,
  cm.churned_customers,
  CASE 
    WHEN SUM(oe.duration_minutes) > 60 THEN 'Major Incident'
    WHEN SUM(oe.duration_minutes) > 0 THEN 'Minor Incident'
    ELSE 'No Incidents'
  END as incident_severity
FROM customer_metrics cm
LEFT JOIN operational_events oe ON cm.metric_day = oe.event_day
GROUP BY cm.metric_day, cm.daily_nps, cm.daily_usage, cm.churned_customers
ORDER BY cm.metric_day DESC;

### 3. Process Optimization Analysis
```sql
-- Identify bottlenecks and optimization opportunities
WITH process_flow AS (
  SELECT 
    process_name,
    step_name,
    step_sequence,
    AVG(step_duration_minutes) as avg_duration,
    AVG(wait_time_minutes) as avg_wait_time,
    COUNT(*) as executions,
    COUNT(CASE WHEN error_occurred = 1 THEN 1 END) as errors,
    AVG(rework_required) as rework_rate
  FROM process_executions
  WHERE execution_date >= DATEADD('month', -1, CURRENT_DATE)
  GROUP BY process_name, step_name, step_sequence
),
bottleneck_analysis AS (
  SELECT 
    process_name,
    SUM(avg_duration + avg_wait_time) as total_process_time,
    MAX(avg_duration + avg_wait_time) as bottleneck_time,
    SUM(errors) as total_errors,
    AVG(rework_rate) as avg_rework_rate,
    STRING_AGG(
      CASE 
        WHEN (avg_duration + avg_wait_time) = MAX(avg_duration + avg_wait_time) OVER (PARTITION BY process_name)
        THEN step_name 
      END, ', '
    ) as bottleneck_steps
  FROM process_flow
  GROUP BY process_name
)SELECT 
  process_name,
  ROUND(total_process_time, 1) as total_time_minutes,
  ROUND(bottleneck_time, 1) as bottleneck_minutes,
  ROUND(100.0 * bottleneck_time / total_process_time, 1) as bottleneck_pct_of_total,
  bottleneck_steps,
  total_errors,
  ROUND(avg_rework_rate * 100, 1) as rework_rate_pct,
  ROUND(total_process_time * 0.3, 1) as potential_time_savings -- Assume 30% improvement possible
FROM bottleneck_analysis
WHERE total_process_time > 30 -- Focus on longer processes
ORDER BY total_process_time DESC;

## Operations Analytics Best Practices

### 1. Measurement Excellence
- **Real-Time Monitoring**: Catch issues before customers notice
- **Leading Indicators**: Track predictive metrics
- **Root Cause Analysis**: Don't just fix symptoms
- **Continuous Improvement**: Regular process reviews

### 2. Cost Management
- **Unit Economics**: Understand cost per transaction
- **Capacity Planning**: Stay ahead of growth
- **Vendor Management**: Regular contract reviews
- **Automation ROI**: Measure actual savings

### 3. Quality Assurance
- **SLA Adherence**: Never compromise service levels
- **Error Prevention**: Proactive vs reactive
- **Documentation**: Maintain runbooks
- **Training Programs**: Continuous skill development

### 4. Cross-Functional Collaboration
- **Customer Success Alignment**: Operational metrics affect retention
- **Engineering Partnership**: DevOps practices
- **Finance Integration**: Cost allocation accuracy
- **Sales Coordination**: Capacity for growth
## Common Pitfalls to Avoid

1. **Reactive Mode**: Only measuring after problems occur
2. **Vanity Metrics**: Tracking metrics that don't drive action
3. **Siloed Operations**: Not considering end-to-end impact
4. **Over-Optimization**: Efficiency at the expense of quality
5. **Manual Processes**: Not investing in automation

## Key Takeaways

1. **Efficiency Drives Margins**: Operational excellence = profitability
2. **Reliability Builds Trust**: Uptime and SLAs matter
3. **Automation Scales**: Manual processes limit growth
4. **Data Enables Decisions**: Measure everything important
5. **Continuous Improvement**: Small gains compound

---

*Next: [Module 8 - Executive Reporting and Strategic Analytics](08-executive-reporting.md)*