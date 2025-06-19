{{ config(
    materialized='view',
    tags=['stripe', 'billing']
) }}

with source as (
    select * from {{ source('stripe', 'prices') }}
),

renamed as (
    select
        -- IDs
        id as price_id,
        product as product_id,
        
        -- Price Details
        active as is_active,
        currency,
        unit_amount,
        created,
        
        -- Recurring Details
        recurring_interval as billing_interval,
        recurring_interval_count as interval_count,
        
        -- Metadata
        metadata,
        
        -- Price Calculations
        cast(unit_amount as float) / 100 as price_amount,
        
        -- Billing Period Standardization
        case
            when recurring_interval = 'month' and recurring_interval_count = 1 then 'Monthly'
            when recurring_interval = 'month' and recurring_interval_count = 3 then 'Quarterly'
            when recurring_interval = 'month' and recurring_interval_count = 6 then 'Semi-Annual'
            when recurring_interval = 'year' and recurring_interval_count = 1 then 'Annual'
            when recurring_interval = 'week' then 'Weekly'
            when recurring_interval = 'day' then 'Daily'
            else 'Custom'
        end as billing_period,
        
        -- Annual Value Calculation
        case
            when recurring_interval = 'month' then (cast(unit_amount as float) / 100) * 12 / recurring_interval_count
            when recurring_interval = 'year' then (cast(unit_amount as float) / 100) / recurring_interval_count
            when recurring_interval = 'week' then (cast(unit_amount as float) / 100) * 52 / recurring_interval_count
            when recurring_interval = 'day' then (cast(unit_amount as float) / 100) * 365 / recurring_interval_count
            else null
        end as annual_value,
        
        -- Price Tier Classification
        case
            when recurring_interval = 'month' and (cast(unit_amount as float) / 100) < 50 then 'Starter'
            when recurring_interval = 'month' and (cast(unit_amount as float) / 100) < 200 then 'Professional'
            when recurring_interval = 'month' and (cast(unit_amount as float) / 100) < 500 then 'Business'
            when recurring_interval = 'month' and (cast(unit_amount as float) / 100) >= 500 then 'Enterprise'
            else 'Custom'
        end as price_tier,
        
        -- Currency Validation
        case
            when currency in ('usd', 'eur', 'gbp', 'cad', 'aud') then currency
            else 'other'
        end as normalized_currency,
        
        -- Timestamps
        to_timestamp(created) as created_at,
        
        -- Data Quality
        case
            when id is null then 'Missing Price ID'
            when product is null then 'Missing Product ID'
            when unit_amount is null or unit_amount < 0 then 'Invalid Amount'
            when currency is null then 'Missing Currency'
            else 'Valid'
        end as data_quality_flag,
        
        -- Audit Fields
        current_timestamp as _dbt_inserted_at

    from source
),

final as (
    select * from renamed
)

select * from final
