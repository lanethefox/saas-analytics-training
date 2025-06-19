{{ config(materialized='table') }}

-- Intermediate model: Feature adoption patterns
-- Tracks feature adoption journeys by customer segment
-- Analyzes correlation between feature usage and customer value

with feature_usage as (
    select * from {{ ref('stg_app_database__feature_usage') }}
),

customers as (
    select * from {{ ref('int_customers__core') }}
),

subscriptions as (
    select * from {{ ref('stg_app_database__subscriptions') }}
),

-- Feature adoption timeline by account
account_feature_timeline as (
    select
        f.account_id,
        f.feature_name,
        f.feature_category,
        min(f.usage_timestamp) as first_usage,
        max(f.usage_timestamp) as last_usage,
        count(*) as usage_count,
        count(distinct f.user_id) as users_adopted,
        count(distinct date_trunc('day', f.usage_timestamp)) as days_used,
        
        -- Calculate adoption order
        row_number() over (
            partition by f.account_id 
            order by min(f.usage_timestamp)
        ) as feature_adoption_order
        
    from feature_usage f
    group by 1, 2, 3
),

-- Enhance with customer information
feature_customer_adoption as (
    select
        aft.*,
        c.customer_lifecycle_stage,
        c.plan_type,
        c.company_size_category,
        c.monthly_recurring_revenue,
        c.subscription_health_score,
        
        -- Days from account creation to feature adoption
        extract(days from aft.first_usage - c.subscription_started_at) as days_to_adoption,
        
        -- Feature stickiness (still using after 30 days)
        case 
            when aft.last_usage >= aft.first_usage + interval '30 days' then true
            else false
        end as is_sticky_feature
        
    from account_feature_timeline aft
    join customers c on aft.account_id = c.account_id
),

-- Calculate feature value correlation
feature_value_analysis as (
    select
        feature_name,
        feature_category,
        
        -- Adoption by customer segment
        count(distinct case when plan_type = 'enterprise' then account_id end) as enterprise_adopters,
        count(distinct case when plan_type = 'business' then account_id end) as business_adopters,
        count(distinct case when plan_type = 'starter' then account_id end) as starter_adopters,
        
        -- Average MRR by adoption
        avg(case when usage_count > 0 then monthly_recurring_revenue end) as avg_mrr_adopters,
        
        -- Adoption speed by segment
        avg(case when plan_type = 'enterprise' then days_to_adoption end) as avg_days_to_adoption_enterprise,
        avg(case when plan_type = 'business' then days_to_adoption end) as avg_days_to_adoption_business,
        avg(case when plan_type = 'starter' then days_to_adoption end) as avg_days_to_adoption_starter,
        
        -- Stickiness by segment
        sum(case when is_sticky_feature and plan_type = 'enterprise' then 1 else 0 end)::float / 
            nullif(count(case when plan_type = 'enterprise' then 1 end), 0) * 100 as enterprise_stickiness_rate,
        sum(case when is_sticky_feature and plan_type = 'business' then 1 else 0 end)::float / 
            nullif(count(case when plan_type = 'business' then 1 end), 0) * 100 as business_stickiness_rate,
        sum(case when is_sticky_feature and plan_type = 'starter' then 1 else 0 end)::float / 
            nullif(count(case when plan_type = 'starter' then 1 end), 0) * 100 as starter_stickiness_rate
        
    from feature_customer_adoption
    group by 1, 2
),

-- Common feature adoption paths
adoption_paths as (
    select
        account_id,
        string_agg(
            feature_name, 
            ' -> ' 
            order by feature_adoption_order
        ) as adoption_path,
        count(*) as path_length,
        max(monthly_recurring_revenue) as account_mrr
    from feature_customer_adoption
    where feature_adoption_order <= 5  -- First 5 features only
    group by 1
),

-- Popular adoption paths by value
popular_paths as (
    select
        adoption_path,
        count(*) as accounts_on_path,
        avg(account_mrr) as avg_mrr_on_path,
        percentile_cont(0.5) within group (order by account_mrr) as median_mrr_on_path
    from adoption_paths
    group by 1
    having count(*) >= 5  -- Minimum accounts for significance
),

final as (
    select
        fva.*,
        
        -- Feature value score (0-100)
        -- Based on enterprise adoption, MRR correlation, and stickiness
        (
            -- Enterprise adoption weight (40%)
            case 
                when fva.enterprise_adopters > 0 then 
                    least(fva.enterprise_adopters::float / 10 * 40, 40)
                else 0
            end +
            
            -- MRR correlation weight (40%)
            case 
                when fva.avg_mrr_adopters > 500 then 40
                when fva.avg_mrr_adopters > 200 then 30
                when fva.avg_mrr_adopters > 100 then 20
                when fva.avg_mrr_adopters > 0 then 10
                else 0
            end +
            
            -- Stickiness weight (20%)
            case 
                when fva.enterprise_stickiness_rate > 80 then 20
                when fva.enterprise_stickiness_rate > 60 then 15
                when fva.enterprise_stickiness_rate > 40 then 10
                when fva.enterprise_stickiness_rate > 20 then 5
                else 0
            end
        ) as feature_value_score,
        
        -- Adoption velocity classification
        case 
            when fva.avg_days_to_adoption_enterprise <= 7 then 'immediate'
            when fva.avg_days_to_adoption_enterprise <= 30 then 'quick'
            when fva.avg_days_to_adoption_enterprise <= 90 then 'gradual'
            else 'slow'
        end as enterprise_adoption_velocity,
        
        -- Market fit indicator
        case 
            when fva.enterprise_adopters > fva.starter_adopters * 2 then 'enterprise_focused'
            when fva.starter_adopters > fva.enterprise_adopters * 2 then 'starter_focused'
            else 'balanced'
        end as market_fit_segment,
        
        -- Strategic importance
        case 
            when fva.enterprise_stickiness_rate > 70 and fva.avg_mrr_adopters > 300 then 'critical'
            when fva.enterprise_stickiness_rate > 50 and fva.avg_mrr_adopters > 200 then 'important'
            when fva.enterprise_adopters > 0 or fva.business_adopters > 10 then 'valuable'
            else 'experimental'
        end as strategic_importance,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from feature_value_analysis fva
)

select * from final