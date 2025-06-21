-- Test: Ensure customer health scores are within valid range
-- Health scores should always be between 0 and 1

select 
    account_id,
    customer_health_score
from {{ ref('entity_customers') }}
where customer_health_score < 0 
   or customer_health_score > 1
   or customer_health_score is null
