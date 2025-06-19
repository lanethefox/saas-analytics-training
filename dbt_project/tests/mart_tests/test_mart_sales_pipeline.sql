-- Test mart_sales__pipeline for sales pipeline metrics
WITH pipeline_validation AS (
    SELECT 
        COUNT(*) AS total_opportunities,
        COUNT(DISTINCT opportunity_id) AS unique_opportunities,
        SUM(CASE WHEN opportunity_value < 0 THEN 1 ELSE 0 END) AS negative_values,
        SUM(CASE WHEN probability < 0 OR probability > 100 THEN 1 ELSE 0 END) AS invalid_probability,
        SUM(CASE WHEN weighted_value < 0 THEN 1 ELSE 0 END) AS negative_weighted_value,
        SUM(CASE WHEN days_in_stage < 0 THEN 1 ELSE 0 END) AS negative_days,
        SUM(CASE WHEN stage NOT IN ('prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost') THEN 1 ELSE 0 END) AS invalid_stages
    FROM {{ ref('mart_sales__pipeline') }}
),
weighted_value_check AS (
    -- Weighted value should equal opportunity_value * probability/100
    SELECT 
        COUNT(*) AS incorrect_weighted_values
    FROM {{ ref('mart_sales__pipeline') }}
    WHERE ABS(weighted_value - (opportunity_value * probability / 100.0)) > 0.01
      AND opportunity_value > 0
),
stage_progression AS (
    -- Validate stage progression logic
    SELECT 
        COUNT(*) AS invalid_progressions
    FROM {{ ref('mart_sales__pipeline') }}
    WHERE (stage = 'closed_won' AND probability < 100)
       OR (stage = 'closed_lost' AND probability > 0)
       OR (stage = 'negotiation' AND probability < 50)
),
close_date_validation AS (
    -- Expected close dates should be reasonable
    SELECT 
        COUNT(*) AS unreasonable_close_dates
    FROM {{ ref('mart_sales__pipeline') }}
    WHERE expected_close_date < created_date
       OR expected_close_date > created_date + INTERVAL '365 days'
       OR (stage IN ('closed_won', 'closed_lost') AND close_date IS NULL)
),
rep_performance AS (
    -- Check sales rep assignments
    SELECT 
        COUNT(*) AS missing_reps
    FROM {{ ref('mart_sales__pipeline') }}
    WHERE sales_rep_id IS NULL
       AND stage NOT IN ('closed_lost')
),
invalid_data AS (
    SELECT 
        v.*,
        wv.incorrect_weighted_values,
        sp.invalid_progressions,
        cd.unreasonable_close_dates,
        rp.missing_reps
    FROM pipeline_validation v
    CROSS JOIN weighted_value_check wv
    CROSS JOIN stage_progression sp
    CROSS JOIN close_date_validation cd
    CROSS JOIN rep_performance rp
    WHERE v.negative_values > 0
       OR v.invalid_probability > 0
       OR v.negative_weighted_value > 0
       OR v.negative_days > 0
       OR v.invalid_stages > 0
       OR wv.incorrect_weighted_values > 0
       OR sp.invalid_progressions > 0
       OR cd.unreasonable_close_dates > 0
       OR rp.missing_reps > 0
)
-- Test fails if sales pipeline data is invalid
SELECT * FROM invalid_data