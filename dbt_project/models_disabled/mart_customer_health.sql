{{ config(materialized='table') }}

-- Customer Success Mart: Customer Health and Engagement Dashboard
-- Comprehensive customer health metrics for proactive success management
-- Primary users: Customer success managers, account managers, executives

with customer_health_summary as (
    select
        c.account_id,
        c.account_name,
        c.account_type,
        c.subscription_status,
        c.monthly_recurring_revenue,
        c.annual_recurring_revenue,
        c.customer_health_score,
        c.churn_risk_score,
        c.total_locations,
        c.total_devices,
        c.active_devices,
        c.device_events_30d,
        c.days_since_signup,
        c.days_since_last_activity,
        c.headquarters_country,
        c.industry_vertical,
        
        -- User engagement from entity
        u.total_users,
        u.active_users,
        u.engagement_score as avg_user_engagement,
        u.latest_user_login
        
    from {{ ref('entity_customers') }} c
    left join (
        select 
            account_id,
            count(*) as total_users,
            count(case when user_health_status = 'healthy' then 1 end) as active_users,
            avg(engagement_score) as engagement_score,
            max(last_login_at) as latest_user_login
        from {{ ref('entity_users') }}
        group by account_id
    ) u on c.account_id = u.account_id
),

feature_adoption_analysis as (
    select
        fu.account_id,
        count(distinct fu.feature_name) as total_features_adopted,
        count(distinct case when f.adoption_tier in ('widely_adopted', 'moderately_adopted') then fu.feature_name end) as key_features_adopted,
        count(distinct case when f.revenue_impact_tier in ('high_revenue_impact', 'medium_revenue_impact') then fu.feature_name end) as revenue_features_adopted,
        avg(case when fu.success_indicator then 1.0 else 0.0 end) as feature_success_rate,
        max(fu.usage_timestamp) as last_feature_usage,
        
        -- Advanced feature metrics
        count(distinct case when f.strategic_value_score >= 0.8 then fu.feature_name end) as strategic_features_adopted,
        count(distinct fu.user_id) as users_using_features,
        avg(fu.usage_duration_seconds) as avg_feature_engagement_time
        
    from {{ ref('stg_app_database__feature_usage') }} fu
    join {{ ref('entity_features') }} f on fu.feature_name = f.feature_name
    where fu.usage_timestamp >= current_date - 30
    group by fu.account_id
),

location_performance as (
    select
        l.account_id,
        count(*) as total_locations,
        count(case when l.operational_health_score >= 0.8 then 1 end) as high_performing_locations,
        count(case when l.risk_status = 'at_risk' then 1 end) as at_risk_locations,
        avg(l.operational_health_score) as avg_location_health,
        avg(l.customer_satisfaction_score) as avg_customer_satisfaction,
        sum(l.support_requests_30d) as total_support_requests_30d,
        avg(l.location_efficiency_score) as avg_location_efficiency
        
    from {{ ref('entity_locations') }} l
    group by l.account_id
),

recent_activity_trends as (
    select
        cd.account_id,
        
        -- 7-day trends
        avg(case when cd.snapshot_date >= current_date - 7 then cd.daily_device_events else null end) as avg_daily_events_7d,
        avg(case when cd.snapshot_date >= current_date - 7 then cd.daily_active_users else null end) as avg_daily_users_7d,
        avg(case when cd.snapshot_date >= current_date - 7 then cd.daily_health_score else null end) as avg_health_score_7d,
        
        -- 30-day trends
        avg(case when cd.snapshot_date >= current_date - 30 then cd.daily_device_events else null end) as avg_daily_events_30d,
        avg(case when cd.snapshot_date >= current_date - 30 then cd.daily_active_users else null end) as avg_daily_users_30d,
        avg(case when cd.snapshot_date >= current_date - 30 then cd.daily_health_score else null end) as avg_health_score_30d,
        
        -- Trend calculations
        case 
            when avg(case when cd.snapshot_date >= current_date - 7 then cd.daily_device_events else null end) >
                 avg(case when cd.snapshot_date between current_date - 14 and current_date - 8 then cd.daily_device_events else null end) * 1.1
            then 'increasing'
            when avg(case when cd.snapshot_date >= current_date - 7 then cd.daily_device_events else null end) <
                 avg(case when cd.snapshot_date between current_date - 14 and current_date - 8 then cd.daily_device_events else null end) * 0.9
            then 'decreasing'
            else 'stable'
        end as activity_trend_7d
        
    from {{ ref('entity_customers_daily') }} cd
    where cd.snapshot_date >= current_date - 30
    group by cd.account_id
),

final as (
    select
        current_date as report_date,
        
        -- Customer identification
        chs.account_id,
        chs.account_name,
        chs.account_type,
        chs.subscription_status,
        chs.headquarters_country,
        chs.industry_vertical,
        
        -- Revenue metrics
        chs.monthly_recurring_revenue,
        chs.annual_recurring_revenue,
        
        case 
            when chs.annual_recurring_revenue >= 100000 then 'enterprise'
            when chs.annual_recurring_revenue >= 25000 then 'mid_market'
            when chs.annual_recurring_revenue >= 5000 then 'small_business'
            else 'startup'
        end as revenue_segment,
        
        -- Health scores
        chs.customer_health_score,
        chs.churn_risk_score,
        lp.avg_location_health,
        chs.avg_user_engagement,
        
        -- Composite health score
        (chs.customer_health_score * 0.4 + 
         coalesce(lp.avg_location_health, 0) * 0.3 + 
         coalesce(chs.avg_user_engagement, 0) * 0.3) as composite_health_score,
        
        -- Infrastructure metrics
        chs.total_locations,
        chs.total_devices,
        chs.active_devices,
        lp.high_performing_locations,
        lp.at_risk_locations,
        
        case 
            when chs.total_devices > 0 
            then chs.active_devices::numeric / chs.total_devices
            else 0
        end as device_utilization_rate,
        
        case 
            when chs.total_locations > 0 
            then lp.high_performing_locations::numeric / chs.total_locations
            else 0
        end as high_performing_location_rate,
        
        -- Activity and engagement
        chs.device_events_30d,
        rat.avg_daily_events_30d,
        rat.avg_daily_users_30d,
        rat.activity_trend_7d,
        chs.total_users,
        chs.active_users,
        
        case 
            when chs.total_users > 0 
            then chs.active_users::numeric / chs.total_users
            else 0
        end as user_activation_rate,
        
        -- Feature adoption
        faa.total_features_adopted,
        faa.key_features_adopted,
        faa.revenue_features_adopted,
        faa.strategic_features_adopted,
        faa.feature_success_rate,
        faa.users_using_features,
        
        case 
            when faa.total_features_adopted >= 10 then 'power_adopter'
            when faa.total_features_adopted >= 5 then 'moderate_adopter'
            when faa.total_features_adopted >= 2 then 'basic_adopter'
            when faa.total_features_adopted >= 1 then 'minimal_adopter'
            else 'non_adopter'
        end as feature_adoption_tier,
        
        -- Support and satisfaction
        lp.avg_customer_satisfaction,
        lp.total_support_requests_30d,
        
        case 
            when lp.total_support_requests_30d >= 10 then 'high_touch'
            when lp.total_support_requests_30d >= 5 then 'medium_touch'
            when lp.total_support_requests_30d >= 1 then 'low_touch'
            else 'self_service'
        end as support_intensity,
        
        -- Temporal context
        chs.days_since_signup,
        chs.days_since_last_activity,
        
        case 
            when chs.days_since_signup <= 30 then 'onboarding'
            when chs.days_since_signup <= 90 then 'early_adoption'
            when chs.days_since_signup <= 365 then 'growth_phase'
            else 'mature'
        end as customer_lifecycle_stage,
        
        -- Risk assessment
        case 
            when chs.churn_risk_score >= 0.8 then 'critical_risk'
            when chs.churn_risk_score >= 0.6 then 'high_risk'
            when chs.churn_risk_score >= 0.4 then 'medium_risk'
            when chs.churn_risk_score >= 0.2 then 'low_risk'
            else 'healthy'
        end as churn_risk_tier,
        
        case 
            when chs.churn_risk_score >= 0.7 and chs.annual_recurring_revenue >= 25000 then 'immediate_intervention'
            when chs.churn_risk_score >= 0.6 then 'proactive_outreach'
            when chs.customer_health_score <= 0.5 and chs.days_since_last_activity > 14 then 'engagement_campaign'
            when faa.feature_adoption_tier = 'minimal_adopter' and chs.days_since_signup > 60 then 'adoption_support'
            when lp.total_support_requests_30d >= 5 then 'success_check_in'
            else 'standard_cadence'
        end as recommended_action,
        
        -- Success opportunities
        case 
            when composite_health_score >= 0.8 and chs.annual_recurring_revenue < 50000 then 'expansion_opportunity'
            when faa.key_features_adopted < 3 and chs.customer_health_score >= 0.7 then 'feature_expansion'
            when high_performing_location_rate >= 0.8 and chs.total_locations < 10 then 'location_expansion'
            when user_activation_rate < 0.7 and chs.total_users >= 5 then 'user_adoption'
            when lp.avg_customer_satisfaction >= 4.5 then 'reference_candidate'
            else 'maintain_health'
        end as growth_opportunity,
        
        -- Account priority scoring
        case 
            when chs.annual_recurring_revenue >= 100000 and chs.churn_risk_score >= 0.6 then 4  -- Critical enterprise
            when chs.annual_recurring_revenue >= 50000 and chs.churn_risk_score >= 0.5 then 3   -- High priority
            when chs.churn_risk_score >= 0.7 then 3                                            -- High risk any size
            when chs.annual_recurring_revenue >= 25000 then 2                                  -- Medium priority
            else 1                                                                             -- Standard priority
        end as account_priority_score,
        
        current_timestamp as _mart_created_at
        
    from customer_health_summary chs
    left join feature_adoption_analysis faa on chs.account_id = faa.account_id
    left join location_performance lp on chs.account_id = lp.account_id
    left join recent_activity_trends rat on chs.account_id = rat.account_id
)

select * from final
