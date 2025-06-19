-- 02_id_reconciliation.sql
-- Phase 1: Fix Existing ID Relationships
-- ======================================
-- This script creates normalized versions of all entity tables
-- with consistent ID relationships

-- ========================================
-- Create Normalized Entity Tables
-- ========================================

-- Normalized Customers
DROP TABLE IF EXISTS normalized.customers CASCADE;
CREATE TABLE normalized.customers AS
SELECT 
    m.normalized_account_id as account_id,
    c.company_name,
    c.industry,
    c.customer_tier,
    c.customer_status,
    c.created_at,
    c.first_subscription_date,
    c.days_since_creation,
    c.customer_lifetime_days,
    -- Revenue will be fixed in revenue_distribution.sql
    COALESCE(c.monthly_recurring_revenue, 0) as monthly_recurring_revenue_original,
    0::NUMERIC as monthly_recurring_revenue, -- To be calculated
    0::NUMERIC as annual_recurring_revenue,  -- To be calculated
    c.active_subscriptions,
    c.total_subscriptions,
    c.total_devices,
    c.device_events_30d,
    c.avg_device_uptime_30d,
    c.healthy_devices,
    c.device_health_percentage,
    c.last_device_activity,
    c.total_users,
    c.active_users_7d,
    c.active_users_30d,
    c.user_activation_rate_30d,
    c.avg_user_engagement_score,
    c.last_user_activity,
    c.total_locations,
    c.active_locations,
    c.location_activation_rate,
    c.avg_location_health_score,
    c.customer_health_score,
    c.growth_trajectory,
    c.expansion_score,
    c.retention_score,
    c.usage_score,
    c.feature_adoption_score,
    c.payment_reliability_score,
    c.support_satisfaction_score,
    c.nps_score,
    c.last_nps_survey_date,
    c.churn_risk_score,
    c.churn_risk_factors,
    c.predicted_churn_date,
    c.lifetime_value_predicted,
    c.lifetime_value_realized,
    c.next_best_action,
    c.last_updated
FROM entity.entity_customers c
INNER JOIN normalized.account_id_mapping m 
    ON c.account_id::VARCHAR = m.customer_account_id;

-- Add primary key and indexes
ALTER TABLE normalized.customers ADD PRIMARY KEY (account_id);
CREATE INDEX idx_norm_cust_status ON normalized.customers(customer_status);
CREATE INDEX idx_norm_cust_tier ON normalized.customers(customer_tier);
CREATE INDEX idx_norm_cust_created ON normalized.customers(created_at);

-- Normalized Subscriptions
DROP TABLE IF EXISTS normalized.subscriptions CASCADE;
CREATE TABLE normalized.subscriptions AS
SELECT 
    s.subscription_id,
    COALESCE(m.normalized_account_id, 'ACC_ORPHANED_' || s.account_id) as account_id,
    s.subscription_name,
    s.plan_type,
    s.plan_tier,
    s.billing_interval,
    s.subscription_status,
    s.contract_start_date,
    s.contract_end_date,
    s.next_renewal_date,
    s.auto_renewal,
    s.days_until_renewal,
    s.monthly_recurring_revenue,
    s.annual_recurring_revenue,
    s.currency,
    s.payment_method,
    s.payment_status,
    s.last_payment_date,
    s.last_payment_amount,
    s.total_paid_lifetime,
    s.discount_percentage,
    s.discount_end_date,
    s.trial_start_date,
    s.trial_end_date,
    s.is_trial,
    s.conversion_date,
    s.conversion_source,
    s.cancellation_date,
    s.cancellation_reason,
    s.pause_date,
    s.resume_date,
    s.subscription_age_days,
    s.lifecycle_stage,
    s.health_score,
    s.usage_percentage,
    s.overage_charges_mtd,
    s.expansion_potential_score,
    s.downgrade_risk_score,
    s.last_updated
FROM entity.entity_subscriptions s
LEFT JOIN normalized.account_id_mapping m 
    ON s.account_id::VARCHAR = m.subscription_account_id;

-- Add indexes
CREATE INDEX idx_norm_sub_account ON normalized.subscriptions(account_id);
CREATE INDEX idx_norm_sub_status ON normalized.subscriptions(subscription_status);
CREATE INDEX idx_norm_sub_plan ON normalized.subscriptions(plan_type);

-- Normalized Users
DROP TABLE IF EXISTS normalized.users CASCADE;
CREATE TABLE normalized.users AS
SELECT 
    u.user_id,
    u.user_key,
    COALESCE(
        m.normalized_account_id, 
        'ACC' || LPAD(u.account_id::VARCHAR, 10, '0')
    ) as account_id,
    u.email,
    u.first_name,
    u.last_name,
    u.full_name,
    u.user_role,
    u.role_type_standardized,
    u.user_status,
    u.access_level,
    u.email_domain,
    u.email_type,
    u.is_new_user,
    u.is_admin_user,
    u.is_manager_user,
    u.user_created_at,
    u.user_age_days,
    u.user_age_months,
    u.days_since_last_login,
    u.total_sessions_30d,
    u.total_session_minutes_30d,
    u.avg_session_minutes_30d,
    u.active_days_30d,
    u.device_types_used_30d,
    u.sessions_per_active_day_30d,
    u.features_used_30d,
    u.power_features_used_30d,
    u.most_used_features,
    u.mobile_app_usage_30d,
    u.mobile_usage_percentage,
    u.failed_login_attempts_7d,
    u.api_calls_30d,
    u.data_exported_mb_30d,
    u.reports_generated_30d,
    u.alerts_configured,
    u.integrations_active,
    u.last_feature_adopted,
    u.last_feature_adoption_date,
    u.time_to_first_value_minutes,
    u.days_to_habit_formation,
    u.engagement_score,
    u.engagement_trend,
    u.influence_score,
    u.knowledge_sharing_score,
    u.is_champion_user,
    u.needs_training,
    u.training_completed_modules,
    u.certification_status,
    u.support_tickets_created_30d,
    u.last_support_ticket_date,
    u.satisfaction_score,
    u.predicted_churn_risk,
    u.predicted_expansion_value,
    u.recommended_features,
    u.last_updated
FROM entity.entity_users u
LEFT JOIN normalized.account_id_mapping m 
    ON u.account_id = m.user_account_id
    OR u.account_id::VARCHAR = m.customer_account_id;

-- Add indexes
CREATE INDEX idx_norm_user_account ON normalized.users(account_id);
CREATE INDEX idx_norm_user_role ON normalized.users(role_type_standardized);
CREATE INDEX idx_norm_user_status ON normalized.users(user_status);

-- Normalized Locations
DROP TABLE IF EXISTS normalized.locations CASCADE;
CREATE TABLE normalized.locations AS
SELECT 
    l.location_id,
    l.location_key,
    COALESCE(
        m.normalized_account_id, 
        'ACC' || LPAD(l.account_id::VARCHAR, 10, '0')
    ) as account_id,
    l.location_name,
    l.location_type,
    l.address,
    l.city,
    l.state,
    l.postal_code,
    l.country,
    l.latitude,
    l.longitude,
    l.timezone,
    l.location_status,
    l.created_at,
    l.activated_at,
    l.deactivated_at,
    l.days_active,
    l.business_hours,
    l.capacity,
    l.current_occupancy,
    l.square_footage,
    l.device_count,
    l.active_device_count,
    l.device_health_avg,
    l.last_device_sync,
    l.user_count,
    l.active_user_count,
    l.primary_contact_user_id,
    l.total_events_30d,
    l.daily_events_avg,
    l.peak_hour_events,
    l.off_hours_usage_pct,
    l.revenue_per_location,
    l.transactions_30d,
    l.avg_transaction_value,
    l.operational_health_score,
    l.compliance_score,
    l.safety_incidents_30d,
    l.maintenance_tickets_open,
    l.last_maintenance_date,
    l.wifi_strength_avg,
    l.network_uptime_30d,
    l.power_consumption_kwh_30d,
    l.environmental_score,
    l.customer_rating,
    l.review_count,
    l.last_review_date,
    l.competitor_distance_km,
    l.foot_traffic_index,
    l.seasonality_factor,
    l.expansion_potential,
    l.risk_score,
    l.last_updated
FROM entity.entity_locations l
LEFT JOIN normalized.account_id_mapping m 
    ON l.account_id = m.location_account_id
    OR l.account_id::VARCHAR = m.customer_account_id;

-- Add indexes
CREATE INDEX idx_norm_loc_account ON normalized.locations(account_id);
CREATE INDEX idx_norm_loc_status ON normalized.locations(location_status);
CREATE INDEX idx_norm_loc_type ON normalized.locations(location_type);

-- Normalized Devices (with location relationships fixed)
DROP TABLE IF EXISTS normalized.devices CASCADE;
CREATE TABLE normalized.devices AS
SELECT 
    d.device_id,
    d.device_key,
    d.device_name,
    l.account_id, -- Get account_id from normalized locations
    d.location_id,
    d.device_type,
    d.device_category,
    d.manufacturer,
    d.model,
    d.serial_number,
    d.firmware_version,
    d.hardware_version,
    d.device_installed_date,
    d.device_activated_date,
    d.device_deactivated_date,
    d.warranty_expiry_date,
    d.device_age_days,
    d.operational_status,
    d.connectivity_status,
    d.last_seen_at,
    d.minutes_since_last_seen,
    d.total_events_30d,
    d.usage_events_30d,
    d.alert_events_30d,
    d.error_events_30d,
    d.maintenance_events_30d,
    d.avg_events_per_day,
    d.peak_hour_events,
    d.temperature_current,
    d.temperature_avg_24h,
    d.temperature_max_24h,
    d.temperature_min_24h,
    d.high_temp_events_30d,
    d.low_temp_events_30d,
    d.pressure_current,
    d.pressure_avg_24h,
    d.high_pressure_events_30d,
    d.low_pressure_events_30d,
    d.usage_minutes_30d,
    d.active_hours_30d,
    d.utilization_percentage,
    d.power_consumption_kwh_30d,
    d.network_latency_ms_avg,
    d.packet_loss_rate,
    d.bandwidth_usage_gb_30d,
    d.cpu_usage_avg,
    d.memory_usage_avg,
    d.storage_usage_pct,
    d.uptime_percentage_30d,
    d.downtime_minutes_30d,
    d.restart_count_30d,
    d.mtbf_hours,
    d.mttr_hours,
    d.overall_health_score,
    d.performance_score,
    d.reliability_score,
    d.uptime_score,
    d.alert_score,
    d.failure_prediction_score,
    d.maintenance_due_days,
    d.last_maintenance_date,
    d.maintenance_cost_total,
    d.estimated_replacement_date,
    d.compliance_certified,
    d.last_audit_date,
    d.security_patch_current,
    d.custom_attributes,
    d.last_updated
FROM entity.entity_devices d
LEFT JOIN normalized.locations l ON d.location_id::VARCHAR = l.location_id::VARCHAR;

-- Add indexes
CREATE INDEX idx_norm_dev_account ON normalized.devices(account_id);
CREATE INDEX idx_norm_dev_location ON normalized.devices(location_id);
CREATE INDEX idx_norm_dev_status ON normalized.devices(operational_status);
CREATE INDEX idx_norm_dev_type ON normalized.devices(device_type);

-- ========================================
-- Update Cross-References
-- ========================================

-- Update customer revenue from subscriptions
UPDATE normalized.customers c
SET 
    monthly_recurring_revenue = sub_revenue.total_mrr,
    annual_recurring_revenue = sub_revenue.total_arr,
    active_subscriptions = sub_revenue.active_count,
    total_subscriptions = sub_revenue.total_count
FROM (
    SELECT 
        account_id,
        SUM(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN monthly_recurring_revenue ELSE 0 END) as total_mrr,
        SUM(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN annual_recurring_revenue ELSE 0 END) as total_arr,
        COUNT(CASE WHEN subscription_status IN ('Active', 'active') 
            THEN 1 END) as active_count,
        COUNT(*) as total_count
    FROM normalized.subscriptions
    GROUP BY account_id
) sub_revenue
WHERE c.account_id = sub_revenue.account_id;

-- Update customer device counts
UPDATE normalized.customers c
SET 
    total_devices = device_counts.total_devices,
    healthy_devices = device_counts.healthy_devices,
    avg_device_uptime_30d = device_counts.avg_uptime
FROM (
    SELECT 
        account_id,
        COUNT(*) as total_devices,
        COUNT(CASE WHEN overall_health_score >= 70 THEN 1 END) as healthy_devices,
        AVG(uptime_percentage_30d) as avg_uptime
    FROM normalized.devices
    GROUP BY account_id
) device_counts
WHERE c.account_id = device_counts.account_id;

-- Update customer user counts
UPDATE normalized.customers c
SET 
    total_users = user_counts.total_users,
    active_users_30d = user_counts.active_users,
    avg_user_engagement_score = user_counts.avg_engagement
FROM (
    SELECT 
        account_id,
        COUNT(*) as total_users,
        COUNT(CASE WHEN days_since_last_login <= 30 THEN 1 END) as active_users,
        AVG(engagement_score) as avg_engagement
    FROM normalized.users
    GROUP BY account_id
) user_counts
WHERE c.account_id = user_counts.account_id;

-- Update customer location counts
UPDATE normalized.customers c
SET 
    total_locations = location_counts.total_locations,
    active_locations = location_counts.active_locations,
    avg_location_health_score = location_counts.avg_health
FROM (
    SELECT 
        account_id,
        COUNT(*) as total_locations,
        COUNT(CASE WHEN location_status = 'active' THEN 1 END) as active_locations,
        AVG(operational_health_score) as avg_health
    FROM normalized.locations
    GROUP BY account_id
) location_counts
WHERE c.account_id = location_counts.account_id;

-- ========================================
-- Create Validation Report
-- ========================================

CREATE OR REPLACE VIEW normalized.reconciliation_report AS
WITH customer_stats AS (
    SELECT 
        COUNT(*) as total_customers,
        COUNT(CASE WHEN monthly_recurring_revenue > 0 THEN 1 END) as customers_with_revenue,
        SUM(monthly_recurring_revenue) as total_mrr
    FROM normalized.customers
),
subscription_stats AS (
    SELECT 
        COUNT(*) as total_subscriptions,
        COUNT(DISTINCT account_id) as accounts_with_subscriptions,
        COUNT(CASE WHEN account_id LIKE 'ACC_ORPHANED_%' THEN 1 END) as orphaned_subscriptions
    FROM normalized.subscriptions
),
relationship_stats AS (
    SELECT 
        COUNT(DISTINCT c.account_id) as customers_with_valid_relationships
    FROM normalized.customers c
    WHERE EXISTS (SELECT 1 FROM normalized.subscriptions s WHERE s.account_id = c.account_id)
       OR EXISTS (SELECT 1 FROM normalized.users u WHERE u.account_id = c.account_id)
       OR EXISTS (SELECT 1 FROM normalized.locations l WHERE l.account_id = c.account_id)
       OR EXISTS (SELECT 1 FROM normalized.devices d WHERE d.account_id = c.account_id)
)
SELECT 
    'Customers' as metric,
    c.total_customers::VARCHAR as value
FROM customer_stats c
UNION ALL
SELECT 
    'Customers with Revenue',
    c.customers_with_revenue || ' (' || 
    ROUND(100.0 * c.customers_with_revenue / c.total_customers, 2) || '%)'
FROM customer_stats c
UNION ALL
SELECT 
    'Total MRR',
    '$' || TO_CHAR(c.total_mrr, 'FM999,999.00')
FROM customer_stats c
UNION ALL
SELECT 
    'Subscriptions Linked',
    s.accounts_with_subscriptions || ' accounts'
FROM subscription_stats s
UNION ALL
SELECT 
    'Orphaned Subscriptions',
    s.orphaned_subscriptions::VARCHAR
FROM subscription_stats s
UNION ALL
SELECT 
    'Valid Relationships',
    r.customers_with_valid_relationships || ' customers'
FROM relationship_stats r;

-- Display the report
SELECT * FROM normalized.reconciliation_report;
