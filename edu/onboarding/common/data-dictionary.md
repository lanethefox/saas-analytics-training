# Data Dictionary

This comprehensive dictionary defines all entities, tables, and key fields in the SaaS Analytics Platform.

## 📊 Entity Definitions

### 1. Customer Entity (`entity_customers`)

**Description**: Represents a B2B customer account (company) using the platform.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `customer_id` | STRING | Unique customer identifier | "cust_abc123" |
| `company_name` | STRING | Legal company name | "Joe's Bar & Grill" |
| `customer_tier` | STRING | Customer segment | "Enterprise", "Mid-Market", "SMB" |
| `customer_industry` | STRING | Industry classification | "Restaurant", "Bar", "Brewery" |
| `customer_status` | STRING | Account status | "Active", "Churned", "Suspended" |
| `customer_health_score` | FLOAT | Composite health (0-100) | 85.5 |
| `churn_risk_score` | FLOAT | Churn probability (0-100) | 15.2 |
| `monthly_recurring_revenue` | FLOAT | Current MRR in USD | 2500.00 |
| `annual_recurring_revenue` | FLOAT | Current ARR in USD | 30000.00 |
| `lifetime_value` | FLOAT | Total revenue to date | 75000.00 |
| `first_subscription_date` | DATE | Initial subscription | "2022-01-15" |
| `months_since_first_subscription` | INT | Tenure in months | 24 |
| `total_users` | INT | Active user count | 25 |
| `total_locations` | INT | Number of venues | 3 |
| `total_devices` | INT | Active device count | 12 |
| `is_active` | BOOLEAN | Currently active | true |
| `created_at` | TIMESTAMP | Record creation | "2022-01-15 10:30:00" |
| `updated_at` | TIMESTAMP | Last update | "2024-01-20 14:45:00" |

### 2. User Entity (`entity_users`)

**Description**: Individual users within customer accounts who access the platform.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `user_id` | STRING | Unique user identifier | "user_xyz789" |
| `customer_id` | STRING | Parent customer ID | "cust_abc123" |
| `email` | STRING | User email (hashed) | "hash_123abc" |
| `user_role` | STRING | Platform role | "Admin", "Manager", "Viewer" |
| `user_status` | STRING | Account status | "Active", "Inactive", "Invited" |
| `engagement_score` | FLOAT | Engagement level (0-100) | 72.3 |
| `user_engagement_tier` | STRING | Engagement segment | "Power User", "Regular", "Casual" |
| `days_since_last_login` | INT | Inactivity period | 2 |
| `total_sessions_30d` | INT | Recent session count | 45 |
| `features_used_30d` | INT | Distinct features used | 8 |
| `last_active_date` | DATE | Last activity | "2024-01-18" |
| `created_at` | TIMESTAMP | User creation | "2023-06-10 09:00:00" |

### 3. Device Entity (`entity_devices`)

**Description**: IoT-enabled tap devices installed at customer locations.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `device_id` | STRING | Unique device identifier | "dev_tap001" |
| `customer_id` | STRING | Owner customer | "cust_abc123" |
| `location_id` | STRING | Installation location | "loc_venue1" |
| `device_type` | STRING | Device model | "TapMaster Pro", "TapMaster Lite" |
| `device_status` | STRING | Operational status | "Online", "Offline", "Maintenance" |
| `overall_health_score` | FLOAT | Device health (0-100) | 92.1 |
| `uptime_percentage_30d` | FLOAT | Recent uptime % | 99.5 |
| `total_volume_liters_30d` | FLOAT | Volume dispensed | 1250.5 |
| `maintenance_score` | FLOAT | Maintenance need (0-100) | 15.0 |
| `last_maintenance_date` | DATE | Last service date | "2023-12-15" |
| `estimated_revenue_30d` | FLOAT | Revenue contribution | 5000.00 |
| `installation_date` | DATE | Install date | "2022-03-20" |

### 4. Location Entity (`entity_locations`)

**Description**: Physical venues where devices are installed.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `location_id` | STRING | Unique location ID | "loc_venue1" |
| `customer_id` | STRING | Owner customer | "cust_abc123" |
| `location_name` | STRING | Venue name | "Downtown Location" |
| `location_type` | STRING | Venue type | "Bar", "Restaurant", "Stadium" |
| `address` | STRING | Physical address | "123 Main St" |
| `city` | STRING | City | "San Francisco" |
| `state` | STRING | State/Province | "CA" |
| `country` | STRING | Country code | "US" |
| `timezone` | STRING | Local timezone | "America/Los_Angeles" |
| `active_devices` | INT | Device count | 4 |
| `total_revenue_30d` | FLOAT | Location revenue | 20000.00 |
| `is_active` | BOOLEAN | Currently operating | true |

### 5. Subscription Entity (`entity_subscriptions`)

**Description**: Customer subscription details and billing information.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `subscription_id` | STRING | Unique subscription ID | "sub_monthly123" |
| `customer_id` | STRING | Customer reference | "cust_abc123" |
| `subscription_plan` | STRING | Plan name | "Professional", "Enterprise" |
| `billing_period` | STRING | Billing frequency | "Monthly", "Annual" |
| `subscription_status` | STRING | Current status | "Active", "Cancelled", "Past Due" |
| `monthly_recurring_revenue` | FLOAT | MRR value | 2500.00 |
| `start_date` | DATE | Subscription start | "2022-01-15" |
| `end_date` | DATE | Cancellation date | null |
| `renewal_date` | DATE | Next renewal | "2024-02-15" |
| `expansion_revenue` | FLOAT | Upsell amount | 500.00 |
| `contraction_revenue` | FLOAT | Downgrade amount | 0.00 |

### 6. Campaign Entity (`entity_campaigns`)

**Description**: Marketing campaigns and their performance metrics.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `campaign_id` | STRING | Unique campaign ID | "camp_summer2024" |
| `campaign_name` | STRING | Campaign name | "Summer Promotion 2024" |
| `campaign_type` | STRING | Campaign category | "Email", "Paid Social", "Content" |
| `channel` | STRING | Marketing channel | "Facebook", "Google", "Email" |
| `start_date` | DATE | Campaign start | "2024-06-01" |
| `end_date` | DATE | Campaign end | "2024-08-31" |
| `total_spend` | FLOAT | Total cost | 50000.00 |
| `impressions` | INT | Total impressions | 2500000 |
| `clicks` | INT | Total clicks | 75000 |
| `conversions` | INT | Total conversions | 500 |
| `revenue_attributed` | FLOAT | Revenue generated | 250000.00 |
| `roi` | FLOAT | Return on investment | 4.0 |

### 7. Feature Entity (`entity_features`)

**Description**: Product features and their adoption metrics.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `feature_id` | STRING | Unique feature ID | "feat_reporting" |
| `feature_name` | STRING | Feature name | "Advanced Reporting" |
| `feature_category` | STRING | Feature group | "Analytics", "Operations", "Admin" |
| `customer_id` | STRING | Customer using feature | "cust_abc123" |
| `adoption_rate` | FLOAT | % of users adopted | 0.75 |
| `usage_intensity_score` | FLOAT | Usage depth (0-100) | 82.5 |
| `retention_impact_score` | FLOAT | Impact on retention | 15.2 |
| `time_to_first_use_days` | FLOAT | Adoption speed | 3.5 |
| `usage_frequency` | STRING | Usage pattern | "Daily", "Weekly", "Monthly" |
| `is_core_feature` | BOOLEAN | Core feature flag | true |

## 📋 Metric Tables

### Sales Metrics (`metrics.sales`)

| Field | Type | Description |
|-------|------|-------------|
| `date` | DATE | Metric date |
| `sales_rep_id` | STRING | Sales representative |
| `total_pipeline_value` | FLOAT | Open opportunity value |
| `qualified_pipeline_value` | FLOAT | Stage 3+ opportunities |
| `deals_won_mtd` | INT | Closed deals this month |
| `revenue_closed_mtd` | FLOAT | Revenue this month |
| `win_rate` | FLOAT | Win percentage |
| `avg_deal_size` | FLOAT | Average deal value |
| `avg_sales_cycle_days` | FLOAT | Sales cycle length |

### Customer Success Metrics (`metrics.customer_success`)

| Field | Type | Description |
|-------|------|-------------|
| `date` | DATE | Metric date |
| `customer_id` | STRING | Customer reference |
| `composite_success_score` | FLOAT | Overall success metric |
| `health_trend_30d` | FLOAT | Health score change |
| `support_tickets_30d` | INT | Recent ticket count |
| `ticket_resolution_rate` | FLOAT | % tickets resolved |
| `user_activation_rate` | FLOAT | % users activated |
| `feature_adoption_rate` | FLOAT | % features adopted |

### Marketing Metrics (`metrics.marketing`)

| Field | Type | Description |
|-------|------|-------------|
| `date` | DATE | Metric date |
| `overall_roi` | FLOAT | Blended ROI |
| `total_ad_spend_active` | FLOAT | Active campaign spend |
| `total_mqls` | INT | Marketing qualified leads |
| `mql_conversion_rate` | FLOAT | MQL to SQL rate |
| `cost_per_mql` | FLOAT | Cost per MQL |
| `cost_per_acquisition` | FLOAT | Customer acquisition cost |

### Product Analytics Metrics (`metrics.product_analytics`)

| Field | Type | Description |
|-------|------|-------------|
| `date` | DATE | Metric date |
| `daily_active_users` | INT | DAU count |
| `weekly_active_users` | INT | WAU count |
| `monthly_active_users` | INT | MAU count |
| `dau_mau_ratio` | FLOAT | Stickiness ratio |
| `avg_session_duration_minutes` | FLOAT | Session length |
| `power_user_percentage` | FLOAT | % power users |

## 🔄 Table Relationships

### Primary Relationships
```
customers (1) ← → (n) users
customers (1) ← → (n) locations
customers (1) ← → (n) devices
customers (1) ← → (n) subscriptions
locations (1) ← → (n) devices
campaigns (n) ← → (n) customers (via attribution)
features (n) ← → (n) customers (via adoption)
```

### Join Patterns
```sql
-- Customer to Users
FROM entity.entity_customers c
JOIN entity.entity_users u ON c.customer_id = u.customer_id

-- Customer to Devices (via Location)
FROM entity.entity_customers c
JOIN entity.entity_locations l ON c.customer_id = l.customer_id
JOIN entity.entity_devices d ON l.location_id = d.location_id

-- Customer to Metrics
FROM entity.entity_customers c
JOIN metrics.customer_success cs ON c.customer_id = cs.customer_id
```

## 📐 Data Types & Constraints

### Standard Data Types
- **STRING**: UTF-8 encoded, max 255 chars
- **FLOAT**: 64-bit floating point
- **INT**: 64-bit integer
- **BOOLEAN**: true/false
- **DATE**: YYYY-MM-DD format
- **TIMESTAMP**: YYYY-MM-DD HH:MM:SS UTC

### Naming Conventions
- **IDs**: `{entity}_id` format
- **Dates**: `{action}_date` format
- **Metrics**: `{metric}_{timeframe}` format
- **Flags**: `is_{condition}` format
- **Counts**: `total_{entity}` or `{entity}_count`

### Data Quality Rules
- All IDs must be non-null
- Scores must be between 0-100
- Percentages stored as decimals (0.75 = 75%)
- Currency in USD with 2 decimal places
- Dates cannot be future dates
- Timestamps in UTC timezone