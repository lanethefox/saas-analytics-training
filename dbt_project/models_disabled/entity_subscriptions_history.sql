{{
    config(
        materialized = 'incremental',
        unique_key = ['subscription_id', 'valid_from'],
        on_schema_change = 'fail'
    )
}}

with subscription_snapshots as (
    select
        subscription_id,
        subscription_name,
        account_id,
        plan_id,
        plan_name,
        status,
        billing_period,
        billing_interval,
        currency,
        mrr,
        arr,
        quantity,
        unit_price,
        discount_percentage,
        discount_amount,
        tax_rate,
        tax_amount,
        total_amount,
        start_date,
        end_date,
        trial_start_date,
        trial_end_date,
        activated_at,
        cancelled_at,
        cancellation_reason,
        renewal_date,
        payment_method,
        payment_status,
        is_active,
        auto_renew,
        created_at,
        updated_at,
        _synced_at,
        
        -- Create validity window
        updated_at as valid_from,
        lead(updated_at, 1, '9999-12-31'::timestamp) over (
            partition by subscription_id 
            order by updated_at
        ) as valid_to,
        
        -- Track what changed
        lag(status) over (partition by subscription_id order by updated_at) as prev_status,
        lag(plan_id) over (partition by subscription_id order by updated_at) as prev_plan_id,
        lag(mrr) over (partition by subscription_id order by updated_at) as prev_mrr,
        lag(quantity) over (partition by subscription_id order by updated_at) as prev_quantity,
        lag(discount_percentage) over (partition by subscription_id order by updated_at) as prev_discount_percentage,
        lag(payment_status) over (partition by subscription_id order by updated_at) as prev_payment_status,
        lag(auto_renew) over (partition by subscription_id order by updated_at) as prev_auto_renew,
        lag(is_active) over (partition by subscription_id order by updated_at) as prev_is_active
        
    from {{ ref('entity_subscriptions') }}
    
    {% if is_incremental() %}
    where updated_at > (select max(valid_from) from {{ this }})
    {% endif %}
),

subscription_history as (
    select
        subscription_id,
        subscription_name,
        account_id,
        plan_id,
        plan_name,
        status,
        billing_period,
        billing_interval,
        currency,
        mrr,
        arr,
        quantity,
        unit_price,
        discount_percentage,
        discount_amount,
        tax_rate,
        tax_amount,
        total_amount,
        start_date,
        end_date,
        trial_start_date,
        trial_end_date,
        activated_at,
        cancelled_at,
        cancellation_reason,
        renewal_date,
        payment_method,
        payment_status,
        is_active,
        auto_renew,
        created_at,
        updated_at,
        valid_from,
        valid_to,
        
        -- Change tracking flags
        case when status != prev_status then true else false end as status_changed,
        case when plan_id != prev_plan_id then true else false end as plan_changed,
        case when mrr != prev_mrr then true else false end as mrr_changed,
        case when quantity != prev_quantity then true else false end as quantity_changed,
        case when discount_percentage != prev_discount_percentage then true else false end as discount_changed,
        case when payment_status != prev_payment_status then true else false end as payment_status_changed,
        case when auto_renew != prev_auto_renew then true else false end as auto_renew_changed,
        case when is_active != prev_is_active then true else false end as active_status_changed,
        
        -- MRR change calculation
        mrr - coalesce(prev_mrr, 0) as mrr_change_amount,
        case 
            when prev_mrr > 0 then ((mrr - prev_mrr) / prev_mrr) * 100 
            else null 
        end as mrr_change_percentage,
        
        -- Change summary
        case
            when prev_status is null then 'Initial Record'
            when status != prev_status then 'Status Change: ' || prev_status || ' → ' || status
            when plan_id != prev_plan_id then 'Plan Change'
            when mrr > prev_mrr then 'Expansion: +$' || round(mrr - prev_mrr, 2)
            when mrr < prev_mrr then 'Contraction: -$' || round(prev_mrr - mrr, 2)
            when quantity != prev_quantity then 'Quantity Change: ' || prev_quantity || ' → ' || quantity
            when discount_percentage != prev_discount_percentage then 'Discount Change'
            when payment_status != prev_payment_status then 'Payment Status: ' || prev_payment_status || ' → ' || payment_status
            when auto_renew != prev_auto_renew then case when auto_renew then 'Auto-Renew Enabled' else 'Auto-Renew Disabled' end
            else 'Other Update'
        end as change_type,
        
        -- Record metadata
        row_number() over (partition by subscription_id order by valid_from) as version_number,
        case when valid_to = '9999-12-31'::timestamp then true else false end as is_current,
        _synced_at
        
    from subscription_snapshots
)

select * from subscription_history