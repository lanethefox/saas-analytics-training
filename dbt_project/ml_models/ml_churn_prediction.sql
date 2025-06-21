{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- ML Model: Customer Churn Prediction
-- Predicts customer churn probability using entity-centric features
-- Model Type: Logistic Regression features for external ML pipeline

with churn_features as (
    select
        c.account_id,
        c.account_key,
        c.account_name,
        c.customer_health_score,
        c.monthly_recurring_revenue,
        c.device_events_30d,
        c.total_locations,
        c.active_devices,
        c.days_since_signup,
        
        -- User engagement features
        coalesce(u_agg.total_users, 0) as total_users,
        coalesce(u_agg.active_users, 0) as active_users,
        coalesce(u_agg.avg_engagement_score, 0) as avg_user_engagement,
        coalesce(u_agg.admin_users, 0) as admin_users,
        coalesce(u_agg.users_last_7d, 0) as users_active_last_7d,
        
        -- Device performance features
        coalesce(d_agg.avg_device_health, 0) as avg_device_health,
        coalesce(d_agg.avg_uptime, 0) as avg_device_uptime,
        coalesce(d_agg.devices_needing_maintenance, 0) as devices_needing_maintenance,
        coalesce(d_agg.inactive_devices, 0) as inactive_devices,
        
        -- Location operational features
        coalesce(l_agg.avg_location_health, 0) as avg_location_health,
        coalesce(l_agg.avg_capacity_utilization, 0) as avg_capacity_utilization,
        coalesce(l_agg.total_support_tickets, 0) as total_support_tickets,
        coalesce(l_agg.underperforming_locations, 0) as underperforming_locations,
        
        -- Temporal features (trend analysis)
        coalesce(daily_trend.avg_daily_events_week1, 0) as avg_daily_events_week1,
        coalesce(daily_trend.avg_daily_events_week4, 0) as avg_daily_events_week4,
        coalesce(daily_trend.event_trend_slope, 0) as event_trend_slope,
        
        -- Product adoption features
        coalesce(feature_agg.total_feature_interactions, 0) as total_feature_interactions,
        coalesce(feature_agg.unique_features_used, 0) as unique_features_used,
        coalesce(feature_agg.feature_success_rate, 0) as feature_success_rate,
        coalesce(feature_agg.advanced_features_used, 0) as advanced_features_used,
        
        -- Business context features
        case when c.monthly_recurring_revenue >= 1000 then 1 else 0 end as is_enterprise_customer,
        case when c.total_locations >= 5 then 1 else 0 end as is_multi_location,
        case when c.days_since_signup <= 30 then 1 else 0 end as is_new_customer,
        case when c.days_since_signup <= 90 then 1 else 0 end as is_onboarding_customer,
        
        -- Churn indicators (target variable for training)
        case 
            when c.subscription_status = 'cancelled' then 1
            when c.customer_health_score < 0.3 then 1
            when c.churn_risk_score > 0.8 then 1
            else 0
        end as is_churned,
        
        -- Risk tier classification
        case 
            when c.churn_risk_score >= 0.8 then 'high_risk'
            when c.churn_risk_score >= 0.6 then 'medium_risk'
            when c.churn_risk_score >= 0.4 then 'low_risk'
            else 'healthy'
        end as current_risk_tier
        
    from {{ ref('entity_customers') }} c
    
    -- User engagement aggregations
    left join (
        select 
            account_id,
            count(distinct user_id) as total_users,
            count(case when user_status = 'active' then user_id end) as active_users,
            avg(engagement_score) as avg_engagement_score,
            count(case when role_type_standardized = 'admin' then user_id end) as admin_users,
            count(case when last_active_date >= current_date - 7 then user_id end) as users_last_7d
        from {{ ref('entity_users') }}
        group by account_id
    ) u_agg on c.account_id = u_agg.account_id
    
    -- Device performance aggregations
    left join (
        select 
            account_id,
            avg(device_health_score) as avg_device_health,
            avg(uptime_percentage_30d) as avg_uptime,
            count(case when last_maintenance_date < current_date - 90 then device_id end) as devices_needing_maintenance,
            count(case when device_status = 'inactive' then device_id end) as inactive_devices
        from {{ ref('entity_devices') }}
        group by account_id
    ) d_agg on c.account_id = d_agg.account_id
    
    -- Location operational aggregations
    left join (
        select 
            account_id,
            avg(location_health_score) as avg_location_health,
            avg(capacity_utilization_pct) as avg_capacity_utilization,
            sum(support_tickets_open) as total_support_tickets,
            count(case when location_health_score < 0.5 then location_id end) as underperforming_locations
        from {{ ref('entity_locations') }}
        group by account_id
    ) l_agg on c.account_id = l_agg.account_id
    
    -- Temporal trend analysis
    left join (
        select 
            account_id,
            avg(case when snapshot_date >= current_date - 7 then device_events end) as avg_daily_events_week1,
            avg(case when snapshot_date between current_date - 28 and current_date - 22 then device_events end) as avg_daily_events_week4,
            -- Simple linear trend calculation
            case 
                when count(*) >= 14 then
                    (avg(case when snapshot_date >= current_date - 7 then device_events end) - 
                     avg(case when snapshot_date between current_date - 28 and current_date - 22 then device_events end))
                else 0
            end as event_trend_slope
        from {{ ref('entity_customers_daily') }}
        group by account_id
    ) daily_trend on c.account_id = daily_trend.account_id
    
    -- Feature usage aggregations
    left join (
        select 
            fu.account_id,
            count(fu.usage_id) as total_feature_interactions,
            count(distinct fu.feature_name) as unique_features_used,
            avg(case when fu.success_indicator then 1.0 else 0.0 end) as feature_success_rate,
            count(distinct case when fu.feature_name like '%admin%' or fu.feature_name like '%advanced%' then fu.feature_name end) as advanced_features_used
        from {{ ref('stg_app_database__feature_usage') }} fu
        where fu.feature_used_at >= current_date - 30
        group by fu.account_id
    ) feature_agg on c.account_id = feature_agg.account_id
),

churn_prediction_features as (
    select
        account_id,
        account_key,
        account_name,
        
        -- Core health and business metrics
        customer_health_score,
        monthly_recurring_revenue,
        device_events_30d,
        total_locations,
        active_devices,
        days_since_signup,
        
        -- Engagement metrics
        total_users,
        active_users,
        avg_user_engagement,
        admin_users,
        users_active_last_7d,
        
        -- Device performance metrics
        avg_device_health,
        avg_device_uptime,
        devices_needing_maintenance,
        inactive_devices,
        
        -- Location operational metrics
        avg_location_health,
        avg_capacity_utilization,
        total_support_tickets,
        underperforming_locations,
        
        -- Trend and temporal features
        avg_daily_events_week1,
        avg_daily_events_week4,
        event_trend_slope,
        
        -- Product adoption metrics
        total_feature_interactions,
        unique_features_used,
        feature_success_rate,
        advanced_features_used,
        
        -- Categorical features
        is_enterprise_customer,
        is_multi_location,
        is_new_customer,
        is_onboarding_customer,
        
        -- Target and current state
        is_churned,
        current_risk_tier,
        
        -- Derived risk indicators
        case 
            when avg_user_engagement < 0.3 then 1 else 0 
        end as low_engagement_risk,
        
        case 
            when device_events_30d = 0 then 1 else 0 
        end as zero_activity_risk,
        
        case 
            when total_support_tickets >= 5 then 1 else 0 
        end as high_support_burden_risk,
        
        case 
            when avg_device_health < 0.4 then 1 else 0 
        end as poor_device_health_risk,
        
        case 
            when users_active_last_7d = 0 and total_users > 0 then 1 else 0 
        end as no_recent_users_risk,
        
        -- Composite risk score (simple weighted sum)
        (
            (1 - customer_health_score) * 0.3 +
            case when device_events_30d = 0 then 0.2 else 0 end +
            case when avg_user_engagement < 0.3 then 0.15 else 0 end +
            case when total_support_tickets >= 5 then 0.1 else 0 end +
            case when avg_device_health < 0.4 then 0.1 else 0 end +
            case when users_active_last_7d = 0 and total_users > 0 then 0.15 else 0 end
        ) as calculated_churn_probability,
        
        -- Model prediction confidence
        case 
            when is_churned = 1 then 'high_confidence'
            when customer_health_score < 0.3 or device_events_30d = 0 then 'medium_confidence'
            else 'low_confidence'
        end as prediction_confidence,
        
        -- Intervention recommendations
        case 
            when device_events_30d = 0 then 'immediate_activation_intervention'
            when avg_user_engagement < 0.3 then 'user_engagement_program'
            when total_support_tickets >= 5 then 'technical_support_escalation'
            when avg_device_health < 0.4 then 'device_optimization_program'
            when users_active_last_7d = 0 and total_users > 0 then 'user_reactivation_campaign'
            else 'standard_customer_success'
        end as recommended_intervention,
        
        -- Metadata
        current_timestamp as model_generated_at
        
    from churn_features
)

select * from churn_prediction_features
order by calculated_churn_probability desc, monthly_recurring_revenue desc
