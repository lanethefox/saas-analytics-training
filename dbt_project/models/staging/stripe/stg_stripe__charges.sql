{{ config(materialized='view') }}

-- Staging model for Stripe charge/payment data
-- Tracks successful payment processing with risk scoring

select
    -- Primary identifiers
    id as stripe_charge_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} as stripe_charge_key,
    
    -- Foreign keys
    customer as stripe_customer_id,
    invoice as stripe_invoice_id,
    payment_intent as stripe_payment_intent_id,
    
    -- Transaction details
    amount / 100.0 as charge_amount_usd,
    amount_refunded / 100.0 as refunded_amount_usd,
    currency,
    description,
    
    -- Payment status
    status,
    paid,
    captured,
    refunded,
    disputed,
    
    -- Payment method information
    payment_method,
    payment_method_details->>'type' as payment_method_type,
    payment_method_details->'card'->>'brand' as card_brand,
    payment_method_details->'card'->>'last4' as card_last4,
    payment_method_details->'card'->>'network' as card_network,
    (payment_method_details->'card'->>'exp_month')::int as card_exp_month,
    (payment_method_details->'card'->>'exp_year')::int as card_exp_year,
    
    -- Risk assessment
    outcome->>'network_status' as network_status,
    outcome->>'reason' as outcome_reason,
    outcome->>'risk_level' as risk_level,
    (outcome->>'risk_score')::int as risk_score,
    
    -- Failure information
    failure_code,
    failure_message,
    
    -- Geographic information (properly extract nested JSON)
    billing_details->'address'->>'country' as billing_country,
    billing_details->'address'->>'city' as billing_city,
    billing_details->'address'->>'state' as billing_state,
    billing_details->'address'->>'postal_code' as billing_postal_code,
    
    -- Timing
    created as stripe_charge_created_at,
    
    -- Account mapping
    metadata->>'account_id' as account_id,
    
    -- Processing details
    balance_transaction as stripe_balance_transaction_id,
    receipt_url,
    
    -- Additional flags
    livemode,
    
    -- Data quality
    case
        when id is null then 'Missing Charge ID'
        when customer is null then 'Missing Customer'
        when amount is null or amount < 0 then 'Invalid Amount'
        else 'Valid'
    end as data_quality_flag,
    
    -- Metadata
    current_timestamp as _stg_loaded_at
    
from {{ source('stripe', 'charges') }}
