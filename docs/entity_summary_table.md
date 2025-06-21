# Entity Summary Reference Table

## Core Entity Classification Matrix

| Entity | Table Name | Primary Key | Grain | Entity Type | SCD Type | Volume | Key Relationships |
|--------|------------|-------------|-------|-------------|----------|--------|-------------------|
| **Account** | `accounts` | `account_id` (UUID) | One per customer organization | Master Dimension | Type 2 | Low | 1:N → Locations, Users, Subscriptions, Devices |
| **Location** | `locations` | `location_id` (UUID) | One per physical business location | Dimension | Type 1/2 Hybrid | Low-Medium | N:1 → Account; 1:N → Devices, Users |
| **User** | `users` | `user_id` (UUID) | One per individual user | Dimension | Type 2 | Medium | N:1 → Account, Location; 1:N → Sessions, Feature Usage |
| **Device** | `devices` | `device_id` (UUID) | One per IoT hardware device | Dimension | Type 1 | Medium | N:1 → Location, Account; 1:N → Tap Events |
| **Subscription** | `subscriptions` | `subscription_id` (UUID) | One per subscription period | Dimension | Type 2 | Low-Medium | N:1 → Account |
| **Tap Events** | `tap_events` | `tap_event_id` (UUID) | One per device sensor event | Fact Table | N/A | Very High | N:1 → Device, Location, Account |
| **User Sessions** | `user_sessions` | `session_id` (UUID) | One per user login session | Fact Table | N/A | High | N:1 → User, Account; 1:N → Page Views |
| **Page Views** | `page_views` | `page_view_id` (UUID) | One per page view | Fact Table | N/A | Very High | N:1 → Session, User |
| **Feature Usage** | `feature_usage` | `usage_id` (UUID) | One per feature interaction | Fact Table | N/A | High | N:1 → User, Account |
| **Stripe Customer** | `stripe_customers` | `id` (Stripe ID) | One per Stripe customer | External Dimension | Type 1 | Low | 1:N → Stripe Subscriptions, Invoices, Charges |
| **Stripe Subscription** | `stripe_subscriptions` | `id` (Stripe ID) | One per Stripe subscription | External Dimension | Type 1 | Low-Medium | N:1 → Stripe Customer; 1:N → Invoices |
| **Stripe Invoice** | `stripe_invoices` | `id` (Stripe ID) | One per billing invoice | Fact Table | N/A | Medium | N:1 → Customer, Subscription; 1:N → Charges |
| **Stripe Charge** | `stripe_charges` | `id` (Stripe ID) | One per payment transaction | Fact Table | N/A | Medium | N:1 → Customer, Invoice |
| **Marketing Qualified Lead** | `marketing_qualified_leads` | `lead_id` (UUID) | One per qualified prospect | Dimension | Type 2 | Medium | 1:N → Attribution Touchpoints |
| **Attribution Touchpoints** | `attribution_touchpoints` | `touchpoint_id` (UUID) | One per marketing touchpoint | Fact Table | N/A | High | N:1 → User, Account, Session |
| **Campaign Performance** | `google_ads_campaign_performance` | (`campaign_id`, `date`) | One per campaign per day | Fact Table | N/A | Medium | Time-series aggregated data |
| **HubSpot Companies** | `hubspot_companies` | `id` (HubSpot ID) | One per CRM company | External Dimension | Type 1 | Low | Semi-structured CRM data |
| **HubSpot Contacts** | `hubspot_contacts` | `id` (HubSpot ID) | One per CRM contact | External Dimension | Type 1 | Medium | Semi-structured CRM data |
| **HubSpot Deals** | `hubspot_deals` | `id` (HubSpot ID) | One per sales opportunity | External Dimension | Type 1 | Medium | Semi-structured CRM data |
| **Email Events** | `iterable_email_events` | Composite Key | One per email interaction | Fact Table | N/A | High | Email marketing engagement |

## Key Metrics Foundation by Entity

### Revenue & Billing Metrics
| Metric | Primary Tables | Calculation Pattern |
|--------|----------------|-------------------|
| **Monthly Recurring Revenue (MRR)** | `subscriptions`, `stripe_subscriptions` | Sum of active subscription values per month |
| **Annual Recurring Revenue (ARR)** | `subscriptions` | MRR × 12 for annual plans |
| **Customer Acquisition Cost (CAC)** | `attribution_touchpoints`, `*_campaign_performance` | Marketing spend ÷ new accounts |
| **Customer Lifetime Value (CLV)** | `accounts`, `subscriptions`, `stripe_invoices` | Average revenue per account × retention period |
| **Churn Rate** | `accounts`, `subscriptions` | Accounts lost ÷ total accounts (period over period) |
| **Average Revenue Per User (ARPU)** | `stripe_invoices`, `accounts` | Total revenue ÷ active accounts |

### Product & Engagement Metrics
| Metric | Primary Tables | Calculation Pattern |
|--------|----------------|-------------------|
| **Daily Active Users (DAU)** | `user_sessions` | Distinct users with sessions per day |
| **Monthly Active Users (MAU)** | `user_sessions` | Distinct users with sessions per month |
| **Feature Adoption Rate** | `feature_usage`, `users` | Users using feature ÷ total users |
| **Session Duration** | `user_sessions` | Average of (session_end - session_start) |
| **Page Views per Session** | `page_views`, `user_sessions` | Count of page views ÷ sessions |
| **Feature Success Rate** | `feature_usage` | Successful interactions ÷ total interactions |

### Operational & IoT Metrics
| Metric | Primary Tables | Calculation Pattern |
|--------|----------------|-------------------|
| **Device Health Score** | `devices`, `tap_events` | Based on heartbeat frequency and event patterns |
| **Pour Volume Analytics** | `tap_events` | Aggregated volume measurements by time/location |
| **Device Utilization Rate** | `tap_events`, `devices` | Active devices ÷ total devices |
| **Maintenance Efficiency** | `devices` | Planned vs. unplanned maintenance events |
| **Location Performance** | `tap_events`, `locations` | Aggregated activity metrics per location |

### Marketing & Attribution Metrics
| Metric | Primary Tables | Calculation Pattern |
|--------|----------------|-------------------|
| **Lead Conversion Rate** | `marketing_qualified_leads`, `accounts` | Converted leads ÷ total leads |
| **Marketing Attribution** | `attribution_touchpoints`, `accounts` | Revenue attributed to marketing channels |
| **Campaign ROI** | `*_campaign_performance`, `attribution_touchpoints` | Revenue generated ÷ campaign spend |
| **Email Engagement Rate** | `iterable_email_events` | Opens + clicks ÷ emails sent |
| **Cost Per Lead (CPL)** | `*_campaign_performance`, `marketing_qualified_leads` | Campaign spend ÷ leads generated |

## Data Volume & Performance Considerations

### High-Volume Tables (Partitioning Recommended)
- **`tap_events`**: Partition by `event_timestamp` (monthly)
- **`page_views`**: Partition by `timestamp` (monthly)  
- **`user_sessions`**: Partition by `session_start` (monthly)
- **`feature_usage`**: Partition by `usage_timestamp` (monthly)
- **`iterable_email_events`**: Partition by `created_at` (monthly)

### Index Strategy by Entity Type
- **Dimension Tables**: Primary key + status fields + frequently filtered attributes
- **Fact Tables**: Foreign keys + timestamp fields + commonly aggregated measures
- **External Integration Tables**: Native IDs + status fields + JSON property indexes (GIN)

### Slowly Changing Dimension Implementation
- **Type 1 (Overwrite)**: Device status, external system data
- **Type 2 (Historical Tracking)**: Account status/tier, user roles, subscription changes
- **Type 6 (Hybrid)**: Current + historical versions for frequently accessed dimensions

This entity model provides a comprehensive foundation for analytical workloads while maintaining operational efficiency and supporting both real-time and batch processing patterns.

