{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- ML Model: Customer Lifetime Value Prediction
-- Predicts customer lifetime value using behavioral and engagement patterns
-- Model Type: Regression features for external ML pipeline

with clv_features as (
    select
        c.account_id,
        c.account_key,
        c.account_name,
        c.monthly_recurring_revenue,
        c.customer_health_score,
        c.days_since_signup,
        c.device_events_30d,
        c.total_locations,
        c.active_devices,
        c.subscription_status,
        
        -- Historical revenue patterns
        case 
            when c.days_since_signup > 0 
            then c.monthly_recurring_revenue * 12 * (365.0 / c.days_since_signup)
            else c.monthly_recurring_revenue * 12
        end as annualized_revenue_rate,
        
        -- Customer maturity and growth indicators
        case 
            when c.days_since_signup <= 30 then 'new'
            when c.days_since_signup <= 90 then 'ramping'
            when c.days_since_signup <= 365 then 'established'
            else 'mature'
        end as customer_lifecycle_stage,
        
        -- Revenue tier classification
        case 
            when c.monthly_recurring_revenue >= 1000 then 'enterprise'
            when c.monthly_recurring_revenue >= 500 then 'mid_market'
            when c.monthly_recurring_revenue >= 100 then 'small_business'
            else 'startup'
        end as revenue_tier,
        
        -- Engagement and adoption metrics
        coalesce(u_agg.total_users, 0) as total_users,
        coalesce(u_agg.active_users, 0) as active_users,
        coalesce(u_agg.avg_engagement_score, 0) as avg_user_engagement,
        coalesce(u_agg.power_users, 0) as power_users,
        coalesce(u_agg.weekly_active_users, 0) as weekly_active_users,
        
        -- Product adoption depth
        coalesce(feature_agg.unique_features_adopted, 0) as unique_features_adopted,
        coalesce(feature_agg.advanced_features_adopted, 0) as advanced_features_adopted,
        coalesce(feature_agg.feature_success_rate, 0) as feature_success_rate,
        coalesce(feature_agg.total_feature_interactions, 0) as total_feature_interactions,
        
        -- Operational scale and efficiency
        coalesce(d_agg.avg_device_health, 0) as avg_device_health,
        coalesce(d_agg.device_utilization_rate, 0) as device_utilization_rate,
        coalesce(d_agg.events_per_device, 0) as events_per_device,
        
        -- Location expansion indicators
        coalesce(l_agg.avg_location_health, 0) as avg_location_health,
        coalesce(l_agg.geographic_diversity, 0) as geographic_diversity,
        coalesce(l_agg.avg_capacity_utilization, 0) as avg_capacity_utilization,
        
        -- Support and satisfaction metrics
        coalesce(support_agg.total_support_tickets, 0) as total_support_tickets,
        coalesce(support_agg.support_resolution_rate, 1.0) as support_resolution_rate,
        coalesce(support_agg.avg_satisfaction_score, 0.5) as avg_satisfaction_score,
        
        -- Growth trajectory indicators
        coalesce(growth_agg.user_growth_rate, 0) as user_growth_rate,
        coalesce(growth_agg.device_growth_rate, 0) as device_growth_rate,
        coalesce(growth_agg.location_growth_rate, 0) as location_growth_rate,
        coalesce(growth_agg.activity_growth_rate, 0) as activity_growth_rate
        
    from {{ ref('entity_customers') }} c
    
    -- User engagement and adoption metrics
    left join (
        select 
            account_id,
            count(distinct user_id) as total_users,
            count(case when user_status = 'active' then user_id end) as active_users,
            avg(engagement_score) as avg_engagement_score,
            count(case when engagement_score >= 0.8 then user_id end) as power_users,
            count(case when last_active_date >= current_date - 7 then user_id end) as weekly_active_users
        from {{ ref('entity_users') }}
        group by account_id
    ) u_agg on c.account_id = u_agg.account_id
    
    -- Feature adoption metrics
    left join (
        select 
            fu.account_id,
            count(distinct fu.feature_name) as unique_features_adopted,
            count(distinct case when fu.feature_name like '%advanced%' or fu.feature_name like '%admin%' then fu.feature_name end) as advanced_features_adopted,
            avg(case when fu.success_indicator then 1.0 else 0.0 end) as feature_success_rate,
            count(fu.usage_id) as total_feature_interactions
        from {{ ref('stg_app_database__feature_usage') }} fu
        where fu.feature_used_at >= current_date - 30
        group by fu.account_id
    ) feature_agg on c.account_id = feature_agg.account_id
    
    -- Device performance and utilization
    left join (
        select 
            account_id,
            avg(device_health_score) as avg_device_health,
            avg(case when events_30d > 0 then 1.0 else 0.0 end) as device_utilization_rate,
            avg(case when events_30d > 0 then events_30d else null end) as events_per_device
        from {{ ref('entity_devices') }}
        group by account_id
    ) d_agg on c.account_id = d_agg.account_id
    
    -- Location expansion and geographic diversity
    left join (
        select 
            account_id,
            avg(location_health_score) as avg_location_health,
            count(distinct city) as geographic_diversity,
            avg(capacity_utilization_pct) as avg_capacity_utilization
        from {{ ref('entity_locations') }}
        group by account_id
    ) l_agg on c.account_id = l_agg.account_id
    
    -- Support and satisfaction indicators
    left join (
        select 
            account_id,
            sum(support_tickets_open) as total_support_tickets,
            case when sum(support_tickets_open) > 0 then 0.8 else 1.0 end as support_resolution_rate,
            case when sum(support_tickets_open) = 0 then 0.9 else 0.5 end as avg_satisfaction_score
        from {{ ref('entity_locations') }}
        group by account_id
    ) support_agg on c.account_id = support_agg.account_id
    
    -- Growth trajectory analysis
    left join (
        select 
            cd.account_id,
            case 
                when count(*) >= 30 then
                    (count(case when cd.snapshot_date >= current_date - 7 then cd.active_users end)::numeric / 7.0 - 
                     count(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.active_users end)::numeric / 7.0) /
                    nullif(count(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.active_users end)::numeric / 7.0, 0)
                else 0
            end as user_growth_rate,
            case 
                when count(*) >= 30 then
                    (avg(case when cd.snapshot_date >= current_date - 7 then cd.active_devices_today end) - 
                     avg(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.active_devices_today end)) /
                    nullif(avg(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.active_devices_today end), 0)
                else 0
            end as device_growth_rate,
            case 
                when count(*) >= 30 then
                    (avg(case when cd.snapshot_date >= current_date - 7 then cd.active_locations_today end) - 
                     avg(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.active_locations_today end)) /
                    nullif(avg(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.active_locations_today end), 0)
                else 0
            end as location_growth_rate,
            case 
                when count(*) >= 30 then
                    (avg(case when cd.snapshot_date >= current_date - 7 then cd.device_events end) - 
                     avg(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.device_events end)) /
                    nullif(avg(case when cd.snapshot_date between current_date - 30 and current_date - 24 then cd.device_events end), 0)
                else 0
            end as activity_growth_rate
        from {{ ref('entity_customers_daily') }} cd
        group by cd.account_id
    ) growth_agg on c.account_id = growth_agg.account_id
),

clv_calculations as (
    select
        account_id,
        account_key,
        account_name,
        monthly_recurring_revenue,
        customer_health_score,
        days_since_signup,
        customer_lifecycle_stage,
        revenue_tier,
        
        -- Core CLV components
        monthly_recurring_revenue as base_monthly_value,
        
        -- Retention probability based on health and engagement
        case 
            when customer_health_score >= 0.8 and avg_user_engagement >= 0.7 then 0.95
            when customer_health_score >= 0.6 and avg_user_engagement >= 0.5 then 0.85
            when customer_health_score >= 0.4 and avg_user_engagement >= 0.3 then 0.70
            when customer_health_score >= 0.2 then 0.50
            else 0.25
        end as retention_probability,
        
        -- Expected lifetime (in months) based on retention
        case 
            when customer_health_score >= 0.8 and avg_user_engagement >= 0.7 then 36  -- 3 years
            when customer_health_score >= 0.6 and avg_user_engagement >= 0.5 then 24  -- 2 years
            when customer_health_score >= 0.4 and avg_user_engagement >= 0.3 then 18  -- 1.5 years
            when customer_health_score >= 0.2 then 12  -- 1 year
            else 6  -- 6 months
        end as expected_lifetime_months,
        
        -- Expansion probability based on usage and growth
        case 
            when total_users >= 5 and unique_features_adopted >= 5 and device_utilization_rate >= 0.8 then 0.4
            when total_users >= 3 and unique_features_adopted >= 3 and device_utilization_rate >= 0.6 then 0.25
            when total_users >= 2 and unique_features_adopted >= 2 then 0.15
            else 0.05
        end as expansion_probability,
        
        -- Expected expansion value
        case 
            when revenue_tier = 'enterprise' then monthly_recurring_revenue * 0.3
            when revenue_tier = 'mid_market' then monthly_recurring_revenue * 0.4
            when revenue_tier = 'small_business' then monthly_recurring_revenue * 0.5
            else monthly_recurring_revenue * 0.6
        end as expected_expansion_value,
        
        -- All base features for analysis
        total_users,
        active_users,
        avg_user_engagement,
        power_users,
        weekly_active_users,
        unique_features_adopted,
        advanced_features_adopted,
        feature_success_rate,
        total_feature_interactions,
        avg_device_health,
        device_utilization_rate,
        events_per_device,
        avg_location_health,
        geographic_diversity,
        avg_capacity_utilization,
        total_support_tickets,
        support_resolution_rate,
        avg_satisfaction_score,
        user_growth_rate,
        device_growth_rate,
        location_growth_rate,
        activity_growth_rate
        
    from clv_features
),

clv_predictions as (
    select
        account_id,
        account_key,
        account_name,
        monthly_recurring_revenue,
        customer_health_score,
        customer_lifecycle_stage,
        revenue_tier,
        
        -- CLV calculation components
        base_monthly_value,
        retention_probability,
        expected_lifetime_months,
        expansion_probability,
        expected_expansion_value,
        
        -- Core CLV calculation
        (base_monthly_value * expected_lifetime_months * retention_probability) as base_clv,
        
        -- CLV with expansion potential
        (base_monthly_value * expected_lifetime_months * retention_probability + 
         expected_expansion_value * expansion_probability * (expected_lifetime_months * 0.6)) as clv_with_expansion,
        
        -- Conservative CLV (discounted for risk)
        (base_monthly_value * expected_lifetime_months * retention_probability * 0.8) as conservative_clv,
        
        -- Optimistic CLV (with maximum expansion)
        (base_monthly_value * expected_lifetime_months * retention_probability + 
         expected_expansion_value * expansion_probability * expected_lifetime_months) as optimistic_clv,
        
        -- CLV confidence scoring
        case 
            when days_since_signup >= 180 and customer_health_score >= 0.6 then 'high_confidence'
            when days_since_signup >= 90 and customer_health_score >= 0.4 then 'medium_confidence'
            when days_since_signup >= 30 then 'low_confidence'
            else 'very_low_confidence'
        end as clv_confidence,
        
        -- Customer value tier
        case 
            when (base_monthly_value * expected_lifetime_months * retention_probability) >= 10000 then 'high_value'
            when (base_monthly_value * expected_lifetime_months * retention_probability) >= 5000 then 'medium_value'
            when (base_monthly_value * expected_lifetime_months * retention_probability) >= 1000 then 'standard_value'
            else 'low_value'
        end as customer_value_tier,
        
        -- Growth potential classification
        case 
            when expansion_probability >= 0.3 and user_growth_rate > 0.1 then 'high_growth_potential'
            when expansion_probability >= 0.15 and user_growth_rate > 0 then 'medium_growth_potential'
            when expansion_probability >= 0.05 then 'low_growth_potential'
            else 'minimal_growth_potential'
        end as growth_potential,
        
        -- Investment recommendations
        case 
            when (base_monthly_value * expected_lifetime_months * retention_probability) >= 10000 
                 and expansion_probability >= 0.3 then 'high_touch_account_management'
            when (base_monthly_value * expected_lifetime_months * retention_probability) >= 5000 
                 and customer_health_score >= 0.6 then 'dedicated_customer_success'
            when expansion_probability >= 0.25 then 'growth_focused_engagement'
            when retention_probability < 0.6 then 'retention_focused_intervention'
            else 'standard_customer_success'
        end as recommended_investment_strategy,
        
        -- Key success metrics for tracking
        total_users,
        avg_user_engagement,
        unique_features_adopted,
        avg_device_health,
        device_utilization_rate,
        geographic_diversity,
        user_growth_rate,
        activity_growth_rate,
        
        -- Model metadata
        current_timestamp as clv_calculated_at
        
    from clv_calculations
)

select * from clv_predictions
order by clv_with_expansion desc, base_clv desc
