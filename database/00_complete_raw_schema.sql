-- =====================================================
-- SaaS Data Platform - Complete Raw Schema Definition
-- =====================================================
-- Creates all tables needed for comprehensive synthetic data loading
-- Optimized for Entity-Centric Modeling with multi-source integration
-- Target: saas_platform_dev database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- CREATE RAW SCHEMA
-- =====================================================
CREATE SCHEMA IF NOT EXISTS raw;

-- =====================================================
-- APP DATABASE TABLES (Core Business Entities)
-- =====================================================

-- Accounts (Companies/Customers)
CREATE TABLE IF NOT EXISTS raw.accounts (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subscription_tier VARCHAR(50),
    mrr DECIMAL(10,2),
    employee_count INTEGER,
    is_active BOOLEAN DEFAULT true
);

-- Locations (Physical business locations)
CREATE TABLE IF NOT EXISTS raw.locations (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'US',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    location_type VARCHAR(50)
);

-- Users (Platform users)
CREATE TABLE IF NOT EXISTS raw.users (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    permissions TEXT
);

-- Devices (IoT devices at locations)
CREATE TABLE IF NOT EXISTS raw.devices (
    id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    serial_number VARCHAR(100),
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    installed_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    status VARCHAR(50) DEFAULT 'online'
);

-- Subscriptions (Account subscription plans)
CREATE TABLE IF NOT EXISTS raw.subscriptions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    plan_name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    mrr DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tap Events (IoT sensor data - high volume)
CREATE TABLE IF NOT EXISTS raw.tap_events (
    id VARCHAR(50) PRIMARY KEY,
    device_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    tap_type VARCHAR(50),
    volume_ml DECIMAL(10,2),
    timestamp TIMESTAMP NOT NULL,
    product_name VARCHAR(100),
    product_category VARCHAR(50),
    temperature_c DECIMAL(5,2),
    duration_seconds DECIMAL(10,2)
);

-- User Sessions (Web application usage)
CREATE TABLE IF NOT EXISTS raw.user_sessions (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    duration_seconds INTEGER,
    page_views INTEGER DEFAULT 0,
    actions_taken INTEGER DEFAULT 0,
    device_type VARCHAR(50),
    browser VARCHAR(50),
    ip_address VARCHAR(50)
);

-- Page Views (Detailed web analytics)
CREATE TABLE IF NOT EXISTS raw.page_views (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    page_url VARCHAR(500),
    page_title VARCHAR(255),
    timestamp TIMESTAMP NOT NULL,
    time_on_page_seconds INTEGER,
    referrer_url VARCHAR(500),
    exit_page BOOLEAN DEFAULT false
);

-- Feature Usage (Product analytics)
CREATE TABLE IF NOT EXISTS raw.feature_usage (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    feature_name VARCHAR(100),
    feature_category VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    usage_count INTEGER DEFAULT 1,
    success BOOLEAN DEFAULT true,
    error_message VARCHAR(500)
);

-- =====================================================
-- STRIPE TABLES (Billing & Payments)
-- =====================================================

-- Stripe Customers
CREATE TABLE IF NOT EXISTS raw.stripe_customers (
    id VARCHAR(50) PRIMARY KEY,
    account_id INTEGER,
    email VARCHAR(255),
    name VARCHAR(255),
    created TIMESTAMP NOT NULL,
    currency VARCHAR(10) DEFAULT 'usd',
    default_source VARCHAR(50),
    delinquent BOOLEAN DEFAULT false,
    balance INTEGER DEFAULT 0,
    metadata TEXT
);

-- Stripe Pricing Plans
CREATE TABLE IF NOT EXISTS raw.stripe_prices (
    id VARCHAR(50) PRIMARY KEY,
    product VARCHAR(50),
    active BOOLEAN DEFAULT true,
    currency VARCHAR(10) DEFAULT 'usd',
    unit_amount INTEGER NOT NULL,
    type VARCHAR(20) DEFAULT 'recurring',
    recurring_interval VARCHAR(20),
    recurring_interval_count INTEGER DEFAULT 1,
    nickname VARCHAR(100),
    created TIMESTAMP NOT NULL
);

-- Stripe Subscriptions
CREATE TABLE IF NOT EXISTS raw.stripe_subscriptions (
    id VARCHAR(50) PRIMARY KEY,
    customer VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    cancel_at TIMESTAMP,
    canceled_at TIMESTAMP,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP
);

-- Stripe Subscription Items
CREATE TABLE IF NOT EXISTS raw.stripe_subscription_items (
    id VARCHAR(50) PRIMARY KEY,
    subscription VARCHAR(50) NOT NULL,
    price VARCHAR(50) NOT NULL,
    quantity INTEGER DEFAULT 1,
    created TIMESTAMP NOT NULL,
    metadata TEXT
);

-- Stripe Invoices
CREATE TABLE IF NOT EXISTS raw.stripe_invoices (
    id VARCHAR(50) PRIMARY KEY,
    customer VARCHAR(50) NOT NULL,
    subscription VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    amount_due INTEGER NOT NULL,
    amount_paid INTEGER DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'usd',
    created TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    paid_at TIMESTAMP,
    period_start TIMESTAMP,
    period_end TIMESTAMP
);

-- Stripe Charges
CREATE TABLE IF NOT EXISTS raw.stripe_charges (
    id VARCHAR(50) PRIMARY KEY,
    customer VARCHAR(50) NOT NULL,
    invoice VARCHAR(50),
    amount INTEGER NOT NULL,
    currency VARCHAR(10) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL,
    created TIMESTAMP NOT NULL,
    paid BOOLEAN DEFAULT false,
    payment_method_details TEXT,
    failure_code VARCHAR(50),
    failure_message TEXT
);

-- Stripe Payment Intents
CREATE TABLE IF NOT EXISTS raw.stripe_payment_intents (
    id VARCHAR(50) PRIMARY KEY,
    customer VARCHAR(50),
    amount INTEGER NOT NULL,
    currency VARCHAR(10) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL,
    created TIMESTAMP NOT NULL,
    payment_method VARCHAR(50),
    confirmation_method VARCHAR(50),
    invoice VARCHAR(50),
    metadata TEXT
);

-- Stripe Events (Webhook events)
CREATE TABLE IF NOT EXISTS raw.stripe_events (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    created TIMESTAMP NOT NULL,
    data TEXT,
    request_id VARCHAR(50),
    idempotency_key VARCHAR(50),
    api_version VARCHAR(20)
);

-- =====================================================
-- HUBSPOT TABLES (CRM & Sales)
-- =====================================================

-- HubSpot Companies
CREATE TABLE IF NOT EXISTS raw.hubspot_companies (
    id INTEGER PRIMARY KEY,
    properties TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT false
);

-- HubSpot Contacts
CREATE TABLE IF NOT EXISTS raw.hubspot_contacts (
    id INTEGER PRIMARY KEY,
    properties TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT false
);

-- HubSpot Deals
CREATE TABLE IF NOT EXISTS raw.hubspot_deals (
    id INTEGER PRIMARY KEY,
    properties TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT false
);

-- HubSpot Engagements (Calls, emails, meetings, etc.)
CREATE TABLE IF NOT EXISTS raw.hubspot_engagements (
    id INTEGER PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    owner_id INTEGER,
    portal_id INTEGER,
    active BOOLEAN DEFAULT true,
    metadata TEXT,
    associations TEXT
);

-- HubSpot Owners (Sales reps, account managers)
CREATE TABLE IF NOT EXISTS raw.hubspot_owners (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT false
);

-- HubSpot Support Tickets
CREATE TABLE IF NOT EXISTS raw.hubspot_tickets (
    id INTEGER PRIMARY KEY,
    properties TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT false
);

-- =====================================================
-- MARKETING TABLES (Attribution & Campaigns)
-- =====================================================

-- Attribution Touchpoints (Multi-touch attribution)
CREATE TABLE IF NOT EXISTS raw.attribution_touchpoints (
    id VARCHAR(50) PRIMARY KEY,
    contact_id INTEGER,
    account_id INTEGER,
    touchpoint_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    attribution_credit DECIMAL(5,4) DEFAULT 0.0000,
    position_in_journey INTEGER,
    days_to_conversion INTEGER
);

-- Facebook Ads Campaigns
CREATE TABLE IF NOT EXISTS raw.facebook_ads_campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    objective VARCHAR(50),
    created_time TIMESTAMP,
    start_time TIMESTAMP,
    stop_time TIMESTAMP,
    daily_budget DECIMAL(10,2),
    lifetime_budget DECIMAL(10,2),
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0.00,
    conversions INTEGER DEFAULT 0
);

-- Google Ads Campaigns
CREATE TABLE IF NOT EXISTS raw.google_ads_campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    campaign_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    budget_amount DECIMAL(10,2),
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    cost DECIMAL(10,2) DEFAULT 0.00,
    conversions INTEGER DEFAULT 0,
    conversion_value DECIMAL(10,2) DEFAULT 0.00
);

-- Google Analytics Sessions
CREATE TABLE IF NOT EXISTS raw.google_analytics_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    session_date DATE NOT NULL,
    source VARCHAR(100),
    medium VARCHAR(50),
    campaign VARCHAR(100),
    device_category VARCHAR(50),
    landing_page VARCHAR(500),
    session_duration INTEGER DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    goal_completions INTEGER DEFAULT 0,
    ecommerce_revenue DECIMAL(10,2) DEFAULT 0.00
);

-- Iterable Email Campaigns
CREATE TABLE IF NOT EXISTS raw.iterable_campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_at TIMESTAMP,
    ended_at TIMESTAMP,
    send_size INTEGER DEFAULT 0,
    message_medium VARCHAR(50),
    labels TEXT
);

-- LinkedIn Ads Campaigns
CREATE TABLE IF NOT EXISTS raw.linkedin_ads_campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    campaign_type VARCHAR(50),
    objective_type VARCHAR(50),
    created_time TIMESTAMP,
    start_date DATE,
    end_date DATE,
    daily_budget DECIMAL(10,2),
    total_budget DECIMAL(10,2),
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    cost DECIMAL(10,2) DEFAULT 0.00,
    conversions INTEGER DEFAULT 0
);

-- Marketing Qualified Leads
CREATE TABLE IF NOT EXISTS raw.marketing_qualified_leads (
    lead_id VARCHAR(50) PRIMARY KEY,
    contact_id INTEGER,
    account_id INTEGER,
    mql_date TIMESTAMP NOT NULL,
    mql_score DECIMAL(5,2) DEFAULT 0.00,
    lead_source VARCHAR(100),
    campaign_id VARCHAR(50),
    conversion_probability DECIMAL(5,4) DEFAULT 0.0000,
    days_to_mql INTEGER,
    engagement_score DECIMAL(5,2) DEFAULT 0.00
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- App Database Indexes
CREATE INDEX IF NOT EXISTS idx_accounts_created_at ON raw.accounts(created_at);
CREATE INDEX IF NOT EXISTS idx_accounts_is_active ON raw.accounts(is_active);

CREATE INDEX IF NOT EXISTS idx_locations_account_id ON raw.locations(account_id);
CREATE INDEX IF NOT EXISTS idx_locations_created_at ON raw.locations(created_at);

CREATE INDEX IF NOT EXISTS idx_users_account_id ON raw.users(account_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON raw.users(email);

CREATE INDEX IF NOT EXISTS idx_devices_location_id ON raw.devices(location_id);
CREATE INDEX IF NOT EXISTS idx_devices_account_id ON raw.devices(account_id);
CREATE INDEX IF NOT EXISTS idx_devices_status ON raw.devices(status);

CREATE INDEX IF NOT EXISTS idx_subscriptions_account_id ON raw.subscriptions(account_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON raw.subscriptions(status);

-- High-volume tables need partitioning considerations
CREATE INDEX IF NOT EXISTS idx_tap_events_timestamp ON raw.tap_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_tap_events_device_id ON raw.tap_events(device_id);
CREATE INDEX IF NOT EXISTS idx_tap_events_account_id ON raw.tap_events(account_id);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON raw.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_account_id ON raw.user_sessions(account_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_start ON raw.user_sessions(session_start);

CREATE INDEX IF NOT EXISTS idx_page_views_session_id ON raw.page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_page_views_user_id ON raw.page_views(user_id);
CREATE INDEX IF NOT EXISTS idx_page_views_timestamp ON raw.page_views(timestamp);

CREATE INDEX IF NOT EXISTS idx_feature_usage_user_id ON raw.feature_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_account_id ON raw.feature_usage(account_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_timestamp ON raw.feature_usage(timestamp);

-- Stripe Indexes
CREATE INDEX IF NOT EXISTS idx_stripe_customers_account_id ON raw.stripe_customers(account_id);
CREATE INDEX IF NOT EXISTS idx_stripe_customers_email ON raw.stripe_customers(email);

CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_customer ON raw.stripe_subscriptions(customer);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_status ON raw.stripe_subscriptions(status);

CREATE INDEX IF NOT EXISTS idx_stripe_invoices_customer ON raw.stripe_invoices(customer);
CREATE INDEX IF NOT EXISTS idx_stripe_invoices_subscription ON raw.stripe_invoices(subscription);
CREATE INDEX IF NOT EXISTS idx_stripe_invoices_created ON raw.stripe_invoices(created);

CREATE INDEX IF NOT EXISTS idx_stripe_charges_customer ON raw.stripe_charges(customer);
CREATE INDEX IF NOT EXISTS idx_stripe_charges_created ON raw.stripe_charges(created);

-- HubSpot Indexes
CREATE INDEX IF NOT EXISTS idx_hubspot_companies_created_at ON raw.hubspot_companies(created_at);
CREATE INDEX IF NOT EXISTS idx_hubspot_contacts_created_at ON raw.hubspot_contacts(created_at);
CREATE INDEX IF NOT EXISTS idx_hubspot_deals_created_at ON raw.hubspot_deals(created_at);
CREATE INDEX IF NOT EXISTS idx_hubspot_engagements_owner_id ON raw.hubspot_engagements(owner_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_engagements_created_at ON raw.hubspot_engagements(created_at);

-- Marketing Indexes
CREATE INDEX IF NOT EXISTS idx_attribution_touchpoints_contact_id ON raw.attribution_touchpoints(contact_id);
CREATE INDEX IF NOT EXISTS idx_attribution_touchpoints_account_id ON raw.attribution_touchpoints(account_id);
CREATE INDEX IF NOT EXISTS idx_attribution_touchpoints_timestamp ON raw.attribution_touchpoints(timestamp);

CREATE INDEX IF NOT EXISTS idx_facebook_campaigns_created_time ON raw.facebook_ads_campaigns(created_time);
CREATE INDEX IF NOT EXISTS idx_facebook_campaigns_status ON raw.facebook_ads_campaigns(status);

CREATE INDEX IF NOT EXISTS idx_google_campaigns_start_date ON raw.google_ads_campaigns(start_date);
CREATE INDEX IF NOT EXISTS idx_google_campaigns_status ON raw.google_ads_campaigns(status);

CREATE INDEX IF NOT EXISTS idx_ga_sessions_date ON raw.google_analytics_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_ga_sessions_source ON raw.google_analytics_sessions(source);

CREATE INDEX IF NOT EXISTS idx_mqls_mql_date ON raw.marketing_qualified_leads(mql_date);
CREATE INDEX IF NOT EXISTS idx_mqls_contact_id ON raw.marketing_qualified_leads(contact_id);
CREATE INDEX IF NOT EXISTS idx_mqls_account_id ON raw.marketing_qualified_leads(account_id);

-- =====================================================
-- FOREIGN KEY CONSTRAINTS (Optional - for data integrity)
-- =====================================================

-- Uncomment these if you want to enforce referential integrity
-- Note: These may slow down bulk loading operations

/*
-- App Database Foreign Keys
ALTER TABLE raw.locations ADD CONSTRAINT fk_locations_account_id 
    FOREIGN KEY (account_id) REFERENCES raw.accounts(id);

ALTER TABLE raw.users ADD CONSTRAINT fk_users_account_id 
    FOREIGN KEY (account_id) REFERENCES raw.accounts(id);

ALTER TABLE raw.devices ADD CONSTRAINT fk_devices_location_id 
    FOREIGN KEY (location_id) REFERENCES raw.locations(id);
    
ALTER TABLE raw.devices ADD CONSTRAINT fk_devices_account_id 
    FOREIGN KEY (account_id) REFERENCES raw.accounts(id);

ALTER TABLE raw.subscriptions ADD CONSTRAINT fk_subscriptions_account_id 
    FOREIGN KEY (account_id) REFERENCES raw.accounts(id);

ALTER TABLE raw.tap_events ADD CONSTRAINT fk_tap_events_device_id 
    FOREIGN KEY (device_id) REFERENCES raw.devices(id);
    
ALTER TABLE raw.tap_events ADD CONSTRAINT fk_tap_events_account_id 
    FOREIGN KEY (account_id) REFERENCES raw.accounts(id);

ALTER TABLE raw.user_sessions ADD CONSTRAINT fk_user_sessions_user_id 
    FOREIGN KEY (user_id) REFERENCES raw.users(id);
    
ALTER TABLE raw.user_sessions ADD CONSTRAINT fk_user_sessions_account_id 
    FOREIGN KEY (account_id) REFERENCES raw.accounts(id);

ALTER TABLE raw.page_views ADD CONSTRAINT fk_page_views_session_id 
    FOREIGN KEY (session_id) REFERENCES raw.user_sessions(id);
    
ALTER TABLE raw.page_views ADD CONSTRAINT fk_page_views_user_id 
    FOREIGN KEY (user_id) REFERENCES raw.users(id);

ALTER TABLE raw.feature_usage ADD CONSTRAINT fk_feature_usage_user_id 
    FOREIGN KEY (user_id) REFERENCES raw.users(id);
    
ALTER TABLE raw.feature_usage ADD CONSTRAINT fk_feature_usage_account_id 
    FOREIGN KEY (account_id) REFERENCES raw.accounts(id);

-- Stripe Foreign Keys
ALTER TABLE raw.stripe_subscriptions ADD CONSTRAINT fk_stripe_subscriptions_customer 
    FOREIGN KEY (customer) REFERENCES raw.stripe_customers(id);

ALTER TABLE raw.stripe_subscription_items ADD CONSTRAINT fk_stripe_sub_items_subscription 
    FOREIGN KEY (subscription) REFERENCES raw.stripe_subscriptions(id);
    
ALTER TABLE raw.stripe_subscription_items ADD CONSTRAINT fk_stripe_sub_items_price 
    FOREIGN KEY (price) REFERENCES raw.stripe_prices(id);

ALTER TABLE raw.stripe_invoices ADD CONSTRAINT fk_stripe_invoices_customer 
    FOREIGN KEY (customer) REFERENCES raw.stripe_customers(id);
    
ALTER TABLE raw.stripe_invoices ADD CONSTRAINT fk_stripe_invoices_subscription 
    FOREIGN KEY (subscription) REFERENCES raw.stripe_subscriptions(id);

ALTER TABLE raw.stripe_charges ADD CONSTRAINT fk_stripe_charges_customer 
    FOREIGN KEY (customer) REFERENCES raw.stripe_customers(id);

ALTER TABLE raw.stripe_payment_intents ADD CONSTRAINT fk_stripe_payment_intents_customer 
    FOREIGN KEY (customer) REFERENCES raw.stripe_customers(id);
*/

-- =====================================================
-- PERFORMANCE OPTIMIZATIONS
-- =====================================================

-- Enable parallel processing for large table operations
SET max_parallel_workers_per_gather = 4;
SET parallel_tuple_cost = 0.1;
SET parallel_setup_cost = 1000.0;

-- Optimize for bulk loading
SET synchronous_commit = off;
SET checkpoint_completion_target = 0.9;
SET wal_buffers = 16MB;

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Grant permissions to saas_user
GRANT USAGE ON SCHEMA raw TO saas_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO saas_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw TO saas_user;

-- Grant read permissions for analytics queries
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO saas_user;

-- =====================================================
-- SUMMARY INFORMATION
-- =====================================================

/*
SCHEMA SUMMARY:
===============

1. APP DATABASE TABLES (9 tables):
   - accounts, locations, users, devices, subscriptions
   - tap_events, user_sessions, page_views, feature_usage

2. STRIPE TABLES (8 tables):
   - stripe_customers, stripe_prices, stripe_subscriptions
   - stripe_subscription_items, stripe_invoices, stripe_charges
   - stripe_payment_intents, stripe_events

3. HUBSPOT TABLES (6 tables):
   - hubspot_companies, hubspot_contacts, hubspot_deals
   - hubspot_engagements, hubspot_owners, hubspot_tickets

4. MARKETING TABLES (7 tables):
   - attribution_touchpoints, facebook_ads_campaigns, google_ads_campaigns
   - google_analytics_sessions, iterable_campaigns, linkedin_ads_campaigns
   - marketing_qualified_leads

TOTAL: 30 tables optimized for Entity-Centric Modeling

EXPECTED DATA VOLUMES (Production Scale):
- 5,000 companies
- 75,000+ locations  
- 375,000+ devices
- 25+ million device events
- Complete CRM pipeline
- Full marketing attribution
- Comprehensive financial data

OPTIMIZATIONS:
- Strategic indexing for query performance
- Bulk loading optimizations
- Optional foreign key constraints
- Parallel processing configuration
*/