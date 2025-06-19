{{ config(materialized='table') }}

-- Customer Success Account Health Dashboard
-- Comprehensive customer health monitoring for proactive success management

with customer_health_base as (
    select * from {{ ref('entity_customers') }}
),

subscription_health as (
    select * from {{ ref('entity_subscriptions') }}
),

location_performance as (
    select
        account_id,
        count(*) as total_locations,
        count(case when location_health_score >= 0.8 then 1 end) as healthy_locations,
        count(case when primary_operational_status != 'operational' then 1 end) as problematic_locations,
        avg(location_health_score) as avg_location_health,
        sum(total_devices) as total_devices_across_locations,
        sum(online_devices) as online_devices_across_locations,
        sum(usage_events_30d) as total_usage_events_30d
    from {{ ref('entity_locations') }}
    group by account_id
),

user_engagement_summary as (
    select
        account_id,
        count(*) as total_users,
        count(case when user_engagement_tier in ('power_user', 'engaged_user') then 1 end) as engaged_users,
        count(case when activity_recency in ('active_today', 'active_this_week') then 1 end) as recently_active_users,
        avg(overall_engagement_score) as avg_user_engagement,
        max(last_login_at) as latest_user_login,
        count(case when role_hierarchy_level >= 4 then 1 end) as decision_makers,
        count(case when user_tenure_category = 'new_user' then 1 end) as new_users
    from {{ ref('entity_users') }}
    group by account_id
),

support_indicators as (
    -- This would typically come from a support system integration
    -- For now, using proxy metrics from device alerts and user activity
    select
        chb.account_id,
        lp.problematic_locations as support_risk_locations,
        case 
            when lp.problematic_locations > lp.total_locations * 0.3 then 'high_support_risk'
            when lp.problematic_locations > 0 then 'medium_support_risk'
            else 'low_support_risk'
        end as support_risk_level,
        
        -- Estimate support load based on operational issues
        lp.problematic_locations * 2 + 
        greatest(0, 30 - ues.recently_active_users) as estimated_support_score
        
    from customer_health_base chb
    left join location_performance lp on chb.account_id = lp.account_id
    left join user_engagement_summary ues on chb.account_id = ues.account_id
),

customer_success_scoring as (
    select
        chb.account_id,
        
        -- Multi-dimensional health assessment
        chb.customer_health_score as platform_health,
        coalesce(lp.avg_location_health, 0) as operational_health,
        coalesce(ues.avg_user_engagement, 0) as engagement_health,
        coalesce(sh.subscription_health_score, 0) as financial_health,
        
        -- Overall customer success score (weighted)
        round(
            (chb.customer_health_score * 0.3 +
             coalesce(lp.avg_location_health, 0) * 0.25 +
             coalesce(ues.avg_user_engagement, 0) * 0.25 +
             coalesce(sh.subscription_health_score, 0) * 0.2), 3
        ) as overall_success_score,
        
        -- Risk indicators
        case 
            when chb.churn_risk_score >= 0.8 then 'critical_risk'
            when chb.churn_risk_score >= 0.6 then 'high_risk'
            when chb.churn_risk_score >= 0.4 then 'medium_risk'
            when chb.churn_risk_score >= 0.2 then 'low_risk'
            else 'minimal_risk'
        end as churn_risk_category,
        
        -- Success stage classification
        case 
            when chb.overall_success_score >= 0.9 then 'thriving'
            when chb.overall_success_score >= 0.8 then 'succeeding'
            when chb.overall_success_score >= 0.6 then 'progressing'
            when chb.overall_success_score >= 0.4 then 'struggling'
            else 'at_risk'
        end as success_stage
        
    from customer_health_base chb
    left join location_performance lp on chb.account_id = lp.account_id
    left join user_engagement_summary ues on chb.account_id = ues.account_id
    left join subscription_health sh on chb.account_id = sh.account_id
),

expansion_opportunities as (
    select
        chb.account_id,
        
        -- Location expansion potential
        case 
            when lp.avg_location_health > 0.8 and chb.monthly_recurring_revenue / lp.total_locations < 100 
            then 'location_expansion'
            else null
        end as location_expansion_opportunity,
        
        -- User adoption expansion
        case 
            when ues.engaged_users / nullif(ues.total_users, 0) > 0.7 
                and ues.total_users < lp.total_locations * 3
            then 'user_expansion'
            else null
        end as user_expansion_opportunity,
        
        -- Feature adoption expansion
        case 
            when chb.customer_health_score > 0.8 and sh.plan_type = 'basic'
            then 'plan_upgrade'
            else null
        end as plan_upgrade_opportunity,
        
        -- Calculate expansion score
        case 
            when chb.customer_health_score > 0.8 
                and sh.subscription_health_score > 0.8
                and lp.avg_location_health > 0.7
            then 0.9
            when chb.customer_health_score > 0.6 
                and sh.payment_success_rate_90d > 0.9
            then 0.7
            when chb.customer_health_score > 0.5 
            then 0.4
            else 0.2
        end as expansion_readiness_score
        
    from customer_health_base chb
    left join location_performance lp on chb.account_id = lp.account_id
    left join user_engagement_summary ues on chb.account_id = ues.account_id
    left join subscription_health sh on chb.account_id = sh.account_id
),

final as (
    select
        -- Customer identification
        chb.account_id,
        chb.account_name,
        chb.account_type,
        chb.industry_vertical,
        chb.headquarters_city,
        chb.headquarters_state,
        chb.headquarters_country,
        
        -- Financial context
        chb.monthly_recurring_revenue,
        chb.annual_recurring_revenue,
        sh.contract_value_tier,
        sh.primary_subscription_status,
        
        -- Health scoring
        css.platform_health,
        css.operational_health,
        css.engagement_health,
        css.financial_health,
        css.overall_success_score,
        
        -- Success classification
        css.success_stage,
        css.churn_risk_category,
        chb.churn_risk_score,
        
        -- Operational metrics
        lp.total_locations,
        lp.healthy_locations,
        lp.problematic_locations,
        lp.total_devices_across_locations,
        lp.online_devices_across_locations,
        
        -- User engagement
        ues.total_users,
        ues.engaged_users,
        ues.recently_active_users,
        ues.decision_makers,
        ues.new_users,
        ues.latest_user_login,
        
        -- Engagement rates
        case 
            when ues.total_users > 0 
            then ues.engaged_users / ues.total_users::decimal
            else 0
        end as user_engagement_rate,
        
        case 
            when lp.total_devices_across_locations > 0 
            then lp.online_devices_across_locations / lp.total_devices_across_locations::decimal
            else 0
        end as device_uptime_rate,
        
        -- Activity indicators
        lp.total_usage_events_30d,
        case 
            when lp.total_locations > 0 
            then lp.total_usage_events_30d / lp.total_locations::decimal
            else 0
        end as avg_usage_per_location,
        
        -- Support risk assessment
        si.support_risk_level,
        si.estimated_support_score,
        
        -- Expansion opportunities
        eo.location_expansion_opportunity,
        eo.user_expansion_opportunity,
        eo.plan_upgrade_opportunity,
        eo.expansion_readiness_score,
        
        -- Customer success recommendations
        case 
            when css.churn_risk_category = 'critical_risk' then 'immediate_intervention'
            when css.churn_risk_category = 'high_risk' then 'proactive_outreach'
            when css.success_stage = 'thriving' and eo.expansion_readiness_score > 0.7 then 'expansion_conversation'
            when ues.user_engagement_rate < 0.5 then 'adoption_coaching'
            when lp.problematic_locations > 0 then 'operational_support'
            when ues.new_users > 0 then 'onboarding_focus'
            else 'regular_check_in'
        end as primary_cs_action,
        
        -- Priority scoring for customer success team
        case 
            when css.churn_risk_category in ('critical_risk', 'high_risk') 
                and chb.monthly_recurring_revenue >= 1000 then 'p0_critical'
            when css.churn_risk_category = 'high_risk' 
                or (chb.monthly_recurring_revenue >= 2000 and css.success_stage = 'struggling') then 'p1_high'
            when eo.expansion_readiness_score > 0.8 
                and chb.monthly_recurring_revenue >= 500 then 'p1_expansion'
            when css.success_stage in ('struggling', 'progressing') then 'p2_medium'
            else 'p3_low'
        end as cs_priority_level,
        
        -- Account segmentation for CS workflow
        case 
            when chb.monthly_recurring_revenue >= 5000 then 'enterprise'
            when chb.monthly_recurring_revenue >= 1000 then 'mid_market'
            when chb.monthly_recurring_revenue >= 300 then 'growth'
            else 'standard'
        end as cs_segment,
        
        -- Health trend indicators
        case 
            when ues.latest_user_login >= current_date - 7 then 'recently_engaged'
            when ues.latest_user_login >= current_date - 30 then 'moderately_engaged'
            when ues.latest_user_login >= current_date - 90 then 'declining_engagement'
            else 'dormant'
        end as engagement_recency,
        
        -- Time-based metrics
        chb.days_since_signup,
        case 
            when ues.latest_user_login is not null 
            then extract(days from (current_date - ues.latest_user_login::date))
            else null
        end as days_since_last_user_activity,
        
        -- Billing health indicators
        sh.billing_health_status,
        sh.payment_success_rate_90d,
        sh.outstanding_amount,
        
        -- Contract and renewal information
        sh.renewal_timeline,
        sh.days_to_renewal,
        
        -- Metadata
        current_timestamp as mart_updated_at
        
    from customer_health_base chb
    left join subscription_health sh on chb.account_id = sh.account_id
    left join location_performance lp on chb.account_id = lp.account_id
    left join user_engagement_summary ues on chb.account_id = ues.account_id
    left join support_indicators si on chb.account_id = si.account_id
    left join customer_success_scoring css on chb.account_id = css.account_id
    left join expansion_opportunities eo on chb.account_id = eo.account_id
)

select * from final
order by 
    case cs_priority_level
        when 'p0_critical' then 1
        when 'p1_high' then 2
        when 'p1_expansion' then 3
        when 'p2_medium' then 4
        else 5
    end,
    monthly_recurring_revenue desc
