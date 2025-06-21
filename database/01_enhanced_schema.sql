-- =====================================================
-- SaaS Data Platform - Enhanced Schema Definition
-- =====================================================
-- This enhanced schema includes all existing columns from the original schema
-- plus additional columns required by the data generator scripts
-- Maintains backward compatibility while supporting new data generation needs
-- Target: saas_platform_dev database

-- =====================================================
-- CREATE DATABASES
-- =====================================================
-- Ensure both main and superset databases exist
CREATE DATABASE IF NOT EXISTS saas_platform_dev;
CREATE DATABASE IF NOT EXISTS superset_db;

-- Switch to main database
\c saas_platform_dev;

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

-- Companies/Accounts - Enhanced with data generator fields
CREATE TABLE IF NOT EXISTS raw.app_database_accounts (
    id VARCHAR(50) PRIMARY KEY,  -- Changed to VARCHAR to support generator's format
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    -- Original schema fields
    created_date DATE,
    business_type VARCHAR(100),
    location_count INTEGER,
    -- Data generator required fields
    industry VARCHAR(100),
    employee_count INTEGER,
    annual_revenue BIGINT,
    website VARCHAR(500),
    status VARCHAR(50),
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations - Enhanced with geographic and status fields
CREATE TABLE IF NOT EXISTS raw.app_database_locations (
    id VARCHAR(50) PRIMARY KEY,  -- Changed to VARCHAR to support generator's format
    customer_id VARCHAR(50) NOT NULL,  -- Changed to match accounts.id type
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'US',
    location_type VARCHAR(50),
    -- Original schema fields
    business_type VARCHAR(100),
    size VARCHAR(50),
    expected_device_count INTEGER,
    install_date DATE,
    -- Data generator required fields
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    capacity INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users - Enhanced with activity tracking
CREATE TABLE IF NOT EXISTS raw.app_database_users (
    id VARCHAR(50) PRIMARY KEY,  -- Changed to VARCHAR to support generator's format
    customer_id VARCHAR(50) NOT NULL,  -- Changed to match accounts.id type
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    role VARCHAR(50),
    -- Original schema fields
    created_date DATE,
    last_login_date DATE,
    -- Data generator required fields
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Devices - Enhanced with maintenance and online status
CREATE TABLE IF NOT EXISTS raw.app_database_devices (
    id VARCHAR(50) PRIMARY KEY,  -- Changed to VARCHAR to support generator's format
    location_id VARCHAR(50) NOT NULL,  -- Changed to match locations.id type
    device_type VARCHAR(100),
    -- Original schema fields
    category VARCHAR(50),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    install_date DATE,
    warranty_expiry DATE,
    purchase_price DECIMAL(10,2),
    firmware_version VARCHAR(50),
    ip_address VARCHAR(45),
    mac_address VARCHAR(17),
    status VARCHAR(50),
    usage_pattern VARCHAR(50),
    expected_lifespan_years INTEGER,
    energy_consumption_watts INTEGER,
    network_connectivity VARCHAR(50),
    -- Data generator required fields
    installation_date DATE,
    last_maintenance_date DATE,
    is_online BOOLEAN DEFAULT TRUE,
    customer_id VARCHAR(50),  -- Added for potential future use
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions - Enhanced with flexible pricing
CREATE TABLE IF NOT EXISTS raw.app_database_subscriptions (
    id VARCHAR(50) PRIMARY KEY,  -- Changed to VARCHAR to support generator's format
    customer_id VARCHAR(50) NOT NULL,  -- Changed to match accounts.id type
    plan_name VARCHAR(100),
    status VARCHAR(50),
    start_date DATE,
    end_date DATE,
    -- Original schema fields
    monthly_price DECIMAL(10,2),
    billing_cycle VARCHAR(20),
    -- Data generator required fields
    monthly_amount DECIMAL(10,2),  -- Alias for monthly_price
    current_term_start DATE,  -- Added as per requirements
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Device Events/Tap Events (unchanged but with VARCHAR IDs)
CREATE TABLE IF NOT EXISTS raw.app_database_tap_events (
    id VARCHAR(50) PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,  -- Changed to match devices.id type
    location_id VARCHAR(50) NOT NULL,  -- Changed to match locations.id type
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(50),
    status VARCHAR(50),
    metrics JSONB,
    device_category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions (unchanged but with VARCHAR IDs)
CREATE TABLE IF NOT EXISTS raw.app_database_user_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,  -- Changed to match users.id type
    customer_id VARCHAR(50) NOT NULL,  -- Changed to match accounts.id type
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    page_views INTEGER,
    actions_taken INTEGER,
    device_type VARCHAR(50),
    browser VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Page Views (unchanged but with VARCHAR IDs)
CREATE TABLE IF NOT EXISTS raw.app_database_page_views (
    page_view_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,  -- Changed to match users.id type
    customer_id VARCHAR(50) NOT NULL,  -- Changed to match accounts.id type
    page_url VARCHAR(500),
    page_title VARCHAR(255),
    timestamp TIMESTAMP,
    time_on_page_seconds INTEGER,
    referrer_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature Usage (unchanged but with VARCHAR IDs)
CREATE TABLE IF NOT EXISTS raw.app_database_feature_usage (
    usage_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,  -- Changed to match users.id type
    customer_id VARCHAR(50) NOT NULL,  -- Changed to match accounts.id type
    feature_name VARCHAR(100),
    usage_count INTEGER DEFAULT 1,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- STRIPE BILLING TABLES (unchanged from original)
-- =====================================================

-- Stripe Customers
CREATE TABLE IF NOT EXISTS raw.stripe_customers (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(255),
    description TEXT,
    phone VARCHAR(50),
    address JSONB,
    created TIMESTAMP,
    currency VARCHAR(10),
    delinquent BOOLEAN DEFAULT FALSE,
    invoice_prefix VARCHAR(50),
    livemode BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    shipping JSONB,
    tax_exempt VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stripe Prices
CREATE TABLE IF NOT EXISTS raw.stripe_prices (
    id VARCHAR(50) PRIMARY KEY,
    object VARCHAR(20),
    active BOOLEAN,
    currency VARCHAR(10),
    unit_amount INTEGER,
    type VARCHAR(20),
    recurring_interval VARCHAR(20),
    recurring_interval_count INTEGER,
    nickname VARCHAR(100),
    created TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stripe Subscriptions
CREATE TABLE IF NOT EXISTS raw.stripe_subscriptions (
    id VARCHAR(50) PRIMARY KEY,
    object VARCHAR(20),
    application_fee_percent DECIMAL(5,4),
    billing_cycle_anchor TIMESTAMP,
    cancel_at TIMESTAMP,
    cancel_at_period_end BOOLEAN,
    canceled_at TIMESTAMP,
    created TIMESTAMP,
    current_period_end TIMESTAMP,
    current_period_start TIMESTAMP,
    customer VARCHAR(50),
    days_until_due INTEGER,
    default_payment_method VARCHAR(50),
    default_source VARCHAR(50),
    discount JSONB,
    ended_at TIMESTAMP,
    items JSONB,
    latest_invoice VARCHAR(50),
    livemode BOOLEAN,
    metadata JSONB,
    next_pending_invoice_item_invoice TIMESTAMP,
    pending_invoice_item_interval JSONB,
    pending_setup_intent VARCHAR(50),
    pending_update JSONB,
    schedule VARCHAR(50),
    start_date TIMESTAMP,
    status VARCHAR(50),
    trial_end TIMESTAMP,
    trial_start TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stripe Subscription Items
CREATE TABLE IF NOT EXISTS raw.stripe_subscription_items (
    id VARCHAR(50) PRIMARY KEY,
    object VARCHAR(20),
    billing_thresholds JSONB,
    created TIMESTAMP,
    metadata JSONB,
    price JSONB,
    quantity INTEGER,
    subscription VARCHAR(50),
    tax_rates JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stripe Invoices
CREATE TABLE IF NOT EXISTS raw.stripe_invoices (
    id VARCHAR(50) PRIMARY KEY,
    object VARCHAR(20),
    account_country VARCHAR(10),
    account_name VARCHAR(255),
    account_tax_ids JSONB,
    amount_due INTEGER,
    amount_paid INTEGER,
    amount_remaining INTEGER,
    application_fee_amount INTEGER,
    attempt_count INTEGER,
    attempted BOOLEAN,
    auto_advance BOOLEAN,
    billing_reason VARCHAR(50),
    charge VARCHAR(50),
    collection_method VARCHAR(20),
    created TIMESTAMP,
    currency VARCHAR(10),
    custom_fields JSONB,
    customer VARCHAR(50),
    customer_address JSONB,
    customer_email VARCHAR(255),
    customer_name VARCHAR(255),
    customer_phone VARCHAR(50),
    customer_shipping JSONB,
    customer_tax_exempt VARCHAR(20),
    customer_tax_ids JSONB,
    default_payment_method VARCHAR(50),
    default_source VARCHAR(50),
    default_tax_rates JSONB,
    description TEXT,
    discount JSONB,
    discounts JSONB,
    due_date TIMESTAMP,
    ending_balance INTEGER,
    footer TEXT,
    hosted_invoice_url TEXT,
    invoice_pdf TEXT,
    last_finalization_error JSONB,
    lines JSONB,
    livemode BOOLEAN,
    metadata JSONB,
    next_payment_attempt TIMESTAMP,
    number VARCHAR(100),
    on_behalf_of VARCHAR(50),
    paid BOOLEAN,
    payment_intent VARCHAR(50),
    payment_settings JSONB,
    period_end TIMESTAMP,
    period_start TIMESTAMP,
    post_payment_credit_notes_amount INTEGER,
    pre_payment_credit_notes_amount INTEGER,
    receipt_number VARCHAR(100),
    starting_balance INTEGER,
    statement_descriptor VARCHAR(100),
    status VARCHAR(50),
    status_transitions JSONB,
    subscription VARCHAR(50),
    subtotal INTEGER,
    tax INTEGER,
    total INTEGER,
    total_tax_amounts JSONB,
    transfer_data JSONB,
    webhooks_delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stripe Charges
CREATE TABLE IF NOT EXISTS raw.stripe_charges (
    id VARCHAR(50) PRIMARY KEY,
    object VARCHAR(20),
    amount INTEGER,
    amount_captured INTEGER,
    amount_refunded INTEGER,
    application VARCHAR(50),
    application_fee VARCHAR(50),
    application_fee_amount INTEGER,
    balance_transaction VARCHAR(50),
    billing_details JSONB,
    calculated_statement_descriptor VARCHAR(100),
    captured BOOLEAN,
    created TIMESTAMP,
    currency VARCHAR(10),
    customer VARCHAR(50),
    description TEXT,
    destination VARCHAR(50),
    dispute VARCHAR(50),
    disputed BOOLEAN,
    failure_code VARCHAR(50),
    failure_message TEXT,
    fraud_details JSONB,
    invoice VARCHAR(50),
    livemode BOOLEAN,
    metadata JSONB,
    on_behalf_of VARCHAR(50),
    order_id VARCHAR(50),
    outcome JSONB,
    paid BOOLEAN,
    payment_intent VARCHAR(50),
    payment_method VARCHAR(50),
    payment_method_details JSONB,
    receipt_email VARCHAR(255),
    receipt_number VARCHAR(100),
    receipt_url TEXT,
    refunded BOOLEAN,
    refunds JSONB,
    review VARCHAR(50),
    shipping JSONB,
    source JSONB,
    source_transfer VARCHAR(50),
    statement_descriptor VARCHAR(100),
    statement_descriptor_suffix VARCHAR(100),
    status VARCHAR(50),
    transfer_data JSONB,
    transfer_group VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stripe Payment Intents
CREATE TABLE IF NOT EXISTS raw.stripe_payment_intents (
    id VARCHAR(50) PRIMARY KEY,
    object VARCHAR(20),
    amount INTEGER,
    amount_capturable INTEGER,
    amount_received INTEGER,
    application VARCHAR(50),
    application_fee_amount INTEGER,
    canceled_at TIMESTAMP,
    cancellation_reason VARCHAR(50),
    capture_method VARCHAR(20),
    charges JSONB,
    client_secret VARCHAR(255),
    confirmation_method VARCHAR(20),
    created TIMESTAMP,
    currency VARCHAR(10),
    customer VARCHAR(50),
    description TEXT,
    invoice VARCHAR(50),
    last_payment_error JSONB,
    livemode BOOLEAN,
    metadata JSONB,
    next_action JSONB,
    on_behalf_of VARCHAR(50),
    payment_method VARCHAR(50),
    payment_method_options JSONB,
    payment_method_types JSONB,
    receipt_email VARCHAR(255),
    review VARCHAR(50),
    setup_future_usage VARCHAR(20),
    shipping JSONB,
    statement_descriptor VARCHAR(100),
    statement_descriptor_suffix VARCHAR(100),
    status VARCHAR(50),
    transfer_data JSONB,
    transfer_group VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stripe Events
CREATE TABLE IF NOT EXISTS raw.stripe_events (
    id VARCHAR(50) PRIMARY KEY,
    object VARCHAR(20),
    api_version VARCHAR(20),
    created TIMESTAMP,
    data JSONB,
    livemode BOOLEAN,
    pending_webhooks INTEGER,
    request JSONB,
    type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- HUBSPOT CRM TABLES (unchanged from original)
-- =====================================================

-- HubSpot Companies
CREATE TABLE IF NOT EXISTS raw.hubspot_companies (
    id VARCHAR(50) PRIMARY KEY,
    properties JSONB,
    name VARCHAR(255),
    business_type VARCHAR(100),
    location_count INTEGER,
    created_date DATE,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HubSpot Contacts
CREATE TABLE IF NOT EXISTS raw.hubspot_contacts (
    id VARCHAR(50) PRIMARY KEY,
    properties JSONB,
    firstName VARCHAR(100),
    lastName VARCHAR(100),
    email VARCHAR(255),
    company VARCHAR(255),
    phone VARCHAR(50),
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HubSpot Deals
CREATE TABLE IF NOT EXISTS raw.hubspot_deals (
    id VARCHAR(50) PRIMARY KEY,
    properties JSONB,
    associations JSONB,
    dealname VARCHAR(255),
    amount DECIMAL(12,2),
    dealstage VARCHAR(100),
    pipeline VARCHAR(100),
    closedate DATE,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HubSpot Engagements
CREATE TABLE IF NOT EXISTS raw.hubspot_engagements (
    id VARCHAR(50) PRIMARY KEY,
    engagement JSONB,
    associations JSONB,
    metadata JSONB,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HubSpot Owners
CREATE TABLE IF NOT EXISTS raw.hubspot_owners (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255),
    firstName VARCHAR(100),
    lastName VARCHAR(100),
    userId INTEGER,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HubSpot Tickets
CREATE TABLE IF NOT EXISTS raw.hubspot_tickets (
    id VARCHAR(50) PRIMARY KEY,
    properties JSONB,
    associations JSONB,
    subject VARCHAR(500),
    content TEXT,
    hs_pipeline VARCHAR(100),
    hs_pipeline_stage VARCHAR(100),
    hs_ticket_priority VARCHAR(50),
    createdate TIMESTAMP,
    hs_lastmodifieddate TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- MARKETING ATTRIBUTION TABLES (unchanged from original)
-- =====================================================

-- Attribution Touchpoints
CREATE TABLE IF NOT EXISTS raw.attribution_touchpoints (
    id VARCHAR(50) PRIMARY KEY,
    mql_id VARCHAR(50),
    touchpoint_date TIMESTAMP,
    channel VARCHAR(100),
    campaign_id VARCHAR(50),
    campaign_name VARCHAR(255),
    medium VARCHAR(100),
    source VARCHAR(100),
    content VARCHAR(255),
    attribution_weight DECIMAL(5,4),
    touchpoint_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Google Ads Campaigns
CREATE TABLE IF NOT EXISTS raw.google_ads_campaigns (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    status VARCHAR(50),
    campaign_type VARCHAR(50),
    advertising_channel_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    budget_amount DECIMAL(12,2),
    target_cpa DECIMAL(10,2),
    impressions INTEGER,
    clicks INTEGER,
    cost DECIMAL(12,2),
    conversions DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Facebook/Meta Ads Campaigns
CREATE TABLE IF NOT EXISTS raw.facebook_ads_campaigns (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    status VARCHAR(50),
    objective VARCHAR(50),
    created_time TIMESTAMP,
    start_time TIMESTAMP,
    stop_time TIMESTAMP,
    daily_budget DECIMAL(10,2),
    lifetime_budget DECIMAL(12,2),
    impressions INTEGER,
    clicks INTEGER,
    spend DECIMAL(12,2),
    actions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LinkedIn Ads Campaigns
CREATE TABLE IF NOT EXISTS raw.linkedin_ads_campaigns (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    status VARCHAR(50),
    campaign_type VARCHAR(50),
    objective_type VARCHAR(50),
    created_time TIMESTAMP,
    start_date DATE,
    end_date DATE,
    daily_budget DECIMAL(10,2),
    total_budget DECIMAL(12,2),
    impressions INTEGER,
    clicks INTEGER,
    cost DECIMAL(12,2),
    conversions INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Iterable Email Campaigns
CREATE TABLE IF NOT EXISTS raw.iterable_campaigns (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    campaign_type VARCHAR(50),
    status VARCHAR(50),
    created_at_source TIMESTAMP,
    updated_at_source TIMESTAMP,
    start_at TIMESTAMP,
    ended_at TIMESTAMP,
    send_size INTEGER,
    message_medium VARCHAR(50),
    labels TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Google Analytics Sessions
CREATE TABLE IF NOT EXISTS raw.google_analytics_sessions (
    date DATE,
    sessions INTEGER,
    users INTEGER,
    new_users INTEGER,
    page_views INTEGER,
    bounce_rate DECIMAL(5,4),
    avg_session_duration DECIMAL(10,2),
    goal_completions INTEGER,
    goal_conversion_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date)
);

-- Marketing Qualified Leads
CREATE TABLE IF NOT EXISTS raw.marketing_qualified_leads (
    id VARCHAR(50) PRIMARY KEY,
    created_at_source TIMESTAMP,
    contact_id INTEGER,
    account_id INTEGER,
    mql_date TIMESTAMP,
    mql_score DECIMAL(5,2),
    lead_source VARCHAR(100),
    campaign_id VARCHAR(50),
    conversion_probability DECIMAL(5,4),
    days_to_mql INTEGER,
    engagement_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- App Database Indexes
CREATE INDEX IF NOT EXISTS idx_app_database_accounts_created_date ON raw.app_database_accounts(created_date);
CREATE INDEX IF NOT EXISTS idx_app_database_accounts_business_type ON raw.app_database_accounts(business_type);
CREATE INDEX IF NOT EXISTS idx_app_database_accounts_email ON raw.app_database_accounts(email);
CREATE INDEX IF NOT EXISTS idx_app_database_accounts_industry ON raw.app_database_accounts(industry);
CREATE INDEX IF NOT EXISTS idx_app_database_accounts_status ON raw.app_database_accounts(status);

CREATE INDEX IF NOT EXISTS idx_app_database_locations_customer_id ON raw.app_database_locations(customer_id);
CREATE INDEX IF NOT EXISTS idx_app_database_locations_business_type ON raw.app_database_locations(business_type);
CREATE INDEX IF NOT EXISTS idx_app_database_locations_install_date ON raw.app_database_locations(install_date);
CREATE INDEX IF NOT EXISTS idx_app_database_locations_is_active ON raw.app_database_locations(is_active);
CREATE INDEX IF NOT EXISTS idx_app_database_locations_lat_lng ON raw.app_database_locations(latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_app_database_users_customer_id ON raw.app_database_users(customer_id);
CREATE INDEX IF NOT EXISTS idx_app_database_users_email ON raw.app_database_users(email);
CREATE INDEX IF NOT EXISTS idx_app_database_users_created_date ON raw.app_database_users(created_date);
CREATE INDEX IF NOT EXISTS idx_app_database_users_last_login_at ON raw.app_database_users(last_login_at);
CREATE INDEX IF NOT EXISTS idx_app_database_users_is_active ON raw.app_database_users(is_active);

CREATE INDEX IF NOT EXISTS idx_app_database_devices_location_id ON raw.app_database_devices(location_id);
CREATE INDEX IF NOT EXISTS idx_app_database_devices_device_type ON raw.app_database_devices(device_type);
CREATE INDEX IF NOT EXISTS idx_app_database_devices_status ON raw.app_database_devices(status);
CREATE INDEX IF NOT EXISTS idx_app_database_devices_install_date ON raw.app_database_devices(install_date);
CREATE INDEX IF NOT EXISTS idx_app_database_devices_is_online ON raw.app_database_devices(is_online);

CREATE INDEX IF NOT EXISTS idx_app_database_subscriptions_customer_id ON raw.app_database_subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_app_database_subscriptions_status ON raw.app_database_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_app_database_subscriptions_start_date ON raw.app_database_subscriptions(start_date);

CREATE INDEX IF NOT EXISTS idx_app_database_tap_events_device_id ON raw.app_database_tap_events(device_id);
CREATE INDEX IF NOT EXISTS idx_app_database_tap_events_location_id ON raw.app_database_tap_events(location_id);
CREATE INDEX IF NOT EXISTS idx_app_database_tap_events_timestamp ON raw.app_database_tap_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_app_database_tap_events_event_type ON raw.app_database_tap_events(event_type);

CREATE INDEX IF NOT EXISTS idx_app_database_user_sessions_user_id ON raw.app_database_user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_app_database_user_sessions_customer_id ON raw.app_database_user_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_app_database_user_sessions_start_time ON raw.app_database_user_sessions(start_time);

CREATE INDEX IF NOT EXISTS idx_app_database_page_views_session_id ON raw.app_database_page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_app_database_page_views_user_id ON raw.app_database_page_views(user_id);
CREATE INDEX IF NOT EXISTS idx_app_database_page_views_timestamp ON raw.app_database_page_views(timestamp);

-- Stripe Indexes
CREATE INDEX IF NOT EXISTS idx_stripe_customers_email ON raw.stripe_customers(email);
CREATE INDEX IF NOT EXISTS idx_stripe_customers_created ON raw.stripe_customers(created);

CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_customer ON raw.stripe_subscriptions(customer);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_status ON raw.stripe_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_created ON raw.stripe_subscriptions(created);

CREATE INDEX IF NOT EXISTS idx_stripe_invoices_customer ON raw.stripe_invoices(customer);
CREATE INDEX IF NOT EXISTS idx_stripe_invoices_subscription ON raw.stripe_invoices(subscription);
CREATE INDEX IF NOT EXISTS idx_stripe_invoices_status ON raw.stripe_invoices(status);
CREATE INDEX IF NOT EXISTS idx_stripe_invoices_created ON raw.stripe_invoices(created);

-- HubSpot Indexes
CREATE INDEX IF NOT EXISTS idx_hubspot_companies_created_date ON raw.hubspot_companies(created_date);
CREATE INDEX IF NOT EXISTS idx_hubspot_companies_business_type ON raw.hubspot_companies(business_type);

CREATE INDEX IF NOT EXISTS idx_hubspot_contacts_email ON raw.hubspot_contacts(email);
CREATE INDEX IF NOT EXISTS idx_hubspot_contacts_company ON raw.hubspot_contacts(company);

CREATE INDEX IF NOT EXISTS idx_hubspot_deals_amount ON raw.hubspot_deals(amount);
CREATE INDEX IF NOT EXISTS idx_hubspot_deals_dealstage ON raw.hubspot_deals(dealstage);
CREATE INDEX IF NOT EXISTS idx_hubspot_deals_closedate ON raw.hubspot_deals(closedate);

-- Marketing Indexes
CREATE INDEX IF NOT EXISTS idx_attribution_touchpoints_mql_id ON raw.attribution_touchpoints(mql_id);
CREATE INDEX IF NOT EXISTS idx_attribution_touchpoints_campaign_id ON raw.attribution_touchpoints(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attribution_touchpoints_touchpoint_date ON raw.attribution_touchpoints(touchpoint_date);

CREATE INDEX IF NOT EXISTS idx_google_ads_campaigns_start_date ON raw.google_ads_campaigns(start_date);
CREATE INDEX IF NOT EXISTS idx_google_ads_campaigns_status ON raw.google_ads_campaigns(status);

CREATE INDEX IF NOT EXISTS idx_facebook_ads_campaigns_start_time ON raw.facebook_ads_campaigns(start_time);
CREATE INDEX IF NOT EXISTS idx_facebook_ads_campaigns_status ON raw.facebook_ads_campaigns(status);

CREATE INDEX IF NOT EXISTS idx_marketing_qualified_leads_mql_date ON raw.marketing_qualified_leads(mql_date);
CREATE INDEX IF NOT EXISTS idx_marketing_qualified_leads_contact_id ON raw.marketing_qualified_leads(contact_id);
CREATE INDEX IF NOT EXISTS idx_marketing_qualified_leads_account_id ON raw.marketing_qualified_leads(account_id);

-- =====================================================
-- FOREIGN KEY CONSTRAINTS (Optional but recommended)
-- =====================================================
-- Note: These are commented out by default to allow flexible data loading
-- Uncomment after initial data load if referential integrity is desired

-- ALTER TABLE raw.app_database_locations 
--     ADD CONSTRAINT fk_locations_customer 
--     FOREIGN KEY (customer_id) REFERENCES raw.app_database_accounts(id);

-- ALTER TABLE raw.app_database_users 
--     ADD CONSTRAINT fk_users_customer 
--     FOREIGN KEY (customer_id) REFERENCES raw.app_database_accounts(id);

-- ALTER TABLE raw.app_database_devices 
--     ADD CONSTRAINT fk_devices_location 
--     FOREIGN KEY (location_id) REFERENCES raw.app_database_locations(id);

-- ALTER TABLE raw.app_database_subscriptions 
--     ADD CONSTRAINT fk_subscriptions_customer 
--     FOREIGN KEY (customer_id) REFERENCES raw.app_database_accounts(id);

-- ALTER TABLE raw.app_database_tap_events 
--     ADD CONSTRAINT fk_tap_events_device 
--     FOREIGN KEY (device_id) REFERENCES raw.app_database_devices(id);

-- ALTER TABLE raw.app_database_tap_events 
--     ADD CONSTRAINT fk_tap_events_location 
--     FOREIGN KEY (location_id) REFERENCES raw.app_database_locations(id);

-- ALTER TABLE raw.app_database_user_sessions 
--     ADD CONSTRAINT fk_sessions_user 
--     FOREIGN KEY (user_id) REFERENCES raw.app_database_users(id);

-- ALTER TABLE raw.app_database_user_sessions 
--     ADD CONSTRAINT fk_sessions_customer 
--     FOREIGN KEY (customer_id) REFERENCES raw.app_database_accounts(id);

-- ALTER TABLE raw.app_database_page_views 
--     ADD CONSTRAINT fk_page_views_session 
--     FOREIGN KEY (session_id) REFERENCES raw.app_database_user_sessions(session_id);

-- ALTER TABLE raw.app_database_page_views 
--     ADD CONSTRAINT fk_page_views_user 
--     FOREIGN KEY (user_id) REFERENCES raw.app_database_users(id);

-- =====================================================
-- PERMISSIONS AND GRANTS
-- =====================================================

-- Grant all privileges to saas_user
GRANT ALL PRIVILEGES ON SCHEMA raw TO saas_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO saas_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw TO saas_user;

-- Allow future tables to be accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT ALL PRIVILEGES ON TABLES TO saas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT ALL PRIVILEGES ON SEQUENCES TO saas_user;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA raw IS 'Raw data layer for all source systems - enhanced to support data generator requirements';

-- App Database Comments
COMMENT ON TABLE raw.app_database_accounts IS 'Customer companies - main business entities with industry and revenue data';
COMMENT ON TABLE raw.app_database_locations IS 'Physical business locations with geographic coordinates and capacity info';
COMMENT ON TABLE raw.app_database_users IS 'Individual platform users with activity tracking';
COMMENT ON TABLE raw.app_database_devices IS 'IoT devices deployed at locations with maintenance and online status';
COMMENT ON TABLE raw.app_database_subscriptions IS 'Subscription plans with flexible pricing options';
COMMENT ON TABLE raw.app_database_tap_events IS 'Real-time device events';
COMMENT ON TABLE raw.app_database_user_sessions IS 'User login sessions tracking';
COMMENT ON TABLE raw.app_database_page_views IS 'Web app page view analytics';

-- HubSpot Comments
COMMENT ON TABLE raw.hubspot_companies IS 'HubSpot CRM companies';
COMMENT ON TABLE raw.hubspot_contacts IS 'HubSpot CRM contacts';
COMMENT ON TABLE raw.hubspot_deals IS 'HubSpot sales deals';

-- Marketing Comments
COMMENT ON TABLE raw.attribution_touchpoints IS 'Marketing attribution touchpoints';
COMMENT ON TABLE raw.google_ads_campaigns IS 'Google Ads performance data';
COMMENT ON TABLE raw.marketing_qualified_leads IS 'Marketing qualified leads (MQLs)';

-- Column Comments for new fields
COMMENT ON COLUMN raw.app_database_accounts.industry IS 'Industry vertical of the company';
COMMENT ON COLUMN raw.app_database_accounts.employee_count IS 'Number of employees in the company';
COMMENT ON COLUMN raw.app_database_accounts.annual_revenue IS 'Annual revenue in dollars';
COMMENT ON COLUMN raw.app_database_accounts.website IS 'Company website URL';
COMMENT ON COLUMN raw.app_database_accounts.status IS 'Account status (active, inactive, prospect)';

COMMENT ON COLUMN raw.app_database_locations.latitude IS 'Geographic latitude coordinate';
COMMENT ON COLUMN raw.app_database_locations.longitude IS 'Geographic longitude coordinate';
COMMENT ON COLUMN raw.app_database_locations.capacity IS 'Maximum capacity of the location';
COMMENT ON COLUMN raw.app_database_locations.is_active IS 'Whether the location is currently active';

COMMENT ON COLUMN raw.app_database_users.last_login_at IS 'Timestamp of user''s last login';
COMMENT ON COLUMN raw.app_database_users.is_active IS 'Whether the user account is active';

COMMENT ON COLUMN raw.app_database_devices.installation_date IS 'Date when device was installed';
COMMENT ON COLUMN raw.app_database_devices.last_maintenance_date IS 'Date of last maintenance performed';
COMMENT ON COLUMN raw.app_database_devices.is_online IS 'Whether the device is currently online';

COMMENT ON COLUMN raw.app_database_subscriptions.monthly_amount IS 'Monthly subscription amount in dollars';
COMMENT ON COLUMN raw.app_database_subscriptions.current_term_start IS 'Start date of current billing term';

-- =====================================================
-- MIGRATION SUPPORT
-- =====================================================
-- Create views to support backward compatibility with INTEGER IDs if needed
-- These views can be used by existing queries expecting INTEGER IDs

-- Example view for accounts with INTEGER ID casting (commented out by default)
-- CREATE OR REPLACE VIEW raw.app_database_accounts_int_id AS
-- SELECT 
--     CASE 
--         WHEN id ~ '^[0-9]+$' THEN id::INTEGER 
--         ELSE NULL 
--     END as id,
--     name,
--     email,
--     created_date,
--     business_type,
--     location_count,
--     industry,
--     employee_count,
--     annual_revenue,
--     website,
--     status,
--     created_at,
--     updated_at
-- FROM raw.app_database_accounts;

-- =====================================================
-- END OF ENHANCED SCHEMA
-- =====================================================