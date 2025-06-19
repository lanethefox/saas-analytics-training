{{ config(
    materialized='table',
    post_hook="ANALYZE {{ this }}"
) }}

-- Mart: Marketing Attribution Analysis
-- Multi-touch attribution analysis across campaigns and customer journeys
-- Primary stakeholders: Marketing team, growth marketing, demand generation
-- Updated to use entity tables and correct column names

with customer_acquisition_base as (
    select
        c.account_id,
        c.account_id as account_key,  -- Use account_id as key
        c.company_name as account_name,
        c.customer_health_score,
        c.monthly_recurring_revenue,
        c.customer_status as subscription_status,
        c.created_at as account_created_at,
        c.days_since_creation as days_since_signup,
        
        -- Customer value metrics
        case 
            when c.monthly_recurring_revenue >= 1000 then 'enterprise'
            when c.monthly_recurring_revenue >= 500 then 'mid_market'
            when c.monthly_recurring_revenue >= 100 then 'small_business'
            else 'starter'
        end as customer_segment,
        
        -- Customer lifecycle stage
        case 
            when c.days_since_creation <= 30 then 'new_customer'
            when c.days_since_creation <= 90 then 'ramping_customer'
            when c.days_since_creation <= 365 then 'established_customer'
            else 'mature_customer'
        end as lifecycle_stage
        
    from {{ ref('entity_customers') }} c
    where c.customer_status in ('active', 'trial')
),

-- Using entity_campaigns for real campaign attribution
campaign_attribution_base as (
    select
        campaign_id,
        campaign_name,
        platform as channel,
        campaign_type,
        total_spend,
        conversions,
        conversion_value as attributed_revenue,
        cost_per_conversion as cost_per_acquisition,
        roi_percentage as roi,
        'multi_touch' as attribution_model,
        campaign_status,
        start_date,
        end_date
    from {{ ref('entity_campaigns') }}
    where campaign_status = 'active'
),

-- Simplified account-campaign mapping using campaign timing
account_campaign_mapping as (
    select
        c.account_id,
        c.created_at as account_created_at,
        camp.campaign_id,
        camp.campaign_name,
        camp.channel,
        camp.cost_per_acquisition,
        camp.roi,
        -- Simple attribution based on account creation timing
        case 
            when c.created_at::date between camp.start_date and camp.end_date then 1.0  -- Full attribution
            when c.created_at::date between camp.end_date and camp.end_date + interval '7 days' then 0.5  -- Partial attribution
            else 0.0
        end as attribution_weight
    from {{ ref('entity_customers') }} c
    cross join campaign_attribution_base camp
    where c.created_at::date >= camp.start_date - interval '30 days'  -- Only consider relevant time windows
),

-- Get primary attribution for each account
primary_attribution as (
    select distinct on (account_id)
        account_id,
        campaign_id,
        campaign_name,
        channel as primary_attribution_channel,
        cost_per_acquisition,
        roi as campaign_roi,
        attribution_weight
    from account_campaign_mapping
    where attribution_weight > 0
    order by account_id, attribution_weight desc, roi desc
),

user_engagement_attribution as (
    select
        u.account_id::varchar as account_id,  -- Cast to match
        count(distinct u.user_id) as total_users,
        count(case when u.user_status = 'active' then u.user_id end) as active_users,
        avg(u.engagement_score) as avg_user_engagement,
        count(case when u.role_type_standardized = 'admin' then u.user_id end) as admin_users,
        count(case when u.role_type_standardized = 'standard_user' then u.user_id end) as standard_users,
        
        -- Engagement quality indicators
        case 
            when avg(u.engagement_score) >= 0.8 then 'high_engagement'
            when avg(u.engagement_score) >= 0.6 then 'medium_engagement'
            when avg(u.engagement_score) >= 0.4 then 'low_engagement'
            else 'minimal_engagement'
        end as engagement_quality
        
    from {{ ref('entity_users') }} u
    group by u.account_id
),

device_adoption_attribution as (
    select
        d.account_id::varchar as account_id,  -- Cast to match
        count(distinct d.device_id) as total_devices,
        count(case when d.device_status = 'active' then d.device_id end) as active_devices,
        avg(d.overall_health_score) as avg_device_health,
        sum(d.total_events_30d) as total_device_events_30d,
        
        -- Device adoption patterns
        case 
            when count(distinct d.device_id) >= 10 then 'high_adoption'
            when count(distinct d.device_id) >= 5 then 'medium_adoption'
            when count(distinct d.device_id) >= 1 then 'low_adoption'
            else 'no_adoption'
        end as device_adoption_level
        
    from {{ ref('entity_devices') }} d
    group by d.account_id
),

location_expansion_attribution as (
    select
        l.account_id::varchar as account_id,  -- Cast to match
        count(distinct l.location_id) as total_locations,
        count(case when l.location_status = 'active' then l.location_id end) as active_locations,
        avg(l.operational_health_score) as avg_location_health,
        count(distinct l.city) as unique_cities,
        count(distinct l.state_code) as unique_states,
        
        -- Geographic expansion indicators
        case 
            when count(distinct l.state_code) > 1 then 'multi_state'
            when count(distinct l.city) > 1 then 'multi_city'
            else 'single_location'
        end as geographic_expansion
        
    from {{ ref('entity_locations') }} l
    group by l.account_id
)

select
    -- Customer identification
    cab.account_id,
    cab.account_key,
    cab.account_name,
    cab.customer_segment,
    cab.lifecycle_stage,
    
    -- Attribution channels
    coalesce(pa.primary_attribution_channel, 'organic') as primary_attribution_channel,
    coalesce(pa.campaign_name, 'Direct/Organic') as campaign_attribution,
    coalesce(pa.campaign_roi, 0) as campaign_roi,
    coalesce(pa.cost_per_acquisition, 0) as acquisition_cost,
    
    -- Customer value metrics
    cab.monthly_recurring_revenue,
    cab.customer_health_score,
    cab.subscription_status,
    cab.account_created_at,
    cab.days_since_signup,
    
    -- Engagement attribution
    coalesce(uea.total_users, 0) as total_users,
    coalesce(uea.active_users, 0) as active_users,
    coalesce(uea.avg_user_engagement, 0) as avg_user_engagement,
    coalesce(uea.engagement_quality, 'no_engagement') as engagement_quality,
    
    -- Product adoption attribution
    coalesce(daa.total_devices, 0) as total_devices,
    coalesce(daa.active_devices, 0) as active_devices,
    coalesce(daa.avg_device_health, 0) as avg_device_health,
    coalesce(daa.device_adoption_level, 'no_adoption') as device_adoption_level,
    coalesce(daa.total_device_events_30d, 0) as total_device_events_30d,
    
    -- Geographic expansion attribution
    coalesce(lea.total_locations, 0) as total_locations,
    coalesce(lea.active_locations, 0) as active_locations,
    coalesce(lea.avg_location_health, 0) as avg_location_health,
    coalesce(lea.geographic_expansion, 'no_locations') as geographic_expansion,
    
    -- Attribution scoring
    case 
        when cab.monthly_recurring_revenue >= 1000 and coalesce(uea.avg_user_engagement, 0) >= 0.7 then 'high_value_attribution'
        when cab.monthly_recurring_revenue >= 500 and coalesce(daa.total_devices, 0) >= 5 then 'medium_value_attribution'
        when cab.monthly_recurring_revenue >= 100 then 'low_value_attribution'
        else 'trial_attribution'
    end as attribution_value_tier,
    
    -- Channel effectiveness indicators
    case 
        when pa.primary_attribution_channel = 'search' and cab.customer_health_score >= 80 then 'high_quality_search'
        when pa.primary_attribution_channel = 'paid_search' and cab.monthly_recurring_revenue >= 500 then 'effective_paid'
        when pa.primary_attribution_channel = 'referral' and coalesce(daa.total_devices, 0) >= 3 then 'strong_referral'
        when pa.primary_attribution_channel = 'social' and coalesce(uea.active_users, 0) >= 5 then 'engaged_social'
        else 'standard_attribution'
    end as channel_quality_indicator,
    
    -- Time-based attribution analysis
    extract(month from cab.account_created_at) as acquisition_month,
    extract(quarter from cab.account_created_at) as acquisition_quarter,
    extract(year from cab.account_created_at) as acquisition_year,
    extract(dow from cab.account_created_at) as acquisition_day_of_week,
    
    -- Customer lifetime value proxies
    cab.monthly_recurring_revenue * 12 as estimated_annual_value,
    cab.monthly_recurring_revenue * case 
        when cab.customer_health_score >= 80 then 24  -- 2 year retention
        when cab.customer_health_score >= 60 then 18  -- 1.5 year retention
        when cab.customer_health_score >= 40 then 12  -- 1 year retention
        else 6  -- 6 month retention
    end as estimated_lifetime_value,
    
    -- ROI calculations
    case 
        when coalesce(pa.cost_per_acquisition, 0) > 0 
        then (cab.monthly_recurring_revenue * 12) / pa.cost_per_acquisition
        else 999  -- No acquisition cost
    end as first_year_roi,
    
    -- Attribution complexity
    case 
        when pa.campaign_id is not null then 'tracked_campaign'
        when cab.account_name ilike '%demo%' then 'demo_conversion'
        else 'organic_conversion'
    end as attribution_type,
    
    -- Metadata
    current_timestamp as attribution_calculated_at
    
from customer_acquisition_base cab
left join primary_attribution pa on cab.account_id = pa.account_id
left join user_engagement_attribution uea on cab.account_id = uea.account_id
left join device_adoption_attribution daa on cab.account_id = daa.account_id
left join location_expansion_attribution lea on cab.account_id = lea.account_id
order by estimated_lifetime_value desc, monthly_recurring_revenue desc