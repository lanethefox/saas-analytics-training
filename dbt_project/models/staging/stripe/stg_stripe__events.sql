{{ config(materialized='view') }}

-- Staging model for Stripe event/webhook data
-- Complete audit log of all Stripe activities

select
    -- Primary identifiers
    id as stripe_event_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} as stripe_event_key,
    
    -- Event details
    type as event_type,
    object as object_type,
    api_version,
    livemode,
    pending_webhooks,
    
    -- Event data
    data,
    data->>'object' as event_object,
    data->'object'->>'id' as related_object_id,
    data->'object'->>'object' as related_object_type,
    
    -- Request information
    request->>'id' as request_id,
    request->>'idempotency_key' as idempotency_key,
    
    -- Timestamps
    created as event_created_at,
    
    -- Event categorization
    case
        when type like 'customer.%' then 'Customer'
        when type like 'charge.%' then 'Charge'
        when type like 'payment_intent.%' then 'Payment Intent'
        when type like 'invoice.%' then 'Invoice'
        when type like 'subscription.%' then 'Subscription'
        when type like 'payment_method.%' then 'Payment Method'
        when type like 'payout.%' then 'Payout'
        when type like 'product.%' then 'Product'
        when type like 'price.%' then 'Price'
        else 'Other'
    end as event_category,
    
    -- Event action
    case
        when type like '%.created' then 'Created'
        when type like '%.updated' then 'Updated'
        when type like '%.deleted' then 'Deleted'
        when type like '%.succeeded' then 'Succeeded'
        when type like '%.failed' then 'Failed'
        when type like '%.canceled' then 'Canceled'
        when type like '%.attached' then 'Attached'
        when type like '%.detached' then 'Detached'
        else 'Other'
    end as event_action,
    
    -- Important event flags
    case
        when type in (
            'charge.failed',
            'payment_intent.payment_failed',
            'invoice.payment_failed',
            'subscription.deleted'
        ) then true
        else false
    end as is_failure_event,
    
    case
        when type in (
            'charge.succeeded',
            'payment_intent.succeeded',
            'invoice.payment_succeeded'
        ) then true
        else false
    end as is_success_event,
    
    -- Data quality
    case
        when id is null then 'Missing Event ID'
        when type is null then 'Missing Event Type'
        when data is null then 'Missing Event Data'
        else 'Valid'
    end as data_quality_flag,
    
    -- Metadata
    current_timestamp as _stg_loaded_at
    
from {{ source('stripe', 'events') }}
