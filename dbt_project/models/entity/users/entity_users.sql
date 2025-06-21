{{ config(
    materialized='table',
    indexes=[
        {'columns': ['user_id'], 'unique': True},
        {'columns': ['account_id']},
        {'columns': ['user_status']},
        {'columns': ['engagement_score']},
        {'columns': ['last_activity_timestamp']}
    ]
) }}

-- Entity: Users (Atomic/Current State)
-- Behavioral focus capturing user engagement, feature adoption, and activity patterns
-- Provides comprehensive view of current user state for operational analytics

with user_core as (
    select * from {{ ref('int_users__core') }}
),

user_engagement as (
    select * from {{ ref('int_users__engagement_metrics') }}
),

final as (
    select
        -- Primary identifiers
        uc.user_id,
        uc.user_key,
        uc.account_id,
        
        -- User profile
        uc.email,
        uc.first_name,
        uc.last_name,
        uc.full_name,
        uc.user_role,
        uc.role_type_standardized,
        uc.user_status,
        uc.access_level,
        uc.email_domain,
        uc.email_type,
        
        -- User categorization
        uc.is_new_user,
        uc.is_admin_user,
        uc.is_manager_user,
        
        -- Lifecycle information
        uc.user_created_at,
        uc.user_age_days,
        uc.user_age_months,
        uc.days_since_last_login,
        
        -- Session activity metrics (30-day)
        uc.total_sessions_30d,
        uc.total_session_minutes_30d,
        uc.avg_session_minutes_30d,
        uc.active_days_30d,
        uc.device_types_used_30d,
        uc.sessions_per_active_day_30d,
        
        -- Feature usage metrics (30-day)
        uc.features_used_30d,
        uc.total_feature_interactions_30d,
        uc.total_feature_uses_30d,
        uc.feature_categories_used_30d,
        uc.avg_features_per_interaction_30d,
        
        -- Page activity metrics (30-day)
        uc.total_page_views_30d,
        uc.total_time_on_pages_30d,
        uc.page_categories_visited_30d,
        uc.page_active_days_30d,
        uc.avg_time_per_page_view_30d,
        
        -- Engagement scoring and classification
        uc.engagement_score_30d as engagement_score,
        uc.activity_level_30d,
        uc.feature_adoption_level,
        ue.user_engagement_tier,
        
        -- Behavioral patterns
        ue.reading_behavior,
        ue.feature_interaction_style,
        ue.feature_success_rate,
        ue.avg_page_views_per_session,
        ue.feature_adoption_ratio,
        
        -- Historical engagement metrics
        ue.total_sessions as lifetime_sessions,
        ue.total_page_views as lifetime_page_views,
        ue.unique_features_used as lifetime_features_used,
        ue.total_feature_interactions as lifetime_feature_interactions,
        
        -- Recent activity metrics (7-day)
        ue.sessions_last_7d,
        ue.page_views_last_7d,
        ue.features_used_last_7d,
        
        -- Activity timestamps
        uc.last_session_start,
        uc.last_feature_usage,
        uc.last_page_view,
        uc.last_activity_timestamp,
        ue.first_session_time,
        ue.first_page_view_time,
        ue.first_feature_use_time,
        
        -- Activity recency
        uc.recency_classification,
        ue.activity_recency,
        
        -- User health and risk indicators
        case 
            when uc.days_since_last_login > 60 then 'high'
            when uc.days_since_last_login > 30 then 'medium'
            when uc.days_since_last_login > 14 then 'low'
            else 'none'
        end as churn_risk_level,
        
        case 
            when uc.engagement_score_30d > 0.7 and uc.feature_categories_used_30d >= 3 then 'high'
            when uc.engagement_score_30d > 0.5 and uc.features_used_30d >= 3 then 'medium'
            when uc.engagement_score_30d > 0.3 then 'low'
            else 'very_low'
        end as user_value_tier,
        
        -- Adoption and maturity indicators
        case 
            when uc.user_age_days < 7 then 'onboarding'
            when uc.user_age_days < 30 then 'new_user'
            when uc.user_age_days < 90 then 'developing'
            when uc.user_age_days < 365 then 'established'
            else 'mature'
        end as user_maturity_stage,
        
        case 
            when uc.features_used_30d >= 10 and uc.feature_categories_used_30d >= 4 then 'complete'
            when uc.features_used_30d >= 5 and uc.feature_categories_used_30d >= 2 then 'substantial'
            when uc.features_used_30d >= 1 then 'minimal'
            else 'none'
        end as feature_adoption_depth,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from user_core uc
    left join user_engagement ue on uc.user_id = ue.user_id
)

select * from final