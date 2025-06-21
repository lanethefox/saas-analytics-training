{{
    config(
        materialized = 'table'
    )
}}

-- Intermediate model: Feature adoption metrics
-- Comprehensive feature adoption and user onboarding analytics
-- Updated to match aligned staging schema

with feature_usage as (
    select * from {{ ref('stg_app_database__feature_usage') }}
),

users as (
    select * from {{ ref('stg_app_database__users') }}
),

accounts as (
    select * from {{ ref('stg_app_database__accounts') }}
),

-- Get unique features (using available columns)
features as (
    select distinct
        feature_name,
        feature_category
    from feature_usage
),

-- Calculate feature usage by user
feature_user_stats as (
    select
        feature_name,
        user_id,
        min(feature_used_at) as first_usage_date, -- Fixed column name
        max(feature_used_at) as last_usage_date, -- Fixed column name
        count(distinct date(feature_used_at)) as days_used, -- Fixed column name
        count(*) as total_usage_count, -- Using count instead of sum
        sum(usage_duration_seconds) as total_usage_duration_seconds
    from feature_usage
    group by 1, 2
),

-- Adoption cohorts (users who first used feature in each month)
feature_adoption_cohorts as (
    select
        feature_name,
        date_trunc('month', first_usage_date) as cohort_month,
        count(distinct user_id) as new_adopters,
        count(distinct case 
            when first_usage_date >= current_date - 30 then user_id 
        end) as new_adopters_last_30d
    from feature_user_stats
    group by 1, 2
),

-- Current period metrics
feature_current_metrics as (
    select
        f.feature_name,
        f.feature_category,
        
        -- Overall adoption
        count(distinct fus.user_id) as total_adopters,
        count(distinct case 
            when fus.user_id is not null then fus.user_id 
        end) as feature_users,
        
        -- Recent activity
        count(distinct case 
            when fus.last_usage_date >= current_date - 30 then fus.user_id 
        end) as active_users_30d,
        count(distinct case 
            when fus.last_usage_date >= current_date - 7 then fus.user_id 
        end) as active_users_7d,
        
        -- Engagement metrics
        avg(fus.total_usage_count) as avg_usage_count_per_user,
        avg(fus.total_usage_duration_seconds) as avg_duration_per_user,
        avg(fus.days_used) as avg_days_used_per_user,
        
        -- Temporal patterns
        min(fus.first_usage_date) as feature_launch_date,
        max(fus.last_usage_date) as last_feature_usage
        
    from features f
    left join feature_user_stats fus on f.feature_name = fus.feature_name
    group by f.feature_name, f.feature_category
),

-- Total platform users for adoption rate calculation
platform_stats as (
    select count(distinct user_id) as total_platform_users
    from users
),

final as (
    select
        fcm.feature_name,
        fcm.feature_category,
        
        -- Adoption metrics
        fcm.total_adopters,
        ps.total_platform_users,
        case 
            when ps.total_platform_users > 0
            then fcm.total_adopters::numeric / ps.total_platform_users
            else 0
        end as adoption_rate,
        
        -- Activity metrics
        fcm.active_users_30d,
        fcm.active_users_7d,
        case 
            when fcm.total_adopters > 0
            then fcm.active_users_30d::numeric / fcm.total_adopters
            else 0
        end as retention_rate_30d,
        
        case 
            when fcm.active_users_30d > 0
            then fcm.active_users_7d::numeric / fcm.active_users_30d
            else 0
        end as weekly_engagement_rate,
        
        -- Usage depth metrics
        coalesce(fcm.avg_usage_count_per_user, 0) as avg_usage_count_per_user,
        coalesce(fcm.avg_duration_per_user, 0) as avg_duration_per_user,
        coalesce(fcm.avg_days_used_per_user, 0) as avg_days_used_per_user,
        
        -- Temporal information
        fcm.feature_launch_date,
        fcm.last_feature_usage,
        case 
            when fcm.feature_launch_date is not null
            then (current_date - fcm.feature_launch_date::date)
            else null
        end as feature_age_days,
        
        -- Feature maturity and health
        case 
            when (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.5 then 'core_feature'
            when (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.2 then 'popular_feature'
            when (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.05 then 'niche_feature'
            when fcm.total_adopters > 0 then 'experimental_feature'
            else 'unused_feature'
        end as adoption_tier,
        
        case 
            when fcm.retention_rate_30d >= 0.8 then 'sticky'
            when fcm.retention_rate_30d >= 0.6 then 'engaging'
            when fcm.retention_rate_30d >= 0.3 then 'moderate'
            when fcm.total_adopters > 0 then 'low_retention'
            else 'no_retention'
        end as retention_tier,
        
        case 
            when fcm.avg_usage_count_per_user >= 10 then 'heavy_usage'
            when fcm.avg_usage_count_per_user >= 5 then 'regular_usage'
            when fcm.avg_usage_count_per_user >= 2 then 'light_usage'
            when fcm.total_adopters > 0 then 'minimal_usage'
            else 'no_usage'
        end as usage_intensity,
        
        -- Growth assessment
        case 
            when extract(days from (current_date - fcm.feature_launch_date::date)) <= 30 
            then 'new_feature'
            when fcm.active_users_7d > fcm.active_users_30d * 0.5
            then 'growing'
            when fcm.retention_rate_30d >= 0.6 and fcm.adoption_rate >= 0.2
            then 'established'
            when fcm.total_adopters > 0
            then 'stable'
            else 'declining'
        end as growth_stage,
        
        -- Business value scoring
        case 
            when fcm.feature_category = 'core' and (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.8 then 0.95
            when fcm.feature_category = 'core' and (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.5 then 0.85
            when fcm.feature_category = 'analytics' and (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.3 then 0.75
            when fcm.feature_category = 'device' and (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.4 then 0.80
            when (case when ps.total_platform_users > 0 then fcm.total_adopters::numeric / ps.total_platform_users else 0 end) >= 0.1 and (case when fcm.total_adopters > 0 then fcm.active_users_30d::numeric / fcm.total_adopters else 0 end) >= 0.6 then 0.65
            when fcm.total_adopters > 0 then 0.40
            else 0.10
        end as business_value_score,
        
        -- Recent adoption trend
        coalesce(fac.new_adopters_last_30d, 0) as new_adopters_last_30d,
        case 
            when fcm.total_adopters > 0
            then coalesce(fac.new_adopters_last_30d, 0)::numeric / fcm.total_adopters
            else 0
        end as recent_adoption_rate,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from feature_current_metrics fcm
    cross join platform_stats ps
    left join (
        select 
            feature_name,
            sum(new_adopters_last_30d) as new_adopters_last_30d
        from feature_adoption_cohorts 
        group by feature_name
    ) fac on fcm.feature_name = fac.feature_name
)

select * from final