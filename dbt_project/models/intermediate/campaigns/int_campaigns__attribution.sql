{{ config(materialized='table') }}

-- Intermediate model: Campaign attribution and lead journey
-- Links marketing touchpoints to conversions with multi-touch attribution modeling
-- Implements various attribution models for comprehensive campaign analysis

with touchpoints as (
    select * from {{ ref('stg_marketing__attribution_touchpoints') }}
),

leads as (
    select * from {{ ref('stg_marketing__marketing_qualified_leads') }}
),

campaigns as (
    select * from {{ ref('int_campaigns__core') }}
),

-- Calculate attribution windows and touchpoint sequences
touchpoint_sequences as (
    select
        t.touchpoint_id,
        t.lead_id,
        t.campaign_id,
        t.channel,
        t.touchpoint_type,
        t.attribution_weight,
        t.campaign_name,
        t.medium,
        t.source,
        t.content,
        t.touchpoint_position,
        t.position_in_journey,
        t.interaction_details,
        t.touchpoint_timestamp,
        t.created_at,
        t.normalized_attribution_weight,
        t.channel_group,
        t.attribution_model_type,
        t.data_quality_flag,
        t._dbt_inserted_at,
        l.lead_source,
        'qualified' as lead_status,  -- Default status since column doesn't exist
        l.lead_score,
        l.mql_date as conversion_date,  -- Using MQL date as conversion date
        case when l.account_id is not null then true else false end as is_converted,  -- Proxy for conversion
        l.account_id as converted_account_id,
        l.days_to_mql as days_to_conversion,  -- Using days_to_mql instead
        
        -- Calculate days between touchpoint and conversion
        case 
            when l.mql_date is not null then 
                extract(epoch from (l.mql_date - t.touchpoint_timestamp)) / 86400
            else null
        end as days_before_conversion,
        
        -- Sequence numbers for attribution modeling
        row_number() over (
            partition by t.lead_id 
            order by t.touchpoint_timestamp
        ) as touchpoint_sequence,
        
        count(*) over (
            partition by t.lead_id
        ) as total_touchpoints,
        
        -- First and last touch indicators
        row_number() over (
            partition by t.lead_id 
            order by t.touchpoint_timestamp
        ) = 1 as is_first_touch,
        
        row_number() over (
            partition by t.lead_id 
            order by t.touchpoint_timestamp desc
        ) = 1 as is_last_touch
        
    from touchpoints t
    left join leads l on t.lead_id = l.lead_id
    where t.touchpoint_timestamp <= coalesce(l.mql_date, current_timestamp)
),

-- Apply different attribution models
attribution_models as (
    select
        ts.touchpoint_id,
        ts.lead_id,
        ts.campaign_id,
        ts.channel,
        ts.touchpoint_type,
        ts.attribution_weight,
        ts.medium,
        ts.source,
        ts.content,
        ts.touchpoint_position,
        ts.position_in_journey,
        ts.interaction_details,
        ts.touchpoint_timestamp,
        ts.created_at,
        ts.normalized_attribution_weight,
        ts.channel_group,
        ts.attribution_model_type,
        ts.data_quality_flag,
        ts._dbt_inserted_at,
        ts.lead_source,
        ts.lead_status,
        ts.lead_score,
        ts.conversion_date,
        ts.is_converted,
        ts.converted_account_id,
        ts.days_to_conversion,
        ts.days_before_conversion,
        ts.touchpoint_sequence,
        ts.total_touchpoints,
        ts.is_first_touch,
        ts.is_last_touch,
        c.campaign_key,
        c.platform,
        c.campaign_name,
        c.total_spend,
        
        -- First Touch Attribution
        case when is_first_touch then 1.0 else 0 end as first_touch_credit,
        
        -- Last Touch Attribution
        case when is_last_touch then 1.0 else 0 end as last_touch_credit,
        
        -- Linear Attribution (equal credit to all touchpoints)
        1.0 / nullif(total_touchpoints, 0) as linear_credit,
        
        -- Time Decay Attribution (more credit to recent touchpoints)
        case 
            when days_before_conversion is not null then
                exp(-0.1 * days_before_conversion) / 
                sum(exp(-0.1 * days_before_conversion)) over (partition by lead_id)
            else 0
        end as time_decay_credit,
        
        -- Position Based Attribution (40% first, 40% last, 20% middle)
        case 
            when is_first_touch then 0.4
            when is_last_touch then 0.4
            when total_touchpoints > 2 then 0.2 / (total_touchpoints - 2)
            else 0
        end as position_based_credit
        
    from touchpoint_sequences ts
    left join campaigns c on ts.campaign_id = c.campaign_id
),

-- Aggregate attribution by campaign
campaign_attribution as (
    select
        campaign_key,
        campaign_id,
        platform,
        campaign_name,
        total_spend,
        
        -- Lead counts
        count(distinct lead_id) as total_leads_touched,
        count(distinct case when is_converted then lead_id end) as converted_leads,
        
        -- Attribution credits by model
        sum(case when is_converted then first_touch_credit else 0 end) as first_touch_conversions,
        sum(case when is_converted then last_touch_credit else 0 end) as last_touch_conversions,
        sum(case when is_converted then linear_credit else 0 end) as linear_conversions,
        sum(case when is_converted then time_decay_credit else 0 end) as time_decay_conversions,
        sum(case when is_converted then position_based_credit else 0 end) as position_based_conversions,
        
        -- Average touchpoints per lead
        avg(total_touchpoints) as avg_touchpoints_per_lead,
        
        -- Touchpoint distribution
        sum(case when is_first_touch then 1 else 0 end) as first_touches,
        sum(case when is_last_touch then 1 else 0 end) as last_touches,
        count(*) as total_touchpoints
        
    from attribution_models
    group by 1, 2, 3, 4, 5
),

final as (
    select
        ca.*,
        
        -- Conversion rates
        case 
            when total_leads_touched > 0 then 
                converted_leads::float / total_leads_touched * 100
            else 0
        end as lead_conversion_rate,
        
        -- Cost per attribution (by model)
        case 
            when first_touch_conversions > 0 then 
                total_spend / first_touch_conversions
            else null
        end as first_touch_cpa,
        
        case 
            when last_touch_conversions > 0 then 
                total_spend / last_touch_conversions
            else null
        end as last_touch_cpa,
        
        case 
            when linear_conversions > 0 then 
                total_spend / linear_conversions
            else null
        end as linear_cpa,
        
        case 
            when time_decay_conversions > 0 then 
                total_spend / time_decay_conversions
            else null
        end as time_decay_cpa,
        
        case 
            when position_based_conversions > 0 then 
                total_spend / position_based_conversions
            else null
        end as position_based_cpa,
        
        -- Attribution pattern classification
        case
            when first_touch_conversions > greatest(last_touch_conversions, linear_conversions) then 'first_touch_dominant'
            when last_touch_conversions > greatest(first_touch_conversions, linear_conversions) then 'last_touch_dominant'
            when abs(first_touch_conversions - last_touch_conversions) < 0.1 then 'balanced_attribution'
            else 'middle_touch_dominant'
        end as attribution_pattern,
        
        -- Performance scoring based on linear attribution
        case
            when linear_conversions > 0 and total_spend / linear_conversions < 50 then 'excellent'
            when linear_conversions > 0 and total_spend / linear_conversions < 100 then 'good'
            when linear_conversions > 0 and total_spend / linear_conversions < 200 then 'average'
            when linear_conversions > 0 then 'poor'
            else 'no_conversions'
        end as attribution_performance,
        
        -- Metadata
        current_timestamp as _int_updated_at
        
    from campaign_attribution ca
)

select * from final