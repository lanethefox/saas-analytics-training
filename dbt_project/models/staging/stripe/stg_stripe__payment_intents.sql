{{ config(materialized='view') }}

-- Staging model for Stripe payment intent data
-- Modern payment processing flow tracking

select
    -- Primary identifiers
    id as stripe_payment_intent_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} as stripe_payment_intent_key,
    
    -- Foreign keys
    customer as stripe_customer_id,
    invoice as stripe_invoice_id,
    payment_method as stripe_payment_method_id,
    
    -- Transaction details
    amount / 100.0 as payment_amount_usd,
    amount_capturable / 100.0 as capturable_amount_usd,
    amount_received / 100.0 as received_amount_usd,
    currency,
    description,
    
    -- Payment status and configuration
    status,
    capture_method,
    confirmation_method,
    setup_future_usage,
    
    -- Cancellation info
    canceled_at,
    cancellation_reason,
    
    -- Payment method details
    payment_method_types,
    
    -- Error handling
    last_payment_error->>'code' as error_code,
    last_payment_error->>'message' as error_message,
    last_payment_error->>'type' as error_type,
    
    -- Charges data (extract first charge ID if available)
    charges->'data'->0->>'id' as primary_charge_id,
    jsonb_array_length(charges->'data') as charge_count,
    
    -- Timestamps
    to_timestamp(created) as payment_intent_created_at,
    
    -- Status categorization
    case
        when status = 'succeeded' then 'Succeeded'
        when status = 'processing' then 'Processing'
        when status = 'requires_payment_method' then 'Requires Payment Method'
        when status = 'requires_confirmation' then 'Requires Confirmation'
        when status = 'requires_action' then 'Requires Action'
        when status = 'canceled' then 'Canceled'
        when status = 'requires_capture' then 'Requires Capture'
        else 'Other'
    end as status_category,
    
    -- Payment timeline
    case
        when status = 'succeeded' then 'Complete'
        when status = 'canceled' then 'Canceled'
        when status like 'requires%' then 'Pending Action'
        when status = 'processing' then 'In Progress'
        else 'Other'
    end as payment_stage,
    
    -- Risk indicators
    case
        when last_payment_error is not null then 'Has Error'
        when status = 'canceled' then 'Canceled'
        when status = 'succeeded' then 'No Risk'
        else 'Pending'
    end as risk_status,
    
    -- Payment size categorization
    case
        when amount < 1000 then 'Micro'         -- Less than $10
        when amount < 5000 then 'Small'         -- $10-$50
        when amount < 25000 then 'Medium'       -- $50-$250
        when amount < 100000 then 'Large'       -- $250-$1000
        else 'Enterprise'                        -- Over $1000
    end as payment_size_category,
    
    -- Additional flags
    livemode,
    case when metadata is not null then metadata->>'account_id' else null end as account_id,
    
    -- Data quality
    case
        when id is null then 'Missing Payment Intent ID'
        when amount is null or amount < 0 then 'Invalid Amount'
        when status is null then 'Missing Status'
        else 'Valid'
    end as data_quality_flag,
    
    -- Raw data
    metadata,
    next_action,
    
    -- Metadata
    current_timestamp as _stg_loaded_at
    
from {{ source('stripe', 'payment_intents') }}
