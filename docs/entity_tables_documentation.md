# Entity Tables Documentation

## entity.entity_devices

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| device_id | integer | Primary key |
| device_key | text | |
| location_id | integer | |
| account_id | integer | |
| device_type | varchar(100) | |
| model | varchar(100) | |
| firmware_version | varchar(50) | |
| serial_number | varchar(100) | |
| device_priority | text | |
| device_installed_date | date | |
| last_maintenance_date | date | |
| next_maintenance_due_date | timestamp | |
| maintenance_interval_days | integer | |
| maintenance_status | text | |
| days_since_maintenance | integer | |
| device_status | text | |
| connectivity_status | varchar(50) | |
| operational_status | text | |
| last_heartbeat_at | timestamp | |
| activity_status | text | |
| overall_health_score | numeric | |
| uptime_score | numeric | |
| performance_score | numeric | |
| alert_score | numeric | |
| performance_tier | text | |
| total_events_30d | bigint | |
| active_days_30d | bigint | |
| usage_events_30d | bigint | |
| alert_events_30d | bigint | |
| maintenance_events_30d | bigint | |
| quality_issues_30d | bigint | |
| total_volume_ml_30d | double precision | |
| total_volume_liters_30d | numeric | |
| avg_flow_rate_30d | double precision | |
| max_flow_rate_30d | double precision | |
| min_flow_rate_30d | double precision | |
| avg_temperature_30d | double precision | |
| max_temperature_30d | double precision | |
| min_temperature_30d | double precision | |
| high_temp_events_30d | bigint | |
| low_temp_events_30d | bigint | |
| avg_pressure_30d | double precision | |
| max_pressure_30d | double precision | |
| min_pressure_30d | double precision | |
| high_pressure_events_30d | bigint | |
| low_pressure_events_30d | bigint | |
| uptime_percentage_30d | numeric | |
| alert_rate_30d | numeric | |
| quality_issue_rate_30d | numeric | |
| maintenance_risk_level | text | |
| requires_immediate_attention | boolean | |
| device_lifecycle_stage | text | |
| device_age_days | integer | |
| is_newly_installed | boolean | |
| avg_daily_volume_ml_lifetime | numeric | |
| device_health_status | text | |
| estimated_revenue_30d | numeric | |
| location_name | text | |
| device_created_at | timestamp | |
| device_updated_at | timestamp | |
| last_activity_at | timestamp | |
| _entity_updated_at | timestamp with time zone | |

## entity.entity_devices_hourly

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| device_id | integer | |
| hour_timestamp | timestamp | |
| location_id | integer | |
| device_type | varchar(100) | |
| model | varchar(100) | |
| total_events | bigint | |
| pour_events | bigint | |
| error_events | bigint | |
| maintenance_events | bigint | |
| cleaning_events | bigint | |
| successful_events | bigint | |
| failed_events | bigint | |
| success_rate | numeric | |
| error_rate | numeric | |
| anomaly_rate | numeric | |
| total_volume_ml | numeric | |
| total_volume_liters | numeric | |
| avg_volume_per_event_ml | numeric | |
| max_volume_ml | numeric | |
| min_volume_ml | numeric | |
| avg_flow_rate | numeric | |
| max_flow_rate | numeric | |
| min_flow_rate | numeric | |
| flow_rate_stddev | numeric | |
| avg_temperature | numeric | |
| max_temperature | numeric | |
| min_temperature | numeric | |
| temperature_stddev | numeric | |
| avg_pressure | numeric | |
| max_pressure | numeric | |
| min_pressure | numeric | |
| pressure_stddev | numeric | |
| temperature_anomalies | bigint | |
| pressure_anomalies | bigint | |
| total_anomalies | bigint | |
| uptime_minutes | integer | |
| total_active_seconds | numeric | |
| utilization_rate | numeric | |
| revenue | double precision | |
| avg_events_24h | numeric | |
| avg_volume_ml_24h | numeric | |
| avg_error_rate_24h | numeric | |
| event_change_rate | numeric | |
| volume_trend | text | |
| hourly_performance_score | numeric | |
| performance_tier | text | |
| hour_of_day | numeric | |
| day_of_week | numeric | |
| is_weekend | boolean | |
| business_period | text | |
| is_peak_hour | boolean | |
| hourly_status | text | |
| meets_sla | boolean | |
| meets_uptime_sla | boolean | |
| alert_level | text | |
| _entity_updated_at | timestamp with time zone | |

## entity.entity_features

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| feature_key | text | |
| feature_name | varchar(100) | Unique key |
| feature_category | text | |
| accounts_using | bigint | |
| users_using | bigint | |
| total_usage_events | bigint | |
| avg_usage_per_account | double precision | |
| avg_daily_usage | double precision | |
| account_adoption_rate | double precision | |
| user_adoption_rate | double precision | |
| adoption_stage | text | |
| enterprise_adopters | bigint | |
| business_adopters | bigint | |
| starter_adopters | bigint | |
| avg_mrr_adopters | numeric | |
| avg_days_to_adoption_enterprise | numeric | |
| avg_days_to_adoption_business | numeric | |
| avg_days_to_adoption_starter | numeric | |
| enterprise_adoption_velocity | text | |
| enterprise_stickiness_rate | double precision | |
| business_stickiness_rate | double precision | |
| starter_stickiness_rate | double precision | |
| engagement_level | text | |
| feature_value_score | double precision | |
| strategic_importance | text | |
| market_fit_segment | text | |
| first_usage_date | timestamp | |
| last_usage_date | timestamp | |
| feature_age_days | numeric | |
| days_with_usage | bigint | |
| weeks_with_usage | bigint | |
| months_with_usage | bigint | |
| used_last_7_days | boolean | |
| used_last_30_days | boolean | |
| feature_maturity | text | |
| usage_frequency | text | |
| satisfaction_score | numeric | |
| estimated_revenue_impact | numeric | |
| roadmap_recommendation | text | |
| lifecycle_stage | text | |
| _entity_updated_at | timestamp with time zone | |
| _dbt_invocation_id | text | |
