{{ config(materialized='view') }}

-- Staging model for Stripe subscription items (pricing tiers and quantities)
-- Standardizes recurring revenue calculations and plan features

with source_data as (
    select * from {{ source('stripe', 'subscription_items') }}
),

enriched as (
    select
        -- Primary identifiers
        id as stripe_subscription_item_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as subscription_item_key,
        subscription as stripe_subscription_id,
        price->>'id' as stripe_price_id,
        
        -- Quantity and billing
        quantity,
        
        -- Price information from JSONB price field
        (price->>'unit_amount')::numeric / 100.0 as unit_price_usd,  -- Stripe stores in cents
        price->>'currency' as currency,
        lower(trim(price->>'billing_scheme')) as billing_scheme,
        lower(trim(price->'recurring'->>'interval')) as billing_interval,
        (price->'recurring'->>'interval_count')::integer as billing_interval_count,
        
        -- Product information
        price->>'product' as stripe_product_id,
        
        -- Calculate recurring revenue
        case 
            when price->'recurring'->>'interval' = 'month' and (price->'recurring'->>'interval_count')::integer = 1
            then (quantity * (price->>'unit_amount')::numeric / 100.0)
            when price->'recurring'->>'interval' = 'year' and (price->'recurring'->>'interval_count')::integer = 1
            then (quantity * (price->>'unit_amount')::numeric / 100.0) / 12
            when price->'recurring'->>'interval' = 'week' and (price->'recurring'->>'interval_count')::integer = 1
            then (quantity * (price->>'unit_amount')::numeric / 100.0) * 4.33  -- Average weeks per month
            when price->'recurring'->>'interval' = 'month'
            then (quantity * (price->>'unit_amount')::numeric / 100.0) / (price->'recurring'->>'interval_count')::integer
            else 0
        end as monthly_recurring_revenue,
        
        case 
            when price->'recurring'->>'interval' = 'year' and (price->'recurring'->>'interval_count')::integer = 1
            then (quantity * (price->>'unit_amount')::numeric / 100.0)
            when price->'recurring'->>'interval' = 'month' and (price->'recurring'->>'interval_count')::integer = 1
            then (quantity * (price->>'unit_amount')::numeric / 100.0) * 12
            when price->'recurring'->>'interval' = 'week' and (price->'recurring'->>'interval_count')::integer = 1
            then (quantity * (price->>'unit_amount')::numeric / 100.0) * 52
            when price->'recurring'->>'interval' = 'month'
            then (quantity * (price->>'unit_amount')::numeric / 100.0) * 12 / (price->'recurring'->>'interval_count')::integer
            else 0
        end as annual_recurring_revenue,
        
        -- Pricing tier classification
        case 
            when (price->>'unit_amount')::numeric <= 999 then 'starter'
            when (price->>'unit_amount')::numeric <= 4999 then 'professional'
            when (price->>'unit_amount')::numeric <= 9999 then 'business'
            when (price->>'unit_amount')::numeric <= 24999 then 'enterprise'
            else 'custom'
        end as pricing_tier,
        
        -- Revenue type classification
        case 
            when price->'recurring' is not null then 'recurring'
            when price->>'type' = 'one_time' then 'one_time'
            else 'other'
        end as revenue_type,
        
        -- Billing frequency for reporting
        case 
            when price->'recurring'->>'interval' = 'month' and (price->'recurring'->>'interval_count')::integer = 1 then 'monthly'
            when price->'recurring'->>'interval' = 'year' and (price->'recurring'->>'interval_count')::integer = 1 then 'annual'
            when price->'recurring'->>'interval' = 'month' and (price->'recurring'->>'interval_count')::integer = 3 then 'quarterly'
            when price->'recurring'->>'interval' = 'month' and (price->'recurring'->>'interval_count')::integer = 6 then 'semi_annual'
            when price->'recurring'->>'interval' = 'week' then 'weekly'
            else 'other'
        end as billing_frequency_display,
        
        -- Usage-based pricing indicators
        case 
            when price->>'billing_scheme' = 'per_unit' then false
            when price->>'billing_scheme' = 'tiered' then true
            else false
        end as is_usage_based,
        
        -- Extract metadata for feature limits
        case 
            when price->'metadata' is not null and price->'metadata'->>'max_devices' is not null
            then (price->'metadata'->>'max_devices')::integer
            when (price->>'unit_amount')::numeric <= 2500 then 10
            when (price->>'unit_amount')::numeric <= 9900 then 50
            when (price->>'unit_amount')::numeric <= 24900 then 200
            else 1000
        end as max_devices_included,
        
        case 
            when price->'metadata' is not null and price->'metadata'->>'max_locations' is not null
            then (price->'metadata'->>'max_locations')::integer
            when (price->>'unit_amount')::numeric <= 2500 then 1
            when (price->>'unit_amount')::numeric <= 9900 then 5
            when (price->>'unit_amount')::numeric <= 24900 then 25
            else 100
        end as max_locations_included,
        
        -- Revenue calculations per unit
        (price->>'unit_amount')::numeric / 100.0 as unit_amount_usd,
        quantity * (price->>'unit_amount')::numeric / 100.0 as total_amount_usd,
        
        -- Timestamps
        created as subscription_item_created_at,
        
        -- Data quality flags
        case 
            when price is null then true
            when price->>'unit_amount' is null then true
            when quantity is null or quantity <= 0 then true
            else false
        end as has_data_quality_issues,
        
        -- Metadata
        current_timestamp as dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from source_data
)

select * from enriched
