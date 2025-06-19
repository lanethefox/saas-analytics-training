{{ config(
    materialized='incremental',
    unique_key='campaign_history_id',
    on_schema_change='sync_all_columns',
    indexes=[
        {'columns': ['campaign_id', 'valid_from']},
        {'columns': ['valid_from']},
        {'columns': ['change_type']}
    ]
) }}

-- Entity: Campaigns (History/Change Tracking)
-- Tracks campaign evolution including budget changes, creative updates, and performance shifts
-- Enables marketing mix modeling, attribution development, and optimization analysis

with campaign_current as (
    select * from {{ ref('entity_campaigns') }}
),

history_records as (
    select
        -- Generate unique history ID
        {{ dbt_utils.generate_surrogate_key(['campaign_id', 'current_timestamp']) }} as campaign_history_id,
        
        -- Campaign identifiers
        campaign_id,
        campaign_key,
        platform,
        
        -- Change tracking
        'snapshot' as change_type,
        
        -- Campaign details at time of change
        campaign_name,
        campaign_type,
        campaign_status,
        is_active,
        campaign_lifecycle_stage,
        
        -- Performance metrics at time of change
        total_spend,
        0::numeric as previous_spend,
        0::numeric as spend_change,
        
        impressions,
        clicks,
        conversions,
        conversion_value,
        
        -- Performance rates
        click_through_rate,
        conversion_rate,
        cost_per_conversion,
        roi_percentage,
        
        -- Performance classification
        performance_tier,
        ''::text as previous_performance_tier,
        
        performance_score,
        0::numeric as previous_performance_score,
        0::numeric as performance_delta,
        
        -- Attribution metrics
        total_leads_touched,
        converted_leads,
        lead_conversion_rate,
        
        linear_conversions,
        linear_cpa,
        
        attribution_pattern,
        attribution_performance,
        
        -- Campaign settings
        target_audience,
        target_location,
        bid_strategy,
        
        -- Optimization tracking
        optimization_recommendation,
        ''::text as previous_optimization,
        
        -- Budget tracking
        daily_spend_rate,
        
        -- Key dates
        campaign_created_at,
        start_date,
        end_date,
        
        -- Temporal validity
        current_timestamp as valid_from,
        null::timestamp as valid_to,
        true as is_current,
        
        -- Metadata
        current_timestamp as _entity_updated_at,
        '{{ invocation_id }}' as _dbt_invocation_id
        
    from campaign_current
    
    {% if is_incremental() %}
    -- For incremental runs, only capture meaningful changes
    where not exists (
        select 1 
        from {{ this }} h
        where h.campaign_id = campaign_current.campaign_id
          and h.is_current = true
          and h.campaign_status = campaign_current.campaign_status
          and h.total_spend = campaign_current.total_spend
          and h.conversions = campaign_current.conversions
          and h.performance_score = campaign_current.performance_score
    )
    {% endif %}
)

select * from history_records