{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Entity: Features (Atomic View)
-- Current-state feature view with adoption metrics and business impact
-- Primary use cases: Product planning, feature prioritization, adoption tracking

with feature_core as (
    select * from {{ ref('int_features__core') }}
),

feature_user_segments as (
    select
        fu.feature_name,
        count(distinct case when u.role_type = 'owner' then fu.user_id end) as owner_users,
        count(distinct case when u.role_type = 'admin' then fu.user_id end) as admin_users,
        count(distinct case when u.role_type = 'manager' then fu.user_id end) as manager_users,
        count(distinct case when u.role_type = 'operator' then fu.user_id end) as operator_users,
        count(distinct case when a.account_type = 'enterprise' then fu.user_id end) as enterprise_users,
        count(distinct case when a.account_type = 'professional' then fu.user_id end) as professional_users,
        count(distinct case when a.account_type = 'basic' then fu.user_id end) as basic_users
    from {{ ref('stg_app_database__feature_usage') }} fu
    join {{ ref('stg_app_database__users') }} u on fu.user_id = u.user_id
    join {{ ref('stg_app_database__accounts') }} a on fu.account_id = a.account_id
    where fu.usage_timestamp >= current_date - 30
    group by fu.feature_name
),

feature_device_correlation as (
    select
        fu.feature_name,
        count(distinct te.device_id) as devices_used_with_feature,
        avg(te.total_volume_ml) as avg_volume_when_feature_used,
        count(distinct te.location_id) as locations_using_feature
    from {{ ref('stg_app_database__feature_usage') }} fu
    join {{ ref('stg_app_database__tap_events') }} te 
        on fu.account_id = te.account_id 
        and date_trunc('day', fu.usage_timestamp) = te.event_date
    where fu.usage_timestamp >= current_date - 30
    group by fu.feature_name
),

final as (
    select
        -- Core identifiers and attributes
        fc.feature_key,
        fc.feature_name,
        fc.feature_category,
        
        -- Adoption metrics
        fc.unique_users_30d,
        fc.unique_accounts_30d,
        fc.user_adoption_rate,
        fc.account_adoption_rate,
        fc.weekly_active_users,
        fc.daily_active_users,
        
        -- Engagement metrics
        fc.total_interactions_30d,
        fc.successful_uses_30d,
        fc.success_rate,
        fc.avg_interactions_per_user,
        fc.avg_usage_duration_seconds,
        fc.weekly_retention_rate,
        fc.daily_weekly_ratio,
        
        -- Revenue impact
        fc.revenue_generating_accounts,
        fc.associated_mrr,
        fc.avg_mrr_per_feature_account,
        fc.revenue_per_adopting_account,
        
        -- User segmentation
        coalesce(fus.owner_users, 0) as owner_users,
        coalesce(fus.admin_users, 0) as admin_users,
        coalesce(fus.manager_users, 0) as manager_users,
        coalesce(fus.operator_users, 0) as operator_users,
        coalesce(fus.enterprise_users, 0) as enterprise_users,
        coalesce(fus.professional_users, 0) as professional_users,
        coalesce(fus.basic_users, 0) as basic_users,
        
        -- Device/operational correlation
        coalesce(fdc.devices_used_with_feature, 0) as devices_used_with_feature,
        coalesce(fdc.avg_volume_when_feature_used, 0) as avg_volume_when_feature_used,
        coalesce(fdc.locations_using_feature, 0) as locations_using_feature,
        
        -- Calculated segmentation metrics
        case 
            when fc.unique_users_30d > 0 
            then fus.owner_users::numeric / fc.unique_users_30d
            else 0
        end as owner_user_ratio,
        
        case 
            when fc.unique_users_30d > 0 
            then fus.enterprise_users::numeric / fc.unique_users_30d
            else 0
        end as enterprise_user_ratio,
        
        -- Feature health scoring
        case 
            when fc.user_adoption_rate >= 0.5 
                and fc.success_rate >= 0.8
                and fc.weekly_retention_rate >= 0.6
                and fc.associated_mrr >= 10000
            then 0.95
            when fc.user_adoption_rate >= 0.25 
                and fc.success_rate >= 0.6
                and fc.weekly_retention_rate >= 0.4
                and fc.associated_mrr >= 2000
            then 0.75
            when fc.user_adoption_rate >= 0.1 
                and fc.success_rate >= 0.4
                and fc.unique_users_30d >= 50
            then 0.5
            when fc.unique_users_30d >= 10
            then 0.25
            else 0.1
        end as feature_health_score,
        
        -- Strategic classifications
        fc.adoption_tier,
        fc.success_tier,
        fc.engagement_tier,
        fc.revenue_impact_tier,
        fc.strategic_value_score,
        
        -- Business value assessment
        case 
            when fc.strategic_value_score >= 0.8 then 'core_feature'
            when fc.strategic_value_score >= 0.6 then 'important_feature'
            when fc.strategic_value_score >= 0.4 then 'supplementary_feature'
            when fc.strategic_value_score >= 0.2 then 'niche_feature'
            else 'experimental_feature'
        end as business_value_tier,
        
        case 
            when fc.user_adoption_rate >= 0.5 and fc.revenue_impact_tier in ('high_revenue_impact', 'medium_revenue_impact') then 'revenue_driver'
            when fc.user_adoption_rate >= 0.25 and fc.success_tier = 'highly_successful' then 'engagement_driver'
            when fc.enterprise_user_ratio >= 0.6 then 'enterprise_focused'
            when fc.user_adoption_rate < 0.1 and fc.feature_age_days > 90 then 'underperforming'
            else 'standard'
        end as feature_role_classification,
        
        -- Product development indicators
        case 
            when fc.success_rate < 0.5 and fc.total_interactions_30d > 100 then 'needs_improvement'
            when fc.user_adoption_rate < 0.05 and fc.feature_age_days > 180 then 'consider_deprecation'
            when fc.weekly_retention_rate < 0.3 and fc.user_adoption_rate > 0.1 then 'retention_issue'
            when fc.daily_weekly_ratio > 0.8 and fc.user_adoption_rate > 0.2 then 'high_engagement_opportunity'
            else 'stable'
        end as product_action_recommendation,
        
        -- Lifecycle indicators
        fc.feature_lifecycle_stage,
        fc.feature_health_status,
        fc.feature_age_days,
        fc.days_since_last_usage,
        
        -- Temporal attributes
        fc.first_usage_date,
        fc.last_usage_date,
        
        -- Metadata
        current_timestamp as entity_updated_at
        
    from feature_core fc
    left join feature_user_segments fus on fc.feature_name = fus.feature_name
    left join feature_device_correlation fdc on fc.feature_name = fdc.feature_name
)

select * from final
