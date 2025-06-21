# Superset Quick Reference Guide

## 🔐 Access Information
- **URL**: http://localhost:8088
- **Username**: admin
- **Password**: admin_password_2024
- **Database**: saas_platform_dev (should already be configured)

## 📊 Key Tables for Dashboards

### Core Business Tables
```sql
-- Customer accounts with MRR
SELECT * FROM raw.app_database_accounts;

-- Locations with coordinates and timezones  
SELECT * FROM raw.app_database_locations;

-- Users with roles and permissions
SELECT * FROM raw.app_database_users;

-- IoT devices with status and serial numbers
SELECT * FROM raw.app_database_devices;

-- Subscriptions with metadata
SELECT * FROM raw.app_database_subscriptions;
```

### Financial/Billing Tables
```sql
-- Stripe billing data
SELECT * FROM raw.stripe_invoices;
SELECT * FROM raw.stripe_charges;
SELECT * FROM raw.stripe_subscriptions;
```

### CRM Tables
```sql
-- HubSpot data
SELECT * FROM raw.hubspot_companies;
SELECT * FROM raw.hubspot_deals;
SELECT * FROM raw.hubspot_tickets;
```

### Activity Tables
```sql
-- User activity
SELECT * FROM raw.app_database_user_sessions;
SELECT * FROM raw.app_database_page_views;
SELECT * FROM raw.app_database_feature_usage;

-- IoT events
SELECT * FROM raw.app_database_tap_events;
```

## 📈 Quick Chart Ideas

### 1. Revenue Dashboard
```sql
-- MRR by subscription tier
SELECT 
    plan_name,
    COUNT(*) as customer_count,
    SUM(monthly_price) as total_mrr
FROM raw.app_database_subscriptions
WHERE status = 'active'
GROUP BY plan_name;

-- Revenue trend over time
SELECT 
    DATE_TRUNC('month', created_date) as month,
    SUM(amount_paid) as revenue
FROM raw.stripe_invoices
WHERE status = 'paid'
GROUP BY month
ORDER BY month;
```

### 2. Operations Dashboard
```sql
-- Device status distribution
SELECT 
    device_type,
    status,
    COUNT(*) as device_count
FROM raw.app_database_devices
GROUP BY device_type, status;

-- Beer volume by location (from tap events)
SELECT 
    l.name as location_name,
    l.state,
    COUNT(CASE WHEN t.event_type = 'pour' THEN 1 END) as pour_count,
    SUM(CASE 
        WHEN t.event_type = 'pour' 
        THEN (t.metrics->>'pour_ounces')::float 
        ELSE 0 
    END) as total_ounces
FROM raw.app_database_tap_events t
JOIN raw.app_database_locations l ON t.location_id = l.id
GROUP BY l.name, l.state
ORDER BY total_ounces DESC;
```

### 3. Customer Success Dashboard
```sql
-- Account health by subscription tier
SELECT 
    s.plan_name,
    AVG((s.metadata->'account_health'->>'feature_adoption_score')::float) as avg_adoption,
    AVG((s.metadata->'account_health'->>'nps_score')::int) as avg_nps
FROM raw.app_database_subscriptions s
WHERE s.status = 'active'
GROUP BY s.plan_name;

-- Support ticket resolution
SELECT 
    hs_ticket_priority as priority,
    COUNT(*) as total_tickets,
    SUM(CASE WHEN hs_pipeline_stage = 'closed' THEN 1 ELSE 0 END) as resolved,
    ROUND(100.0 * SUM(CASE WHEN hs_pipeline_stage = 'closed' THEN 1 ELSE 0 END) / COUNT(*), 1) as resolution_rate
FROM raw.hubspot_tickets
GROUP BY hs_ticket_priority;
```

### 4. Geographic Analysis
```sql
-- Customers by state with coordinates
SELECT 
    l.state,
    COUNT(DISTINCT l.customer_id) as customers,
    COUNT(l.id) as locations,
    AVG(l.latitude) as center_lat,
    AVG(l.longitude) as center_lng
FROM raw.app_database_locations l
GROUP BY l.state
ORDER BY customers DESC;
```

## 🎨 Visualization Tips

1. **Time Series**: Use Line Charts for trends over time
2. **Geographic**: Use Map visualizations with lat/lng coordinates
3. **Distributions**: Use Pie/Donut charts for status breakdowns
4. **Comparisons**: Use Bar charts for metrics by category
5. **KPIs**: Use Big Number charts for key metrics

## 🔧 Advanced Features

### Using JSON Data
Many tables have JSON/JSONB columns with rich data:
```sql
-- Extract from subscription metadata
SELECT 
    customer_id,
    metadata->>'tier_details' as tier_info,
    (metadata->'usage_tracking'->>'current_locations')::int as locations_used
FROM raw.app_database_subscriptions;

-- Extract from user permissions
SELECT 
    email,
    role,
    permissions->'billing'->>'view' as can_view_billing,
    permissions->'users'->>'manage_roles' as can_manage_users
FROM raw.app_database_users;
```

### Time Zone Handling
```sql
-- Convert timestamps to location timezone
SELECT 
    t.timestamp AT TIME ZONE 'UTC' AT TIME ZONE l.timezone as local_time,
    t.event_type,
    l.name as location_name
FROM raw.app_database_tap_events t
JOIN raw.app_database_locations l ON t.location_id = l.id;
```

## 🚀 Getting Started

1. Log into Superset
2. Navigate to SQL Lab to test queries
3. Create a new dashboard
4. Add charts using the queries above
5. Configure filters and refresh schedules

Remember: All data is in the `raw` schema!