{{ config(materialized='table') }}

-- Intermediate model: Subscription revenue metrics and payment health
-- Analyzes payment history, calculates LTV, and assesses churn risk
-- Combines subscription data with invoice and payment information

with subscriptions as (
    select * from {{ ref('int_subscriptions__core') }}
),

stripe_invoices as (
    select * from {{ ref('stg_stripe__invoices') }}
),

stripe_charges as (
    select * from {{ ref('stg_stripe__charges') }}
),

-- Calculate payment history metrics
payment_history as (
    select
        i.stripe_subscription_id as subscription_id,
        count(*) as total_invoices,
        count(case when i.status = 'paid' then 1 end) as paid_invoices,
        count(case when i.status = 'open' then 1 end) as open_invoices,
        count(case when i.status = 'void' then 1 end) as void_invoices,
        count(case when i.status = 'uncollectible' then 1 end) as uncollectible_invoices,
        
        -- Payment amounts
        sum(case when i.status = 'paid' then i.amount_paid_usd else 0 end) as total_paid,
        sum(case when i.status = 'paid' then i.amount_due_usd else 0 end) as total_invoiced,
        
        -- Payment timing
        avg(
            case 
                when i.status = 'paid' and i.paid = true then
                    extract(epoch from (current_timestamp - i.invoice_created_at)) / 86400
                else null
            end
        ) as avg_days_to_payment,
        
        -- Recent payment behavior (last 6 months)
        count(
            case 
                when i.invoice_created_at >= current_date - interval '6 months' 
                then 1 
            end
        ) as recent_invoices,
        count(
            case 
                when i.invoice_created_at >= current_date - interval '6 months' 
                    and i.status = 'paid'
                then 1 
            end
        ) as recent_paid_invoices,
        
        -- Last payment info
        max(case when i.status = 'paid' then i.invoice_created_at end) as last_payment_date,
        max(i.invoice_created_at) as last_invoice_date
        
    from stripe_invoices i
    where i.stripe_subscription_id is not null
    group by 1
),

-- Calculate charge success rates
charge_metrics as (
    select
        i.stripe_subscription_id as subscription_id,
        count(distinct c.stripe_charge_id) as total_charges,
        count(distinct case when c.status = 'succeeded' then c.stripe_charge_id end) as successful_charges,
        count(distinct case when c.status = 'failed' then c.stripe_charge_id end) as failed_charges,
        count(distinct 
            case 
                when c.stripe_charge_created_at >= current_date - interval '3 months' 
                then c.stripe_charge_id 
            end
        ) as recent_charges,
        count(distinct 
            case 
                when c.stripe_charge_created_at >= current_date - interval '3 months'
                    and c.status = 'failed'
                then c.stripe_charge_id 
            end
        ) as recent_failed_charges
    from stripe_charges c
    join stripe_invoices i on c.stripe_invoice_id = i.stripe_invoice_id
    where i.stripe_subscription_id is not null
    group by 1
),

-- Combine subscription and payment data
subscription_payment_health as (
    select
        s.*,
        coalesce(ph.total_invoices, 0) as total_invoices,
        coalesce(ph.paid_invoices, 0) as paid_invoices,
        coalesce(ph.total_paid, 0) as lifetime_value,
        coalesce(ph.avg_days_to_payment, 0) as avg_days_to_payment,
        ph.last_payment_date,
        
        -- Payment success rate
        case 
            when ph.total_invoices > 0 then 
                ph.paid_invoices::float / ph.total_invoices * 100
            else 0
        end as payment_success_rate,
        
        -- Recent payment rate
        case 
            when ph.recent_invoices > 0 then 
                ph.recent_paid_invoices::float / ph.recent_invoices * 100
            else 0
        end as recent_payment_rate,
        
        -- Charge success rate
        case 
            when cm.total_charges > 0 then 
                cm.successful_charges::float / cm.total_charges * 100
            else 0
        end as charge_success_rate,
        
        -- Days since last payment
        case 
            when ph.last_payment_date is not null then
                extract(days from current_timestamp - ph.last_payment_date)
            else null
        end as days_since_last_payment
        
    from subscriptions s
    left join payment_history ph on s.subscription_id = ph.subscription_id
    left join charge_metrics cm on s.subscription_id = cm.subscription_id
),

-- Calculate health scores and risk metrics
final as (
    select
        sph.*,
        
        -- Payment health score (composite of multiple factors)
        round(
            (
                -- Payment success rate (40% weight)
                coalesce(sph.payment_success_rate, 0) * 0.4 +
                -- Recent payment behavior (30% weight)
                coalesce(sph.recent_payment_rate, 0) * 0.3 +
                -- Charge success rate (30% weight)
                coalesce(sph.charge_success_rate, 0) * 0.3
            )::numeric, 2
        ) as payment_health_score,
        
        -- Churn risk score (0-100, higher = more risk)
        case
            when sph.has_churned then 100
            when sph.subscription_status in ('past_due', 'unpaid') then 80
            when sph.days_since_last_payment > 90 then 70
            when sph.recent_payment_rate < 50 then 60
            when sph.charge_success_rate < 80 then 50
            when sph.payment_success_rate < 90 then 40
            else 20
        end as churn_risk_score,
        
        -- Revenue at risk
        case 
            when sph.subscription_status in ('past_due', 'unpaid', 'canceled') 
            then sph.monthly_recurring_revenue
            else 0
        end as mrr_at_risk,
        
        -- Estimated LTV based on payment history
        case 
            when sph.subscription_age_months > 0 and sph.lifetime_value > 0 then
                sph.lifetime_value / sph.subscription_age_months * 12 -- Annualized
            else sph.annual_recurring_revenue
        end as estimated_annual_ltv,
        
        -- Risk classification
        case 
            when sph.has_churned then 'churned'
            when sph.subscription_status in ('past_due', 'unpaid') then 'high_risk'
            when sph.days_since_last_payment > 60 or sph.recent_payment_rate < 70 then 'medium_risk'
            when sph.payment_success_rate < 90 or sph.charge_success_rate < 90 then 'low_risk'
            else 'minimal_risk'
        end as risk_classification,
        
        -- Payment behavior classification
        case 
            when sph.payment_success_rate >= 95 and sph.avg_days_to_payment <= 1 then 'excellent_payer'
            when sph.payment_success_rate >= 90 and sph.avg_days_to_payment <= 7 then 'good_payer'
            when sph.payment_success_rate >= 80 then 'fair_payer'
            when sph.payment_success_rate >= 70 then 'poor_payer'
            else 'very_poor_payer'
        end as payment_behavior
        
    from subscription_payment_health sph
)

select * from final