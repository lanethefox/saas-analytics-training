{{ config(materialized='view') }}

-- Staging model for Stripe invoice data
-- Tracks billing cycles and payment status

select
    -- Primary identifiers
    id as stripe_invoice_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} as stripe_invoice_key,
    
    -- Foreign keys
    customer as stripe_customer_id,
    subscription as stripe_subscription_id,
    charge as stripe_charge_id,
    payment_intent as stripe_payment_intent_id,
    
    -- Invoice details
    number as invoice_number,
    status,
    
    -- Amounts (convert from cents to dollars)
    amount_due / 100.0 as amount_due_usd,
    amount_paid / 100.0 as amount_paid_usd,
    amount_remaining / 100.0 as amount_remaining_usd,
    subtotal / 100.0 as subtotal_usd,
    total / 100.0 as total_usd,
    
    -- Invoice metadata
    billing_reason,
    collection_method,
    currency,
    attempt_count,
    
    -- Customer information
    customer_email,
    customer_name,
    customer_phone,
    
    -- Payment status
    paid,
    attempted,
    
    -- Billing period
    period_start as billing_period_start,
    period_end as billing_period_end,
    extract(days from (period_end - period_start)) as billing_period_days,
    
    -- Dates
    created as invoice_created_at,
    due_date,
    
    -- Status categorization
    case
        when status = 'paid' then 'Paid'
        when status = 'open' then 'Open'
        when status = 'draft' then 'Draft'
        when status = 'void' then 'Void'
        when status = 'uncollectible' then 'Uncollectible'
        else 'Other'
    end as invoice_status_category,
    
    -- Payment timeline
    case
        when paid = true then 'Paid'
        when due_date < current_timestamp then 'Overdue'
        when due_date <= current_timestamp + interval '7 days' then 'Due Soon'
        else 'Future'
    end as payment_timeline,
    
    -- Days until/since due
    case
        when paid = true then 0
        else extract(days from (due_date - current_timestamp))
    end as days_until_due,
    
    -- Collection risk
    case
        when status = 'uncollectible' then 'Write-off'
        when paid = true then 'No Risk'
        when due_date < current_timestamp - interval '90 days' then 'High Risk'
        when due_date < current_timestamp - interval '30 days' then 'Medium Risk'
        when due_date < current_timestamp then 'Low Risk'
        else 'Current'
    end as collection_risk,
    
    -- Invoice size categorization
    case
        when total < 5000 then 'Small'        -- Less than $50
        when total < 25000 then 'Medium'      -- $50-$250
        when total < 100000 then 'Large'      -- $250-$1000
        else 'Enterprise'                      -- Over $1000
    end as invoice_size_category,
    
    -- Additional flags
    livemode,
    auto_advance,
    
    -- Data quality
    case
        when id is null then 'Missing Invoice ID'
        when customer is null then 'Missing Customer'
        when amount_due is null then 'Missing Amount'
        when status is null then 'Missing Status'
        else 'Valid'
    end as data_quality_flag,
    
    -- Metadata fields
    metadata,
    
    -- Audit
    current_timestamp as _stg_loaded_at
    
from {{ source('stripe', 'invoices') }}
