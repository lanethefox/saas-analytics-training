{{ config(materialized='view') }}

-- Staging model for Stripe customer data
-- Tracks billing relationships with payment status and risk scoring

with source_data as (
    select * from {{ source('stripe', 'customers') }}
),

enriched as (
    select
        -- Primary identifiers
        id as stripe_customer_id,
        {{ dbt_utils.generate_surrogate_key(['id']) }} as stripe_customer_key,
        
        -- Extract account_id from metadata
        case 
            when metadata is not null 
            then metadata->>'account_id'
            else null
        end as account_id,
        
        -- Customer details
        NULL::text as customer_email,
        NULL::text as customer_name,
        trim(description) as customer_description,
        phone,
        currency,
        delinquent,
        tax_exempt,
        livemode,
        invoice_prefix,
        
        -- Balance (not in this table, default to 0)
        0::decimal as account_balance_usd,
        
        -- Shipping information
        case 
            when shipping is not null 
            then trim(shipping -> 'address' ->> 'line1')
            else null
        end as shipping_address_line1,
        
        case 
            when shipping is not null 
            then trim(shipping -> 'address' ->> 'city')
            else null
        end as shipping_city,
        
        case 
            when shipping is not null 
            then trim(shipping -> 'address' ->> 'state')
            else null
        end as shipping_state,
        
        case 
            when shipping is not null 
            then trim(shipping -> 'address' ->> 'country')
            else null
        end as shipping_country,
        
        -- Address information
        case 
            when address is not null 
            then trim(address ->> 'line1')
            else null
        end as billing_address_line1,
        
        case 
            when address is not null 
            then trim(address ->> 'city')
            else null
        end as billing_city,
        
        case 
            when address is not null 
            then trim(address ->> 'state')
            else null
        end as billing_state,
        
        case 
            when address is not null 
            then trim(address ->> 'country')
            else null
        end as billing_country,
        
        -- Standardized timestamps
        created as customer_created_at,
        
        -- Customer status classification
        case 
            when delinquent then 'delinquent'
            else 'current'
        end as customer_status,
        
        -- Risk scoring
        case 
            when delinquent then 100
            else 0
        end as payment_risk_score,
        
        -- Customer lifetime calculation
        extract(days from (current_timestamp - created)) as customer_age_days,
        extract(months from age(current_timestamp, created)) as customer_age_months,
        
        -- Customer categorization
        case 
            when livemode = false then 'test'
            when extract(days from (current_timestamp - created)) <= 30 then 'new'
            when extract(days from (current_timestamp - created)) <= 90 then 'recent'
            when extract(days from (current_timestamp - created)) <= 365 then 'established'
            else 'long_term'
        end as customer_tenure_category,
        
        -- Data quality flags
        case 
            when email is null or trim(email) = '' then true 
            else false 
        end as missing_email,
        
        case 
            when email not like '%@%' then true 
            else false 
        end as invalid_email,
        
        -- Raw data
        metadata,
        address as billing_address_raw,
        shipping as shipping_address_raw,
        
        -- Metadata
        current_timestamp as _stg_loaded_at

    from source_data
)

select * from enriched
