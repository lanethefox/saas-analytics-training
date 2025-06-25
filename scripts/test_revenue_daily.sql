-- Test query to verify the revenue daily logic works
WITH daily_customer_metrics AS (
    SELECT 
        snapshot_date as metric_date,
        COUNT(DISTINCT account_id) as total_customers,
        COUNT(DISTINCT CASE WHEN customer_status = 'active' THEN account_id END) as active_customers,
        SUM(CASE WHEN customer_status = 'active' THEN monthly_recurring_revenue ELSE 0 END) as total_mrr
    FROM intermediate.fct_customer_history
    WHERE snapshot_date >= CURRENT_DATE - interval '7 days'
    GROUP BY 1
)
SELECT * FROM daily_customer_metrics
ORDER BY metric_date DESC;