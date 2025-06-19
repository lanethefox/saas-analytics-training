{{ config(
    materialized='table',
    indexes=[
        {'columns': ['feature_name'], 'unique': True},
        {'columns': ['feature_category']},
        {'columns': ['adoption_stage']},
        {'columns': ['feature_value_score']},
        {'columns': ['strategic_importance']}
    ]
) }}

-- Entity: Features (Atomic/Current State)
-- Product focus capturing usage metrics, customer segments, and business impact
-- Provides comprehensive view of current feature state for product planning

with feature_core as (
    select * from {{ ref('int_features__core') }}
),

feature_adoption as (
    select * from {{ ref('int_features__adoption_patterns') }}
),

final as (
    select
        -- Primary identifiers
        fc.feature_key,
        fc.feature_name,
        fc.feature_category,
        
        -- Usage metrics
        fc.accounts_using,
        fc.users_using,
        fc.total_usage_events,
        fc.avg_usage_per_account,
        fc.avg_daily_usage,
        
        -- Adoption rates
        fc.account_adoption_rate,
        fc.user_adoption_rate,
        fc.adoption_stage,
        
        -- Adoption by segment
        coalesce(fa.enterprise_adopters, 0) as enterprise_adopters,
        coalesce(fa.business_adopters, 0) as business_adopters,
        coalesce(fa.starter_adopters, 0) as starter_adopters,
        
        -- Revenue correlation
        coalesce(fa.avg_mrr_adopters, 0) as avg_mrr_adopters,
        
        -- Adoption velocity
        coalesce(fa.avg_days_to_adoption_enterprise, 0) as avg_days_to_adoption_enterprise,
        coalesce(fa.avg_days_to_adoption_business, 0) as avg_days_to_adoption_business,
        coalesce(fa.avg_days_to_adoption_starter, 0) as avg_days_to_adoption_starter,
        coalesce(fa.enterprise_adoption_velocity, 'unknown') as enterprise_adoption_velocity,
        
        -- Stickiness metrics
        coalesce(fa.enterprise_stickiness_rate, 0) as enterprise_stickiness_rate,
        coalesce(fa.business_stickiness_rate, 0) as business_stickiness_rate,
        coalesce(fa.starter_stickiness_rate, 0) as starter_stickiness_rate,
        
        -- Feature health and value
        fc.engagement_level,
        coalesce(fa.feature_value_score, 0) as feature_value_score,
        coalesce(fa.strategic_importance, 'experimental') as strategic_importance,
        coalesce(fa.market_fit_segment, 'unknown') as market_fit_segment,
        
        -- Usage timeline
        fc.first_usage_date,
        fc.last_usage_date,
        fc.feature_age_days,
        fc.days_with_usage,
        fc.weeks_with_usage,
        fc.months_with_usage,
        
        -- Recent activity
        fc.used_last_7_days,
        fc.used_last_30_days,
        
        -- Feature maturity
        fc.feature_maturity,
        
        -- Usage frequency scoring
        case 
            when fc.avg_daily_usage > 100 then 'very_high'
            when fc.avg_daily_usage > 50 then 'high'
            when fc.avg_daily_usage > 10 then 'medium'
            when fc.avg_daily_usage > 1 then 'low'
            else 'minimal'
        end as usage_frequency,
        
        -- Customer satisfaction proxy (based on stickiness and adoption)
        case 
            when fa.enterprise_stickiness_rate > 80 and fc.account_adoption_rate > 50 then 4.5
            when fa.enterprise_stickiness_rate > 60 and fc.account_adoption_rate > 30 then 4.0
            when fa.enterprise_stickiness_rate > 40 and fc.account_adoption_rate > 20 then 3.5
            when fa.enterprise_stickiness_rate > 20 and fc.account_adoption_rate > 10 then 3.0
            else 2.5
        end as satisfaction_score,
        
        -- Revenue impact estimation
        case 
            when fa.avg_mrr_adopters > 0 and fc.accounts_using > 0
            then round((fa.avg_mrr_adopters * fc.accounts_using)::numeric, 2)
            else 0
        end as estimated_revenue_impact,
        
        -- Roadmap priority recommendation
        case 
            when fa.strategic_importance = 'critical' and fc.engagement_level = 'highly_engaged' 
            then 'maintain_and_enhance'
            when fa.strategic_importance in ('critical', 'important') and fc.engagement_level in ('engaged', 'moderate')
            then 'optimize_experience'
            when fc.adoption_stage in ('emerging', 'growing') and fa.feature_value_score > 50
            then 'accelerate_adoption'
            when fc.engagement_level in ('declining', 'dormant')
            then 'revamp_or_sunset'
            else 'monitor'
        end as roadmap_recommendation,
        
        -- Feature lifecycle stage
        case 
            when fc.feature_maturity = 'new_feature' then 'introduction'
            when fc.adoption_stage in ('emerging', 'growing') then 'growth'
            when fc.adoption_stage in ('mainstream', 'universal') then 'maturity'
            when fc.engagement_level in ('declining', 'dormant') then 'decline'
            else 'stable'
        end as lifecycle_stage,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from feature_core fc
    left join feature_adoption fa on fc.feature_name = fa.feature_name
)

select * from final