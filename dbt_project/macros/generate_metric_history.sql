-- Macro to generate historical snapshots for metrics tables
-- This allows us to simulate having taken daily snapshots over time

{% macro generate_metric_history(start_date='2023-01-01') %}
  {% if is_incremental() %}
    -- For incremental runs, only add new dates
    WHERE metric_date > (SELECT MAX(metric_date) FROM {{ this }})
      AND metric_date <= CURRENT_DATE
  {% else %}
    -- For full refresh, generate history from start_date
    WHERE metric_date >= '{{ start_date }}'::DATE
      AND metric_date <= CURRENT_DATE
  {% endif %}
{% endmacro %}

{% macro generate_date_spine(start_date='2023-01-01', date_column='metric_date') %}
  -- Generate a date spine for historical snapshots
  WITH date_spine AS (
    SELECT 
      generate_series(
        '{{ start_date }}'::DATE,
        CURRENT_DATE,
        '1 day'::INTERVAL
      )::DATE as {{ date_column }}
  )
  SELECT * FROM date_spine
{% endmacro %}

{% macro calculate_historical_value(metric_query, date_column='metric_date', growth_rate=0.02) %}
  -- Calculate historical values based on current value and growth rate
  -- This simulates what the metric would have been on past dates
  WITH current_value AS (
    {{ metric_query }}
  ),
  historical_factor AS (
    SELECT 
      {{ date_column }},
      -- Calculate compound growth factor from date to current
      POWER(1 + {{ growth_rate }}, 
        EXTRACT(EPOCH FROM (CURRENT_DATE - {{ date_column }})) / 86400.0 / 30.0
      ) as growth_factor
    FROM ({{ generate_date_spine(start_date='2023-01-01', date_column=date_column) }}) dates
  )
  SELECT 
    h.{{ date_column }},
    ROUND(c.value / h.growth_factor, 2) as historical_value
  FROM historical_factor h
  CROSS JOIN current_value c
{% endmacro %}