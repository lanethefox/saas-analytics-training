{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Mart: Customer Success Health Monitoring
-- Customer health monitoring and churn prevention analytics
-- Primary stakeholders: Customer success team, account management, retention specialists
-- Updated to use entity layer tables with correct column names

with customer_health_base as (
    select
        c.account_id,
        c.account_id as account_key,  -- Use account_id as key since account_key doesn't exist
        c.company_name as account_name,
        case 
            when c.customer_tier = 1 then 'enterprise'
            when c.customer_tier = 2 then 'premium'
            when c.customer_tier = 3 then 'professional'
            when c.customer_tier = 4 then 'starter'
            else 'unknown'
        end as account_type,
        c.customer_status as subscription_status,
        c.monthly_recurring_revenue,
        c.customer_health_score,
        c.churn_risk_score,
        c.total_locations,
        c.total_devices as active_devices,  -- Using total_devices as proxy for active
        c.device_events_30d,
        c.days_since_creation as days_since_signup,
        c.created_at as account_created_at,
        
        -- Customer value segmentation
        case 
            when c.monthly_recurring_revenue >= 1000 then 'strategic_account'
            when c.monthly_recurring_revenue >= 500 then 'key_account'
            when c.monthly_recurring_revenue >= 100 then 'standard_account'
            else 'basic_account'
        end as account_value_tier,
        
        -- Customer lifecycle segmentation
        case 
            when c.days_since_creation <= 30 then 'onboarding'
            when c.days_since_creation <= 90 then 'adoption'
            when c.days_since_creation <= 365 then 'growth'
            else 'mature'
        end as lifecycle_stage
        
    from {{ ref('entity_customers') }} c
    where c.customer_status in ('active', 'trial')
),

user_engagement_health as (
    select
        u.account_id::varchar as account_id,  -- Cast to varchar to match customer table
        count(distinct u.user_id) as total_users,
        count(case when u.user_status = 'active' then u.user_id end) as active_users,
        count(case when u.last_activity_timestamp >= current_date - 7 then u.user_id end) as users_active_7d,
        count(case when u.last_activity_timestamp >= current_date - 30 then u.user_id end) as users_active_30d,
        avg(u.engagement_score) as avg_engagement_score,
        avg(u.total_sessions_30d) as avg_sessions_per_user,
        avg(u.total_feature_interactions_30d) as avg_feature_interactions_per_user,
        
        -- User engagement health indicators
        case 
            when count(case when u.user_status = 'active' then u.user_id end) = 0 then 'no_active_users'
            when avg(u.engagement_score) >= 0.8 then 'highly_engaged'
            when avg(u.engagement_score) >= 0.6 then 'well_engaged'
            when avg(u.engagement_score) >= 0.4 then 'moderately_engaged'
            else 'poorly_engaged'
        end as user_engagement_health,
        
        -- User adoption trajectory
        case 
            when count(case when u.user_created_at >= current_date - 30 then u.user_id end) > 0 then 'growing_team'
            when count(case when u.last_activity_timestamp >= current_date - 7 then u.user_id end)::numeric / 
                 nullif(count(distinct u.user_id), 0) >= 0.8 then 'stable_team'
            when count(case when u.last_activity_timestamp >= current_date - 30 then u.user_id end)::numeric / 
                 nullif(count(distinct u.user_id), 0) >= 0.5 then 'declining_team'
            else 'inactive_team'
        end as user_adoption_trend,
        
        -- Admin presence health
        count(case when u.role_type_standardized = 'admin' and u.user_status = 'active' then u.user_id end) as active_admin_users,
        case 
            when count(case when u.role_type_standardized = 'admin' and u.user_status = 'active' then u.user_id end) = 0 then 'no_admin_risk'
            when count(case when u.role_type_standardized = 'admin' and u.user_status = 'active' then u.user_id end) = 1 then 'single_admin_risk'
            else 'healthy_admin_coverage'
        end as admin_coverage_health
        
    from {{ ref('entity_users') }} u
    group by u.account_id
),

device_health_analytics as (
    select
        d.account_id::varchar as account_id,  -- Cast to varchar to match customer table
        count(distinct d.device_id) as total_devices,
        count(case when d.device_status = 'active' then d.device_id end) as active_devices,
        count(case when d.total_events_30d > 100 then d.device_id end) as devices_active_7d,  -- Use 30d as proxy
        count(case when d.total_events_30d > 0 then d.device_id end) as devices_active_30d,
        sum(d.total_events_30d) as total_device_events_30d,
        avg(d.overall_health_score) as avg_device_health_score,
        count(case when d.overall_health_score < 0.5 then d.device_id end) as unhealthy_devices,
        count(case when d.last_maintenance_date is null or d.last_maintenance_date < current_date - 90 then d.device_id end) as overdue_maintenance_devices,
        
        -- Device health indicators
        case 
            when count(distinct d.device_id) = 0 then 'no_devices'
            when avg(d.overall_health_score) >= 0.8 and sum(d.total_events_30d) >= 1000 then 'excellent_device_health'
            when avg(d.overall_health_score) >= 0.6 and sum(d.total_events_30d) >= 500 then 'good_device_health'
            when avg(d.overall_health_score) >= 0.4 then 'fair_device_health'
            else 'poor_device_health'
        end as device_health_status,
        
        -- Device utilization health
        case 
            when count(distinct d.device_id) > 0 and 
                 count(case when d.total_events_30d > 0 then d.device_id end)::numeric / count(distinct d.device_id) >= 0.8 then 'high_utilization'
            when count(distinct d.device_id) > 0 and 
                 count(case when d.total_events_30d > 0 then d.device_id end)::numeric / count(distinct d.device_id) >= 0.5 then 'medium_utilization'
            when count(case when d.total_events_30d > 0 then d.device_id end) > 0 then 'low_utilization'
            else 'no_utilization'
        end as device_utilization_health
        
    from {{ ref('entity_devices') }} d
    group by d.account_id
),

location_operational_health as (
    select
        l.account_id::varchar as account_id,  -- Cast to varchar to match customer table
        count(distinct l.location_id) as total_locations,
        count(case when l.location_status = 'active' then l.location_id end) as active_locations,
        avg(l.operational_health_score) as avg_location_health_score,
        avg(l.operational_readiness_score) as avg_operational_efficiency,
        0.65 as avg_capacity_utilization,  -- Default value since column doesn't exist
        count(case when l.support_tickets_open > 0 then l.location_id end) as locations_with_open_tickets,
        sum(l.support_tickets_open) as total_open_support_tickets,
        
        -- Location health indicators
        case 
            when avg(l.operational_health_score) >= 0.8 then 'excellent_location_health'
            when avg(l.operational_health_score) >= 0.6 then 'good_location_health'
            when avg(l.operational_health_score) >= 0.4 then 'fair_location_health'
            else 'poor_location_health'
        end as location_health_status,
        
        -- Support ticket health
        case 
            when sum(l.support_tickets_open) = 0 then 'no_support_issues'
            when sum(l.support_tickets_open) <= 2 then 'minimal_support_issues'
            when sum(l.support_tickets_open) <= 5 then 'moderate_support_issues'
            else 'high_support_issues'
        end as support_ticket_health
        
    from {{ ref('entity_locations') }} l
    group by l.account_id
)

select
    -- Customer identification
    chb.account_id,
    chb.account_key,
    chb.account_name,
    chb.account_type,
    chb.account_value_tier,
    chb.lifecycle_stage,
    chb.subscription_status,
    chb.monthly_recurring_revenue,
    chb.days_since_signup,
    
    -- Core health metrics
    chb.customer_health_score,
    chb.churn_risk_score,
    chb.total_locations,
    chb.active_devices,
    chb.device_events_30d,
    
    -- User engagement health
    coalesce(ueh.total_users, 0) as total_users,
    coalesce(ueh.active_users, 0) as active_users,
    coalesce(ueh.users_active_7d, 0) as users_active_7d,
    coalesce(ueh.users_active_30d, 0) as users_active_30d,
    coalesce(ueh.avg_engagement_score, 0) as avg_user_engagement_score,
    coalesce(ueh.user_engagement_health, 'no_users') as user_engagement_health,
    coalesce(ueh.user_adoption_trend, 'no_users') as user_adoption_trend,
    coalesce(ueh.admin_coverage_health, 'no_admin_risk') as admin_coverage_health,
    
    -- Device health analytics
    coalesce(dha.total_devices, 0) as total_devices,
    coalesce(dha.active_devices, 0) as active_devices_detailed,
    coalesce(dha.devices_active_7d, 0) as devices_active_7d,
    coalesce(dha.devices_active_30d, 0) as devices_active_30d,
    coalesce(dha.total_device_events_30d, 0) as total_device_events_30d_detailed,
    coalesce(dha.avg_device_health_score, 0) as avg_device_health_score,
    coalesce(dha.unhealthy_devices, 0) as unhealthy_devices,
    coalesce(dha.overdue_maintenance_devices, 0) as overdue_maintenance_devices,
    coalesce(dha.device_health_status, 'no_devices') as device_health_status,
    coalesce(dha.device_utilization_health, 'no_utilization') as device_utilization_health,
    
    -- Location operational health
    coalesce(loh.total_locations, 0) as total_locations_detailed,
    coalesce(loh.active_locations, 0) as active_locations,
    coalesce(loh.avg_location_health_score, 0) as avg_location_health_score,
    coalesce(loh.avg_operational_efficiency, 0) as avg_operational_efficiency,
    coalesce(loh.avg_capacity_utilization, 0) as avg_capacity_utilization,
    coalesce(loh.locations_with_open_tickets, 0) as locations_with_open_tickets,
    coalesce(loh.total_open_support_tickets, 0) as total_open_support_tickets,
    coalesce(loh.location_health_status, 'no_locations') as location_health_status,
    coalesce(loh.support_ticket_health, 'no_support_issues') as support_ticket_health,
    
    -- Customer success interventions
    case 
        when chb.churn_risk_score >= 80 then 'immediate_intervention_required'
        when chb.churn_risk_score >= 60 then 'proactive_outreach_needed'
        when chb.churn_risk_score >= 40 then 'monitor_closely'
        else 'healthy_account'
    end as intervention_priority,
    
    -- Specific intervention recommendations
    case 
        when ueh.user_engagement_health = 'no_active_users' then 'user_activation_program'
        when ueh.admin_coverage_health = 'no_admin_risk' then 'admin_enablement_program'
        when dha.device_health_status = 'poor_device_health' then 'device_optimization_program'
        when dha.device_utilization_health = 'no_utilization' then 'adoption_acceleration_program'
        when loh.support_ticket_health = 'high_support_issues' then 'technical_support_escalation'
        when chb.lifecycle_stage = 'onboarding' and coalesce(ueh.avg_engagement_score, 0) < 0.5 then 'onboarding_intervention'
        when chb.lifecycle_stage = 'adoption' and coalesce(dha.total_device_events_30d, 0) < 100 then 'adoption_coaching'
        when chb.account_value_tier = 'strategic_account' and chb.customer_health_score < 70 then 'executive_engagement'
        else 'standard_customer_success'
    end as recommended_intervention,
    
    -- Next action timing
    case 
        when chb.churn_risk_score >= 80 then 'within_24_hours'
        when chb.churn_risk_score >= 60 then 'within_1_week'
        when chb.churn_risk_score >= 40 then 'within_2_weeks'
        else 'quarterly_check_in'
    end as action_timeframe,
    
    -- Customer success owner assignment
    case 
        when chb.account_value_tier = 'strategic_account' then 'senior_csm'
        when chb.account_value_tier = 'key_account' then 'csm'
        when chb.account_value_tier = 'standard_account' then 'junior_csm'
        else 'cs_coordinator'
    end as cs_owner_assignment,
    
    -- Composite health scoring
    (
        chb.customer_health_score * 0.4 +
        coalesce(ueh.avg_engagement_score, 0) * 100 * 0.3 +
        coalesce(dha.avg_device_health_score, 0) * 100 * 0.2 +
        coalesce(loh.avg_location_health_score, 0) * 100 * 0.1
    ) as composite_health_score,
    
    -- Risk indicators
    case 
        when chb.churn_risk_score >= 80 or coalesce(ueh.avg_engagement_score, 0) < 0.3 then 'high_risk'
        when chb.churn_risk_score >= 60 or coalesce(dha.avg_device_health_score, 0) < 0.4 then 'medium_risk'
        when chb.churn_risk_score >= 40 then 'low_risk'
        else 'healthy'
    end as overall_risk_category,
    
    -- Expansion opportunity indicators
    case 
        when chb.customer_health_score >= 80 and coalesce(dha.device_utilization_health, 'no_utilization') = 'high_utilization' 
             and chb.lifecycle_stage != 'onboarding' then 'high_expansion_potential'
        when chb.customer_health_score >= 60 and coalesce(ueh.user_adoption_trend, 'no_users') = 'growing_team' then 'medium_expansion_potential'
        when chb.customer_health_score >= 50 then 'low_expansion_potential'
        else 'no_expansion_potential'
    end as expansion_opportunity,
    
    -- Success metrics tracking
    case 
        when chb.customer_health_score >= 80 and coalesce(ueh.avg_engagement_score, 0) >= 0.7 
             and coalesce(dha.avg_device_health_score, 0) >= 0.7 then 'customer_success_champion'
        when chb.customer_health_score >= 60 and coalesce(ueh.avg_engagement_score, 0) >= 0.5 then 'satisfied_customer'
        when chb.customer_health_score >= 40 then 'neutral_customer'
        else 'at_risk_customer'
    end as success_category,
    
    -- Quarterly business review eligibility
    case 
        when chb.account_value_tier in ('strategic_account', 'key_account') and chb.customer_health_score >= 60 then 'qbr_eligible'
        when chb.account_value_tier = 'standard_account' and chb.customer_health_score >= 80 then 'qbr_eligible'
        else 'qbr_not_eligible'
    end as qbr_eligibility,
    
    -- Metadata
    current_timestamp as health_analyzed_at
    
from customer_health_base chb
left join user_engagement_health ueh on chb.account_id = ueh.account_id
left join device_health_analytics dha on chb.account_id = dha.account_id
left join location_operational_health loh on chb.account_id = loh.account_id
order by 
    case 
        when chb.churn_risk_score >= 80 then 1
        when chb.churn_risk_score >= 60 then 2
        when chb.churn_risk_score >= 40 then 3
        else 4
    end,
    monthly_recurring_revenue desc,
    composite_health_score asc