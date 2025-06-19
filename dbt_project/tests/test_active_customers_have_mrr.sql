-- Test: Ensure active customers have positive MRR
-- All customers with active subscriptions should have MRR > 0

select 
    account_id,
    subscription_status,
    monthly_recurring_revenue
from {{ ref('entity_customers') }}
where subscription_status = 'active'
  and (monthly_recurring_revenue <= 0 or monthly_recurring_revenue is null)
