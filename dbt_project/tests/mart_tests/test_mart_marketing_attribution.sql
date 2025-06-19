-- Test mart_marketing__attribution for marketing attribution logic
WITH attribution_validation AS (
    SELECT 
        COUNT(*) AS total_campaigns,
        COUNT(DISTINCT campaign_id) AS unique_campaigns,
        SUM(CASE WHEN total_spend < 0 THEN 1 ELSE 0 END) AS negative_spend,
        SUM(CASE WHEN attributed_revenue < 0 THEN 1 ELSE 0 END) AS negative_revenue,
        SUM(CASE WHEN conversions < 0 THEN 1 ELSE 0 END) AS negative_conversions,
        SUM(CASE WHEN roi < -100 THEN 1 ELSE 0 END) AS invalid_roi,
        SUM(CASE WHEN attribution_model NOT IN ('first_touch', 'last_touch', 'linear', 'time_decay', 'position_based') THEN 1 ELSE 0 END) AS invalid_model
    FROM {{ ref('mart_marketing__attribution') }}
),
roi_validation AS (
    -- Validate ROI calculations
    SELECT 
        COUNT(*) AS incorrect_roi
    FROM {{ ref('mart_marketing__attribution') }}
    WHERE total_spend > 0
      AND ABS(roi - ((attributed_revenue - total_spend) / total_spend * 100)) > 0.01
),
conversion_metrics AS (
    -- Validate conversion metrics
    SELECT 
        COUNT(*) AS invalid_conversion_metrics
    FROM {{ ref('mart_marketing__attribution') }}
    WHERE conversions > 0
      AND (cost_per_conversion < 0 OR cost_per_conversion != total_spend / conversions)
),
channel_validation AS (
    -- Ensure all major channels are represented
    SELECT 
        COUNT(DISTINCT channel) AS channel_count
    FROM {{ ref('mart_marketing__attribution') }}
),
invalid_data AS (
    SELECT 
        v.*,
        r.incorrect_roi,
        c.invalid_conversion_metrics,
        ch.channel_count
    FROM attribution_validation v
    CROSS JOIN roi_validation r
    CROSS JOIN conversion_metrics c
    CROSS JOIN channel_validation ch
    WHERE v.negative_spend > 0
       OR v.negative_revenue > 0
       OR v.negative_conversions > 0
       OR v.invalid_roi > 0
       OR v.invalid_model > 0
       OR r.incorrect_roi > 0
       OR c.invalid_conversion_metrics > 0
       OR ch.channel_count < 3  -- Should have at least 3 channels
)
-- Test fails if attribution logic is invalid
SELECT * FROM invalid_data