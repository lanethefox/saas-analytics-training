{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Mart: Product Adoption & Feature Analytics
-- Feature adoption analytics for product teams using feature-level data
-- Primary stakeholders: Product team, UX/UI design, product marketing

with feature_summary as (
    select
        ef.*,
        
        -- Feature maturity classification
        case 
            when ef.feature_age_days <= 30 then 'new_feature'
            when ef.feature_age_days <= 90 then 'recent_feature'
            when ef.feature_age_days <= 365 then 'established_feature'
            else 'mature_feature'
        end as feature_age_category,
        
        -- Adoption velocity
        case 
            when ef.enterprise_adoption_velocity = 'rapid' then 3
            when ef.enterprise_adoption_velocity = 'moderate' then 2
            when ef.enterprise_adoption_velocity = 'slow' then 1
            else 0
        end as adoption_velocity_score,
        
        -- Value classification
        case 
            when ef.feature_value_score >= 80 then 'high_value_feature'
            when ef.feature_value_score >= 60 then 'medium_value_feature'
            when ef.feature_value_score >= 40 then 'low_value_feature'
            else 'minimal_value_feature'
        end as value_classification
        
    from {{ ref('entity_features') }} ef
),

customer_feature_adoption as (
    select
        c.account_id,
        c.account_id as account_key,  -- Use account_id as key
        c.company_name as account_name,
        c.customer_tier,
        c.customer_status as subscription_status,
        c.monthly_recurring_revenue,
        c.customer_health_score,
        c.days_since_creation as days_since_signup,
        c.total_users,
        c.active_users_30d,
        
        -- Customer classification
        case 
            when c.monthly_recurring_revenue >= 1000 then 'enterprise'
            when c.monthly_recurring_revenue >= 500 then 'mid_market'
            when c.monthly_recurring_revenue >= 100 then 'small_business'
            else 'starter'
        end as customer_segment,
        
        case 
            when c.days_since_creation <= 30 then 'new_customer'
            when c.days_since_creation <= 90 then 'ramping_customer'
            when c.days_since_creation <= 365 then 'established_customer'
            else 'mature_customer'
        end as customer_lifecycle,
        
        -- Feature adoption aggregates by tier
        count(distinct case when fs.adoption_stage != 'not_adopted' then fs.feature_name end) as features_adopted,
        count(distinct case when fs.feature_category = 'core' then fs.feature_name end) as core_features_adopted,
        count(distinct case when fs.feature_category = 'advanced' then fs.feature_name end) as advanced_features_adopted,
        count(distinct case when fs.feature_category = 'analytics' then fs.feature_name end) as analytics_features_adopted,
        count(distinct case when fs.feature_category = 'integration' then fs.feature_name end) as integration_features_adopted,
        
        -- Average stickiness by tier
        avg(case 
            when c.customer_tier = 3 then fs.enterprise_stickiness_rate  -- 3 = enterprise
            when c.customer_tier = 2 then fs.business_stickiness_rate    -- 2 = business
            when c.customer_tier = 1 then fs.starter_stickiness_rate     -- 1 = starter
            else 0
        end) as avg_feature_stickiness,
        
        -- High value feature adoption
        count(distinct case when fs.value_classification = 'high_value_feature' and fs.adoption_stage != 'not_adopted' then fs.feature_name end) as high_value_features_adopted,
        
        -- Strategic features
        count(distinct case when fs.strategic_importance = 'critical' and fs.adoption_stage != 'not_adopted' then fs.feature_name end) as critical_features_adopted
        
    from {{ ref('entity_customers') }} c
    cross join feature_summary fs
    group by 
        c.account_id, c.company_name, c.customer_tier,
        c.customer_status, c.monthly_recurring_revenue,
        c.customer_health_score, c.days_since_creation,
        c.total_users, c.active_users_30d
),

feature_adoption_analysis as (
    select
        cfa.*,
        
        -- Adoption depth classification
        case 
            when cfa.features_adopted >= 15 and cfa.advanced_features_adopted >= 3 then 'power_adopter'
            when cfa.features_adopted >= 10 and cfa.analytics_features_adopted >= 2 then 'advanced_adopter'
            when cfa.features_adopted >= 5 then 'moderate_adopter'
            when cfa.features_adopted >= 1 then 'light_adopter'
            else 'non_adopter'
        end as adoption_tier,
        
        -- Feature breadth analysis
        case 
            when cfa.advanced_features_adopted >= 2 and cfa.analytics_features_adopted >= 2 then 'deep_feature_usage'
            when cfa.analytics_features_adopted >= 3 then 'analytical_focus'
            when cfa.integration_features_adopted >= 2 then 'integration_focus'
            when cfa.core_features_adopted >= 5 then 'broad_core_usage'
            else 'minimal_usage'
        end as feature_usage_pattern,
        
        -- Product-market fit score
        case 
            when cfa.avg_feature_stickiness >= 80 and cfa.features_adopted >= 10 then 'excellent_fit'
            when cfa.avg_feature_stickiness >= 60 and cfa.features_adopted >= 7 then 'good_fit'
            when cfa.avg_feature_stickiness >= 40 and cfa.features_adopted >= 5 then 'moderate_fit'
            when cfa.features_adopted >= 1 then 'poor_fit'
            else 'no_fit'
        end as product_market_fit,
        
        -- Expansion potential
        case 
            when cfa.customer_tier = 1 and cfa.advanced_features_adopted >= 1 then 'high_expansion_potential'
            when cfa.customer_tier = 2 and cfa.analytics_features_adopted >= 2 then 'high_expansion_potential'
            when cfa.features_adopted >= 10 and cfa.customer_segment in ('starter', 'small_business') then 'medium_expansion_potential'
            when cfa.features_adopted >= 5 then 'low_expansion_potential'
            else 'no_expansion_potential'
        end as expansion_opportunity,
        
        -- User engagement proxy
        case 
            when cfa.active_users_30d::numeric / nullif(cfa.total_users, 0) >= 0.8 then 'high_user_engagement'
            when cfa.active_users_30d::numeric / nullif(cfa.total_users, 0) >= 0.6 then 'medium_user_engagement'
            when cfa.active_users_30d::numeric / nullif(cfa.total_users, 0) >= 0.4 then 'low_user_engagement'
            else 'minimal_user_engagement'
        end as user_engagement_level
        
    from customer_feature_adoption cfa
),

product_adoption_final as (
    select
        faa.*,
        
        -- Feature adoption score (0-100)
        (
            (faa.features_adopted::numeric / 20.0 * 30) +  -- Max 20 features expected
            (faa.avg_feature_stickiness / 100.0 * 30) +
            (faa.high_value_features_adopted::numeric / 5.0 * 20) +  -- Max 5 high value features
            (faa.critical_features_adopted::numeric / 3.0 * 20)  -- Max 3 critical features
        ) as feature_adoption_score,
        
        -- Product recommendations
        case 
            when faa.adoption_tier = 'non_adopter' then 'focus_on_onboarding'
            when faa.adoption_tier = 'light_adopter' and faa.user_engagement_level = 'minimal_user_engagement' then 'improve_user_activation'
            when faa.adoption_tier = 'light_adopter' then 'promote_feature_discovery'
            when faa.avg_feature_stickiness < 50 then 'improve_feature_experience'
            when faa.advanced_features_adopted = 0 then 'introduce_advanced_features'
            when faa.expansion_opportunity = 'high_expansion_potential' then 'upsell_opportunity'
            else 'maintain_engagement'
        end as product_recommendation,
        
        -- Customer success alignment
        case 
            when faa.adoption_tier in ('power_adopter', 'advanced_adopter') and faa.customer_health_score >= 80 then 'product_driving_success'
            when faa.adoption_tier in ('moderate_adopter') and faa.customer_health_score >= 60 then 'product_supporting_success'
            when faa.adoption_tier in ('light_adopter', 'non_adopter') and faa.customer_health_score < 60 then 'product_hindering_success'
            else 'product_neutral_impact'
        end as product_success_impact,
        
        -- Metadata
        current_timestamp as adoption_analyzed_at
        
    from feature_adoption_analysis faa
    where faa.subscription_status in ('active', 'trial')
)

select * from product_adoption_final
order by 
    case adoption_tier
        when 'power_adopter' then 1
        when 'advanced_adopter' then 2
        when 'moderate_adopter' then 3
        when 'light_adopter' then 4
        else 5
    end,
    feature_adoption_score desc,
    monthly_recurring_revenue desc