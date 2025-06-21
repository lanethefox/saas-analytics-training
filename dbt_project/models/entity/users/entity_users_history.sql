{{ config(
    materialized='incremental',
    unique_key='user_history_id',
    on_schema_change='sync_all_columns',
    indexes=[
        {'columns': ['user_id', 'valid_from']},
        {'columns': ['valid_from']},
        {'columns': ['change_type']}
    ]
) }}

-- Entity: Users (History/Change Tracking)
-- Tracks user engagement evolution, feature adoption progressions, and behavioral changes
-- Enables user journey analysis, behavioral pattern recognition, and A/B test analysis

with user_current as (
    select * from {{ ref('entity_users') }}
),

history_records as (
    select
        -- Generate unique history ID
        {{ dbt_utils.generate_surrogate_key(['user_id', 'current_timestamp']) }} as user_history_id,
        
        -- User identifiers
        user_id,
        user_key,
        account_id,
        
        -- Change tracking (simplified for initial implementation)
        'snapshot' as change_type,
        
        -- User profile
        email,
        full_name,
        user_role,
        role_type_standardized,
        user_status,
        access_level,
        
        -- Engagement metrics
        engagement_score,
        0::numeric as previous_engagement_score,
        0::numeric as engagement_delta,
        
        activity_level_30d,
        ''::text as previous_activity_level,
        
        user_engagement_tier,
        ''::text as previous_engagement_tier,
        
        -- Feature adoption
        features_used_30d,
        0::integer as previous_features_used_30d,
        0::integer as features_adopted_delta,
        
        feature_adoption_level,
        ''::text as previous_adoption_level,
        
        feature_categories_used_30d,
        lifetime_features_used,
        
        -- Activity metrics
        total_sessions_30d,
        0::integer as previous_sessions_30d,
        0::integer as sessions_delta,
        
        active_days_30d,
        total_page_views_30d,
        avg_session_minutes_30d,
        
        -- Behavioral attributes
        reading_behavior,
        feature_interaction_style,
        feature_success_rate,
        avg_page_views_per_session,
        
        -- Risk and value indicators
        churn_risk_level,
        ''::text as previous_churn_risk_level,
        
        user_value_tier,
        ''::text as previous_value_tier,
        
        user_maturity_stage,
        feature_adoption_depth,
        
        -- Lifecycle metrics
        user_age_days,
        days_since_last_login,
        last_activity_timestamp,
        
        -- Temporal validity
        current_timestamp as valid_from,
        null::timestamp as valid_to,
        true as is_current,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from user_current
    
    {% if is_incremental() %}
    -- For incremental runs, only capture changes
    where not exists (
        select 1 
        from {{ this }} h
        where h.user_id = user_current.user_id
          and h.is_current = true
          and h.engagement_score = user_current.engagement_score
          and h.user_status = user_current.user_status
          and h.feature_adoption_level = user_current.feature_adoption_level
          and h.user_engagement_tier = user_current.user_engagement_tier
    )
    {% endif %}
)

select * from history_records