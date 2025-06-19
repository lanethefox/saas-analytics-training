{{
    config(
        materialized = 'incremental',
        unique_key = ['feature_id', 'valid_from'],
        on_schema_change = 'fail'
    )
}}

with feature_snapshots as (
    select
        feature_id,
        feature_name,
        feature_category,
        feature_type,
        feature_description,
        feature_status,
        release_version,
        release_date,
        deprecation_date,
        is_beta,
        is_premium,
        is_active,
        required_subscription_tier,
        usage_limit,
        total_users,
        active_users_last_30d,
        total_usage_count,
        adoption_rate,
        retention_rate,
        average_usage_per_user,
        created_at,
        updated_at,
        _synced_at,
        
        -- Create validity window
        updated_at as valid_from,
        lead(updated_at, 1, '9999-12-31'::timestamp) over (
            partition by feature_id 
            order by updated_at
        ) as valid_to,
        
        -- Track what changed
        lag(feature_status) over (partition by feature_id order by updated_at) as prev_feature_status,
        lag(is_beta) over (partition by feature_id order by updated_at) as prev_is_beta,
        lag(is_premium) over (partition by feature_id order by updated_at) as prev_is_premium,
        lag(is_active) over (partition by feature_id order by updated_at) as prev_is_active,
        lag(required_subscription_tier) over (partition by feature_id order by updated_at) as prev_required_subscription_tier,
        lag(usage_limit) over (partition by feature_id order by updated_at) as prev_usage_limit,
        lag(total_users) over (partition by feature_id order by updated_at) as prev_total_users,
        lag(adoption_rate) over (partition by feature_id order by updated_at) as prev_adoption_rate
        
    from {{ ref('entity_features') }}
    
    {% if is_incremental() %}
    where updated_at > (select max(valid_from) from {{ this }})
    {% endif %}
),

feature_history as (
    select
        feature_id,
        feature_name,
        feature_category,
        feature_type,
        feature_description,
        feature_status,
        release_version,
        release_date,
        deprecation_date,
        is_beta,
        is_premium,
        is_active,
        required_subscription_tier,
        usage_limit,
        total_users,
        active_users_last_30d,
        total_usage_count,
        adoption_rate,
        retention_rate,
        average_usage_per_user,
        created_at,
        updated_at,
        valid_from,
        valid_to,
        
        -- Change tracking flags
        case when feature_status != prev_feature_status then true else false end as status_changed,
        case when is_beta != prev_is_beta then true else false end as beta_status_changed,
        case when is_premium != prev_is_premium then true else false end as premium_status_changed,
        case when is_active != prev_is_active then true else false end as active_status_changed,
        case when required_subscription_tier != prev_required_subscription_tier then true else false end as tier_requirement_changed,
        case when usage_limit != prev_usage_limit then true else false end as usage_limit_changed,
        
        -- Growth metrics
        total_users - coalesce(prev_total_users, 0) as user_growth,
        case 
            when prev_total_users > 0 then ((total_users - prev_total_users)::float / prev_total_users) * 100 
            else null 
        end as user_growth_percentage,
        adoption_rate - coalesce(prev_adoption_rate, 0) as adoption_rate_change,
        
        -- Change summary
        case
            when prev_feature_status is null then 'Initial Record'
            when feature_status != prev_feature_status then 'Status Change: ' || prev_feature_status || ' → ' || feature_status
            when is_beta = false and prev_is_beta = true then 'Released from Beta'
            when is_premium = true and prev_is_premium = false then 'Moved to Premium'
            when is_premium = false and prev_is_premium = true then 'Moved to Free'
            when required_subscription_tier != prev_required_subscription_tier then 'Tier Change: ' || prev_required_subscription_tier || ' → ' || required_subscription_tier
            when usage_limit != prev_usage_limit then 'Usage Limit Change: ' || prev_usage_limit || ' → ' || usage_limit
            when is_active != prev_is_active then case when is_active then 'Activated' else 'Deactivated' end
            when (total_users - coalesce(prev_total_users, 0)) > 100 then 'User Growth: +' || (total_users - coalesce(prev_total_users, 0))
            when (adoption_rate - coalesce(prev_adoption_rate, 0)) > 0.05 then 'Adoption Surge: +' || round((adoption_rate - coalesce(prev_adoption_rate, 0)) * 100, 1) || '%'
            else 'Metrics Update'
        end as change_type,
        
        -- Feature lifecycle stage
        case
            when feature_status = 'deprecated' then 'Deprecated'
            when is_beta then 'Beta'
            when datediff('day', release_date, current_date()) <= 30 then 'Recently Released'
            when datediff('day', release_date, current_date()) <= 90 then 'New'
            when adoption_rate >= 0.5 then 'Mature'
            when adoption_rate >= 0.2 then 'Growing'
            else 'Low Adoption'
        end as lifecycle_stage,
        
        -- Record metadata
        row_number() over (partition by feature_id order by valid_from) as version_number,
        case when valid_to = '9999-12-31'::timestamp then true else false end as is_current,
        _synced_at
        
    from feature_snapshots
)

select * from feature_history