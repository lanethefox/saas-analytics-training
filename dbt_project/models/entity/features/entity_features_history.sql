{{ config(
    materialized='incremental',
    unique_key='feature_history_id',
    on_schema_change='sync_all_columns',
    indexes=[
        {'columns': ['feature_name', 'valid_from']},
        {'columns': ['valid_from']},
        {'columns': ['change_type']}
    ]
) }}

-- Entity: Features (History/Change Tracking)
-- Tracks feature evolution including releases, adoption progressions, and usage changes
-- Enables product analytics, feature lifecycle analysis, and roadmap planning

with feature_current as (
    select * from {{ ref('entity_features') }}
),

history_records as (
    select
        -- Generate unique history ID
        {{ dbt_utils.generate_surrogate_key(['feature_name', 'current_timestamp']) }} as feature_history_id,
        
        -- Feature identifiers
        feature_name,
        feature_key,
        feature_category,
        
        -- Change tracking
        'snapshot' as change_type,
        
        -- Usage metrics at time of change
        accounts_using,
        users_using,
        total_usage_events,
        
        -- Adoption metrics
        account_adoption_rate,
        0::numeric as previous_adoption_rate,
        0::numeric as adoption_rate_change,
        
        user_adoption_rate,
        adoption_stage,
        ''::text as previous_adoption_stage,
        
        -- Segment adoption
        enterprise_adopters,
        business_adopters,
        starter_adopters,
        
        -- Value metrics
        feature_value_score,
        0::numeric as previous_value_score,
        0::numeric as value_score_change,
        
        avg_mrr_adopters,
        estimated_revenue_impact,
        
        -- Strategic classification
        strategic_importance,
        ''::text as previous_strategic_importance,
        
        market_fit_segment,
        engagement_level,
        ''::text as previous_engagement_level,
        
        -- Lifecycle tracking
        lifecycle_stage,
        ''::text as previous_lifecycle_stage,
        
        feature_maturity,
        roadmap_recommendation,
        
        -- Stickiness metrics
        enterprise_stickiness_rate,
        business_stickiness_rate,
        starter_stickiness_rate,
        
        -- Usage patterns
        usage_frequency,
        satisfaction_score,
        
        -- Key dates
        first_usage_date,
        last_usage_date,
        feature_age_days,
        
        -- Temporal validity
        current_timestamp as valid_from,
        null::timestamp as valid_to,
        true as is_current,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from feature_current
    
    {% if is_incremental() %}
    -- For incremental runs, only capture meaningful changes
    where not exists (
        select 1 
        from {{ this }} h
        where h.feature_name = feature_current.feature_name
          and h.is_current = true
          and h.adoption_stage = feature_current.adoption_stage
          and h.feature_value_score = feature_current.feature_value_score
          and h.strategic_importance = feature_current.strategic_importance
          and h.lifecycle_stage = feature_current.lifecycle_stage
    )
    {% endif %}
)

select * from history_records