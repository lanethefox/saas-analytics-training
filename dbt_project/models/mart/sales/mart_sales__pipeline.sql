{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Mart: Sales Pipeline & Conversion Analytics
-- Customer acquisition funnel and conversion analytics for sales teams
-- Primary stakeholders: Sales team, revenue operations, business development
-- Updated to use entity tables instead of staging tables

with prospect_base as (
    select
        c.account_id,
        c.account_id as account_key,
        c.company_name as account_name,
        c.customer_tier,  -- Keep original tier for later use
        case 
            when c.customer_tier = 1 then 'enterprise'
            when c.customer_tier = 2 then 'premium'
            when c.customer_tier = 3 then 'professional'
            when c.customer_tier = 4 then 'starter'
            else 'unknown'
        end as account_type,
        c.customer_status as account_status,
        c.created_at as account_created_at,
        
        -- Account characteristics
        c.total_locations,
        case 
            when c.total_locations >= 10 then 'large'
            when c.total_locations >= 5 then 'medium'
            when c.total_locations >= 2 then 'small'
            else 'single_location'
        end as company_size_category,
        
        -- Derive lead source from account creation patterns
        case 
            when c.company_name ilike '%demo%' or c.company_name ilike '%test%' then 'demo_request'
            when extract(hour from c.created_at) between 9 and 17 then 'inbound_lead'
            when extract(dow from c.created_at) in (0, 6) then 'self_signup'
            when c.customer_tier = 1 then 'outbound_sales'  -- enterprise tier
            else 'marketing_qualified'
        end as lead_source,
        
        -- Lead scoring based on account characteristics
        case 
            when c.total_locations >= 10 and c.customer_tier = 1 then 'hot_lead'  -- enterprise tier
            when c.total_locations >= 5 or c.customer_tier in (1, 2) then 'warm_lead'  -- enterprise or premium
            when c.total_locations >= 2 then 'qualified_lead'
            else 'cold_lead'
        end as lead_score
        
    from {{ ref('entity_customers') }} c
),

subscription_conversion as (
    select
        s.account_id,
        s.subscription_id,
        s.subscription_status,
        s.plan_type,
        s.billing_interval as billing_cycle,
        s.monthly_recurring_revenue,
        s.subscription_created_at,
        s.trial_start_date as trial_started_at,
        s.trial_end_date as trial_ended_at,
        
        -- Conversion timing analysis
        s.trial_duration_days,
        
        -- Conversion success indicators
        case 
            when s.subscription_status = 'active' then true
            else false
        end as converted_to_paid,
        
        case 
            when s.subscription_status = 'cancelled' then true
            else false
        end as churned_subscription,
        
        -- Revenue potential
        case 
            when s.monthly_recurring_revenue >= 1000 then 'enterprise_deal'
            when s.monthly_recurring_revenue >= 500 then 'mid_market_deal'
            when s.monthly_recurring_revenue >= 100 then 'smb_deal'
            else 'starter_deal'
        end as deal_size_category
        
    from {{ ref('entity_subscriptions') }} s
),

user_engagement_signals as (
    select
        u.account_id::varchar as account_id,
        count(distinct u.user_id) as total_users_added,
        count(case when u.user_status = 'active' then u.user_id end) as active_users,
        count(case when u.role_type_standardized = 'admin' then u.user_id end) as admin_users,
        avg(u.engagement_score) as avg_engagement_score,
        max(u.user_created_at) as last_user_added_at,
        min(u.user_created_at) as first_user_added_at,
        
        -- User adoption velocity
        case 
            when count(distinct u.user_id) >= 10 then 'rapid_user_adoption'
            when count(distinct u.user_id) >= 5 then 'steady_user_adoption'
            when count(distinct u.user_id) >= 2 then 'slow_user_adoption'
            else 'single_user'
        end as user_adoption_pattern,
        
        -- Engagement health
        case 
            when avg(u.engagement_score) >= 0.8 then 'highly_engaged'
            when avg(u.engagement_score) >= 0.6 then 'moderately_engaged'
            when avg(u.engagement_score) >= 0.4 then 'minimally_engaged'
            else 'disengaged'
        end as engagement_health
        
    from {{ ref('entity_users') }} u
    group by u.account_id
),

device_deployment_signals as (
    select
        d.account_id::varchar as account_id,
        count(distinct d.device_id) as total_devices_deployed,
        count(case when d.device_status = 'active' then d.device_id end) as active_devices,
        count(distinct d.location_id) as locations_with_devices,
        sum(d.total_events_30d) as total_device_activity_30d,
        avg(d.overall_health_score) as avg_device_health,
        max(d.device_created_at) as last_device_deployed_at,
        min(d.device_created_at) as first_device_deployed_at,
        
        -- Deployment velocity
        case 
            when count(distinct d.device_id) >= 10 then 'rapid_deployment'
            when count(distinct d.device_id) >= 5 then 'steady_deployment'
            when count(distinct d.device_id) >= 1 then 'slow_deployment'
            else 'no_deployment'
        end as deployment_velocity,
        
        -- Device health signals
        case 
            when avg(d.overall_health_score) >= 0.8 and sum(d.total_events_30d) >= 1000 then 'healthy_usage'
            when avg(d.overall_health_score) >= 0.6 and sum(d.total_events_30d) >= 500 then 'moderate_usage'
            when sum(d.total_events_30d) > 0 then 'light_usage'
            else 'no_usage'
        end as device_usage_health
        
    from {{ ref('entity_devices') }} d
    group by d.account_id
),

location_expansion_signals as (
    select
        l.account_id::varchar as account_id,
        count(distinct l.location_id) as total_locations,
        count(case when l.location_status = 'active' then l.location_id end) as active_locations,
        count(distinct l.city) as cities_served,
        count(distinct l.state_code) as states_served,
        avg(l.operational_health_score) as avg_location_health,
        
        -- Expansion indicators
        case 
            when count(distinct l.state_code) > 1 then 'multi_state_expansion'
            when count(distinct l.city) > 1 then 'multi_city_expansion'
            when count(distinct l.location_id) > 1 then 'multi_location_expansion'
            else 'single_location'
        end as expansion_pattern
        
    from {{ ref('entity_locations') }} l
    group by l.account_id
)

select
    -- Prospect identification
    pb.account_id,
    pb.account_key,
    pb.account_name,
    pb.account_type,
    pb.account_status,
    pb.lead_source,
    pb.lead_score,
    pb.account_created_at,
    pb.customer_tier,
    
    -- Subscription conversion metrics
    sc.subscription_id,
    sc.subscription_status,
    sc.plan_type,
    sc.billing_cycle,
    sc.monthly_recurring_revenue,
    sc.converted_to_paid,
    sc.churned_subscription,
    sc.deal_size_category,
    sc.trial_duration_days,
    
    -- Engagement signals
    coalesce(ues.total_users_added, 0) as total_users_added,
    coalesce(ues.active_users, 0) as active_users,
    coalesce(ues.admin_users, 0) as admin_users,
    coalesce(ues.avg_engagement_score, 0) as avg_engagement_score,
    coalesce(ues.user_adoption_pattern, 'no_users') as user_adoption_pattern,
    coalesce(ues.engagement_health, 'no_engagement') as engagement_health,
    
    -- Product adoption signals
    coalesce(dds.total_devices_deployed, 0) as total_devices_deployed,
    coalesce(dds.active_devices, 0) as active_devices,
    coalesce(dds.total_device_activity_30d, 0) as total_device_activity_30d,
    coalesce(dds.deployment_velocity, 'no_deployment') as deployment_velocity,
    coalesce(dds.device_usage_health, 'no_usage') as device_usage_health,
    
    -- Market expansion signals
    coalesce(les.total_locations, pb.total_locations) as total_locations,
    coalesce(les.active_locations, 0) as active_locations,
    coalesce(les.cities_served, 0) as cities_served,
    coalesce(les.states_served, 0) as states_served,
    coalesce(les.expansion_pattern, 'no_expansion') as expansion_pattern,
    
    -- Sales pipeline stage classification
    case 
        when sc.subscription_status = 'active' and sc.monthly_recurring_revenue > 0 then 'closed_won'
        when sc.subscription_status = 'cancelled' then 'closed_lost'
        when sc.subscription_status = 'trial' and coalesce(dds.total_devices_deployed, 0) > 0 then 'trial_active_usage'
        when sc.subscription_status = 'trial' then 'trial_limited_usage'
        when pb.lead_score = 'hot_lead' and coalesce(ues.total_users_added, 0) > 0 then 'qualified_opportunity'
        when coalesce(ues.total_users_added, 0) > 0 then 'marketing_qualified_lead'
        else 'prospect'
    end as pipeline_stage,
    
    -- Conversion probability scoring
    case 
        when pb.lead_score = 'hot_lead' and coalesce(ues.avg_engagement_score, 0) >= 0.7 and coalesce(dds.total_devices_deployed, 0) >= 3 then 0.85
        when pb.lead_score in ('hot_lead', 'warm_lead') and coalesce(dds.total_devices_deployed, 0) >= 1 then 0.65
        when pb.lead_score = 'qualified_lead' and coalesce(ues.active_users, 0) >= 2 then 0.45
        when coalesce(ues.total_users_added, 0) > 0 then 0.25
        else 0.10
    end as conversion_probability,
    
    -- Time to conversion analysis
    case 
        when sc.subscription_created_at is not null and pb.account_created_at is not null 
        then (sc.subscription_created_at::date - pb.account_created_at::date)
        else null
    end as days_to_conversion,
    
    -- Deal velocity indicators
    case 
        when sc.converted_to_paid and (sc.subscription_created_at::date - pb.account_created_at::date) <= 7 then 'fast_conversion'
        when sc.converted_to_paid and (sc.subscription_created_at::date - pb.account_created_at::date) <= 30 then 'normal_conversion'
        when sc.converted_to_paid then 'slow_conversion'
        when (current_date - pb.account_created_at::date) > 90 then 'stalled_opportunity'
        else 'active_opportunity'
    end as deal_velocity,
    
    -- Revenue potential calculation
    case 
        when sc.converted_to_paid then sc.monthly_recurring_revenue * 12
        when pb.lead_score = 'hot_lead' then 1000  -- Estimated ARR for hot leads
        when pb.lead_score = 'warm_lead' then 600  -- Estimated ARR for warm leads
        when pb.lead_score = 'qualified_lead' then 300  -- Estimated ARR for qualified leads
        else 100  -- Estimated ARR for cold leads
    end as estimated_annual_revenue,
    
    -- Sales team assignment simulation
    case 
        when pb.customer_tier = 1 or coalesce(sc.monthly_recurring_revenue, 0) >= 1000 then 'enterprise_sales'
        when pb.lead_score = 'hot_lead' or coalesce(sc.monthly_recurring_revenue, 0) >= 500 then 'senior_sales'
        when coalesce(ues.total_users_added, 0) >= 3 or coalesce(dds.total_devices_deployed, 0) >= 2 then 'mid_market_sales'
        else 'inside_sales'
    end as sales_owner_segment,
    
    -- Account scoring for prioritization
    (
        case when pb.lead_score = 'hot_lead' then 40
             when pb.lead_score = 'warm_lead' then 30
             when pb.lead_score = 'qualified_lead' then 20
             else 10 end +
        case when coalesce(ues.avg_engagement_score, 0) >= 0.8 then 30
             when coalesce(ues.avg_engagement_score, 0) >= 0.6 then 20
             when coalesce(ues.avg_engagement_score, 0) >= 0.4 then 10
             else 0 end +
        case when coalesce(dds.total_devices_deployed, 0) >= 5 then 20
             when coalesce(dds.total_devices_deployed, 0) >= 1 then 10
             else 0 end +
        case when coalesce(les.total_locations, 0) >= 5 then 10
             when coalesce(les.total_locations, 0) >= 2 then 5
             else 0 end
    ) as account_priority_score,
    
    -- Metadata
    current_timestamp as pipeline_analyzed_at
    
from prospect_base pb
left join subscription_conversion sc on pb.account_id = sc.account_id
left join user_engagement_signals ues on pb.account_id = ues.account_id
left join device_deployment_signals dds on pb.account_id = dds.account_id
left join location_expansion_signals les on pb.account_id = les.account_id
order by account_priority_score desc, estimated_annual_revenue desc