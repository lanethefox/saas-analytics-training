-- Schema Definition for SaaS Data Platform
-- PostgreSQL database schema for bar management platform

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Core Application Tables
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('enterprise', 'professional', 'basic')),
    industry_vertical VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'trial', 'churned', 'suspended')),
    billing_email VARCHAR(255),
    primary_contact_name VARCHAR(255),
    primary_contact_phone VARCHAR(50),
    total_locations INTEGER DEFAULT 0,
    employee_count INTEGER,
    headquarters_city VARCHAR(100),
    headquarters_state VARCHAR(50),
    headquarters_country VARCHAR(50) DEFAULT 'US',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE locations (
    location_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    location_name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50) DEFAULT 'restaurant',
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50) DEFAULT 'US',
    postal_code VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    business_hours JSONB,
    seating_capacity INTEGER,
    total_taps INTEGER DEFAULT 4,
    active_device_count INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed', 'temporarily_closed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    opened_date DATE,
    closed_date DATE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    location_id UUID REFERENCES locations(location_id),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role_type VARCHAR(50) NOT NULL CHECK (role_type IN ('owner', 'admin', 'manager', 'operator', 'viewer')),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending_invitation')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    plan_type VARCHAR(50) NOT NULL,
    plan_name VARCHAR(100),
    billing_cycle VARCHAR(20) NOT NULL CHECK (billing_cycle IN ('monthly', 'annual')),
    base_price_cents INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'trialing', 'past_due', 'canceled', 'unpaid')),
    trial_start_date DATE,
    trial_end_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    canceled_at TIMESTAMP,
    ended_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE devices (
    device_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL REFERENCES locations(location_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    device_type VARCHAR(50) NOT NULL DEFAULT 'tap_monitor',
    model_number VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    firmware_version VARCHAR(50),
    installation_date DATE,
    installer_name VARCHAR(100),
    last_maintenance_date DATE,
    next_maintenance_due DATE,
    maintenance_interval_days INTEGER DEFAULT 90,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'offline', 'maintenance', 'decommissioned')),
    last_heartbeat_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- High-volume event tables
CREATE TABLE tap_events (
    tap_event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(device_id),
    location_id UUID NOT NULL REFERENCES locations(location_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    event_timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    flow_rate_ml_per_sec DECIMAL(8, 2),
    total_volume_ml DECIMAL(10, 2),
    temperature_celsius DECIMAL(5, 2),
    pressure_psi DECIMAL(6, 2),
    beverage_type VARCHAR(100),
    tap_number INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    device_type VARCHAR(50),
    operating_system VARCHAR(50),
    browser VARCHAR(50),
    browser_version VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    country_code VARCHAR(3),
    region VARCHAR(100),
    city VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE page_views (
    page_view_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES user_sessions(session_id),
    user_id UUID REFERENCES users(user_id),
    page_path VARCHAR(500),
    page_title VARCHAR(255),
    page_category VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    time_on_page_seconds INTEGER,
    referrer_url TEXT,
    referrer_domain VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feature_usage (
    usage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    feature_name VARCHAR(100) NOT NULL,
    feature_category VARCHAR(50),
    feature_version VARCHAR(20),
    usage_timestamp TIMESTAMP NOT NULL,
    usage_duration_seconds INTEGER,
    success_indicator BOOLEAN,
    context_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- External System Integration Tables
-- Stripe Tables
CREATE TABLE stripe_customers (
    id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(255),
    description TEXT,
    currency VARCHAR(3) DEFAULT 'usd',
    default_source VARCHAR(100),
    account_balance INTEGER DEFAULT 0,
    delinquent BOOLEAN DEFAULT FALSE,
    shipping JSONB,
    metadata JSONB,
    created INTEGER NOT NULL,
    updated INTEGER NOT NULL
);

CREATE TABLE stripe_subscriptions (
    id VARCHAR(100) PRIMARY KEY,
    customer VARCHAR(100) REFERENCES stripe_customers(id),
    status VARCHAR(50) NOT NULL,
    billing_cycle_anchor INTEGER,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    collection_method VARCHAR(50) DEFAULT 'charge_automatically',
    current_period_start INTEGER NOT NULL,
    current_period_end INTEGER NOT NULL,
    canceled_at INTEGER,
    cancel_at INTEGER,
    cancellation_details JSONB,
    trial_start INTEGER,
    trial_end INTEGER,
    metadata JSONB,
    created INTEGER NOT NULL,
    start_date INTEGER,
    ended_at INTEGER
);

CREATE TABLE stripe_subscription_items (
    id VARCHAR(100) PRIMARY KEY,
    subscription VARCHAR(100) REFERENCES stripe_subscriptions(id),
    price JSONB NOT NULL,
    quantity INTEGER DEFAULT 1,
    tax_rates JSONB,
    metadata JSONB,
    created INTEGER NOT NULL
);

CREATE TABLE stripe_invoices (
    id VARCHAR(100) PRIMARY KEY,
    customer VARCHAR(100) REFERENCES stripe_customers(id),
    subscription VARCHAR(100) REFERENCES stripe_subscriptions(id),
    invoice_number VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    billing_reason VARCHAR(50),
    collection_method VARCHAR(50),
    amount_due INTEGER NOT NULL,
    amount_paid INTEGER NOT NULL,
    amount_remaining INTEGER NOT NULL,
    subtotal INTEGER NOT NULL,
    total INTEGER NOT NULL,
    tax INTEGER,
    currency VARCHAR(3) DEFAULT 'usd',
    attempt_count INTEGER DEFAULT 0,
    payment_intent VARCHAR(100),
    charge VARCHAR(100),
    period_start INTEGER NOT NULL,
    period_end INTEGER NOT NULL,
    due_date INTEGER,
    status_transitions JSONB,
    auto_advance BOOLEAN DEFAULT TRUE,
    paid BOOLEAN DEFAULT FALSE,
    forgiven BOOLEAN DEFAULT FALSE,
    attempted BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created INTEGER NOT NULL
);

CREATE TABLE stripe_charges (
    id VARCHAR(100) PRIMARY KEY,
    customer VARCHAR(100) REFERENCES stripe_customers(id),
    invoice VARCHAR(100),
    payment_intent VARCHAR(100),
    amount INTEGER NOT NULL,
    amount_captured INTEGER NOT NULL,
    amount_refunded INTEGER NOT NULL,
    application_fee_amount INTEGER,
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL,
    paid BOOLEAN DEFAULT FALSE,
    refunded BOOLEAN DEFAULT FALSE,
    captured BOOLEAN DEFAULT FALSE,
    disputed BOOLEAN DEFAULT FALSE,
    payment_method_details JSONB,
    outcome JSONB,
    failure_code VARCHAR(100),
    failure_message TEXT,
    billing_details JSONB,
    balance_transaction VARCHAR(100),
    receipt_url TEXT,
    metadata JSONB,
    created INTEGER NOT NULL
);

-- HubSpot Tables
CREATE TABLE hubspot_companies (
    id BIGINT PRIMARY KEY,
    properties JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hubspot_contacts (
    id BIGINT PRIMARY KEY,
    properties JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hubspot_deals (
    id BIGINT PRIMARY KEY,
    properties JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Marketing Platform Tables
CREATE TABLE google_ads_campaign_performance (
    campaign_id VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    campaign_name VARCHAR(255),
    campaign_status VARCHAR(50),
    campaign_type VARCHAR(50),
    impressions BIGINT,
    clicks BIGINT,
    cost_micros BIGINT,
    conversions DECIMAL(10, 2),
    conversion_value BIGINT,
    customer_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (campaign_id, date)
);

CREATE TABLE meta_ads_campaign_insights (
    campaign_id VARCHAR(100) NOT NULL,
    date_start DATE NOT NULL,
    campaign_name VARCHAR(255),
    campaign_status VARCHAR(50),
    campaign_objective VARCHAR(50),
    adset_id VARCHAR(100),
    adset_name VARCHAR(255),
    ad_id VARCHAR(100),
    ad_name VARCHAR(255),
    impressions BIGINT,
    clicks BIGINT,
    spend DECIMAL(10, 2),
    actions_value DECIMAL(10, 2),
    actions_count INTEGER,
    video_views INTEGER,
    video_play_actions INTEGER,
    post_engagements INTEGER,
    page_likes INTEGER,
    page_engagement INTEGER,
    account_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (campaign_id, date_start)
);

CREATE TABLE linkedin_ads_campaign_analytics (
    campaign_id VARCHAR(100) NOT NULL,
    date_range JSONB NOT NULL,
    campaign_name VARCHAR(255),
    status VARCHAR(50),
    campaign_type VARCHAR(50),
    objective_type VARCHAR(50),
    impressions BIGINT,
    clicks BIGINT,
    cost_in_usd DECIMAL(10, 2),
    follows INTEGER,
    company_page_clicks INTEGER,
    leads INTEGER,
    lead_generation_mail_contact_info INTEGER,
    lead_generation_mail_interest_clicked INTEGER,
    video_views INTEGER,
    video_completions INTEGER,
    video_first_quartile_completions INTEGER,
    likes INTEGER,
    comments INTEGER,
    shares INTEGER,
    other_engagements INTEGER,
    conversion_value_in_usd DECIMAL(10, 2),
    external_website_conversions INTEGER,
    account_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (campaign_id, (date_range->>'start'))
);

CREATE TABLE iterable_email_events (
    message_id VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    event_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    campaign_id VARCHAR(100),
    template_id VARCHAR(100),
    user_id VARCHAR(100),
    campaign_name VARCHAR(255),
    campaign_type VARCHAR(50),
    subject_line TEXT,
    from_email VARCHAR(255),
    from_name VARCHAR(255),
    content_url TEXT,
    link_url TEXT,
    bounce_reason TEXT,
    unsub_source VARCHAR(100),
    user_agent TEXT,
    ip_address INET,
    city VARCHAR(100),
    region VARCHAR(100),
    country_code VARCHAR(3),
    custom_fields JSONB,
    PRIMARY KEY (message_id, email, event_name, created_at)
);

-- Indexes for performance
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_created_at ON accounts(created_at);

CREATE INDEX idx_locations_account_id ON locations(account_id);
CREATE INDEX idx_locations_status ON locations(status);

CREATE INDEX idx_users_account_id ON users(account_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_last_login ON users(last_login_at);

CREATE INDEX idx_subscriptions_account_id ON subscriptions(account_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

CREATE INDEX idx_devices_location_id ON devices(location_id);
CREATE INDEX idx_devices_account_id ON devices(account_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_heartbeat ON devices(last_heartbeat_at);

-- Partitioned index for high-volume event table
CREATE INDEX idx_tap_events_timestamp ON tap_events(event_timestamp);
CREATE INDEX idx_tap_events_device_id ON tap_events(device_id);
CREATE INDEX idx_tap_events_account_id ON tap_events(account_id);
CREATE INDEX idx_tap_events_event_type ON tap_events(event_type);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_start ON user_sessions(session_start);

CREATE INDEX idx_page_views_session_id ON page_views(session_id);
CREATE INDEX idx_page_views_timestamp ON page_views(timestamp);

CREATE INDEX idx_feature_usage_user_id ON feature_usage(user_id);
CREATE INDEX idx_feature_usage_timestamp ON feature_usage(usage_timestamp);
CREATE INDEX idx_feature_usage_feature ON feature_usage(feature_name);

-- External system indexes
CREATE INDEX idx_stripe_customers_metadata ON stripe_customers USING GIN(metadata);
CREATE INDEX idx_stripe_subscriptions_customer ON stripe_subscriptions(customer);
CREATE INDEX idx_stripe_subscriptions_status ON stripe_subscriptions(status);

CREATE INDEX idx_hubspot_companies_properties ON hubspot_companies USING GIN(properties);
CREATE INDEX idx_hubspot_contacts_properties ON hubspot_contacts USING GIN(properties);
CREATE INDEX idx_hubspot_deals_properties ON hubspot_deals USING GIN(properties);

-- Marketing platform indexes
CREATE INDEX idx_google_ads_date ON google_ads_campaign_performance(date);
CREATE INDEX idx_meta_ads_date ON meta_ads_campaign_insights(date_start);
CREATE INDEX idx_linkedin_ads_date ON linkedin_ads_campaign_analytics((date_range->>'start'));
CREATE INDEX idx_iterable_events_timestamp ON iterable_email_events(created_at);
CREATE INDEX idx_iterable_events_campaign ON iterable_email_events(campaign_id);

-- Update triggers for timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_locations_updated_at BEFORE UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- Missing Tables for Complete 29 Table Coverage
-- Additional tables to complete the full raw data schema

-- Marketing Attribution Table
CREATE TABLE attribution_touchpoints (
    touchpoint_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    account_id UUID REFERENCES accounts(account_id),
    session_id UUID REFERENCES user_sessions(session_id),
    touchpoint_timestamp TIMESTAMP NOT NULL,
    touchpoint_type VARCHAR(50) NOT NULL, -- 'paid_search', 'organic_search', 'social', 'email', 'direct', 'referral'
    channel VARCHAR(50) NOT NULL,
    campaign_id VARCHAR(100),
    campaign_name VARCHAR(255),
    ad_group_id VARCHAR(100),
    ad_group_name VARCHAR(255),
    keyword VARCHAR(255),
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_content VARCHAR(255),
    utm_term VARCHAR(255),
    referrer_url TEXT,
    landing_page_url TEXT,
    conversion_value DECIMAL(10, 2),
    attribution_weight DECIMAL(5, 4) DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Marketing Qualified Leads
CREATE TABLE marketing_qualified_leads (
    lead_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    job_title VARCHAR(100),
    phone VARCHAR(50),
    lead_source VARCHAR(100),
    lead_score INTEGER DEFAULT 0,
    qualification_status VARCHAR(50) DEFAULT 'new' CHECK (qualification_status IN ('new', 'contacted', 'qualified', 'unqualified', 'converted')),
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    form_submission_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    qualified_at TIMESTAMP,
    converted_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Additional Stripe Tables
CREATE TABLE stripe_payment_intents (
    id VARCHAR(100) PRIMARY KEY,
    customer VARCHAR(100) REFERENCES stripe_customers(id),
    amount INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL,
    payment_method VARCHAR(100),
    confirmation_method VARCHAR(50) DEFAULT 'automatic',
    capture_method VARCHAR(50) DEFAULT 'automatic',
    amount_capturable INTEGER DEFAULT 0,
    amount_received INTEGER DEFAULT 0,
    application_fee_amount INTEGER,
    canceled_at INTEGER,
    cancellation_reason VARCHAR(100),
    client_secret VARCHAR(200),
    invoice VARCHAR(100),
    on_behalf_of VARCHAR(100),
    receipt_email VARCHAR(255),
    setup_future_usage VARCHAR(50),
    shipping JSONB,
    statement_descriptor VARCHAR(100),
    statement_descriptor_suffix VARCHAR(50),
    transfer_data JSONB,
    transfer_group VARCHAR(100),
    last_payment_error JSONB,
    next_action JSONB,
    payment_method_options JSONB,
    charges JSONB,
    metadata JSONB,
    created INTEGER NOT NULL
);

CREATE TABLE stripe_events (
    id VARCHAR(100) PRIMARY KEY,
    object VARCHAR(50) NOT NULL DEFAULT 'event',
    type VARCHAR(100) NOT NULL,
    api_version VARCHAR(20),
    livemode BOOLEAN DEFAULT FALSE,
    pending_webhooks INTEGER DEFAULT 0,
    request_id VARCHAR(100),
    request_idempotency_key VARCHAR(100),
    data JSONB NOT NULL,
    previous_attributes JSONB,
    created INTEGER NOT NULL
);

CREATE TABLE stripe_prices (
    id VARCHAR(100) PRIMARY KEY,
    object VARCHAR(50) NOT NULL DEFAULT 'price',
    active BOOLEAN DEFAULT TRUE,
    currency VARCHAR(3) DEFAULT 'usd',
    unit_amount INTEGER,
    unit_amount_decimal DECIMAL(12, 2),
    nickname VARCHAR(255),
    type VARCHAR(50) NOT NULL DEFAULT 'one_time',
    recurring JSONB,
    billing_scheme VARCHAR(50) DEFAULT 'per_unit',
    tiers_mode VARCHAR(50),
    tiers JSONB,
    transform_quantity JSONB,
    lookup_key VARCHAR(255),
    product VARCHAR(100),
    tax_behavior VARCHAR(50),
    metadata JSONB,
    created INTEGER NOT NULL
);
-- Additional HubSpot Table
CREATE TABLE hubspot_engagements (
    id BIGINT PRIMARY KEY,
    engagement JSONB NOT NULL,
    associations JSONB,
    attachments JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Marketing Campaign Tables
CREATE TABLE google_ads_campaigns (
    campaign_id VARCHAR(100) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    campaign_status VARCHAR(50) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL,
    advertising_channel_type VARCHAR(50),
    advertising_channel_sub_type VARCHAR(50),
    bidding_strategy_type VARCHAR(50),
    budget_id VARCHAR(100),
    budget_amount_micros BIGINT,
    budget_delivery_method VARCHAR(50),
    target_cpa_micros BIGINT,
    target_roas DECIMAL(5, 2),
    start_date DATE,
    end_date DATE,
    serving_status VARCHAR(50),
    optimization_score DECIMAL(3, 2),
    customer_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketing_facebook_campaigns (
    campaign_id VARCHAR(100) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    objective VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    buying_type VARCHAR(50) DEFAULT 'AUCTION',
    daily_budget INTEGER,
    lifetime_budget INTEGER,
    bid_strategy VARCHAR(50),
    start_time TIMESTAMP,
    stop_time TIMESTAMP,
    account_id VARCHAR(100),
    created_time TIMESTAMP NOT NULL,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE meta_campaigns (
    campaign_id VARCHAR(100) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    objective VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    buying_type VARCHAR(50) DEFAULT 'AUCTION',
    daily_budget INTEGER,
    lifetime_budget INTEGER,
    bid_strategy VARCHAR(50),
    special_ad_categories JSONB,
    start_time TIMESTAMP,
    stop_time TIMESTAMP,
    account_id VARCHAR(100),
    created_time TIMESTAMP NOT NULL,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketing_linkedin_campaigns (
    campaign_id VARCHAR(100) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    cost_type VARCHAR(50),
    daily_budget_amount DECIMAL(10, 2),
    unit_cost_amount DECIMAL(10, 2),
    bid_amount DECIMAL(10, 2),
    start_at TIMESTAMP,
    end_at TIMESTAMP,
    objective_type VARCHAR(50),
    optimization_target_type VARCHAR(50),
    account_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketing_iterable_campaigns (
    campaign_id VARCHAR(100) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL,
    campaign_state VARCHAR(50) NOT NULL,
    template_id VARCHAR(100),
    created_by_user_id VARCHAR(100),
    updated_by_user_id VARCHAR(100),
    send_size INTEGER,
    start_time_utc TIMESTAMP,
    end_time_utc TIMESTAMP,
    recurring_campaign_id VARCHAR(100),
    workflow_id VARCHAR(100),
    message_medium VARCHAR(50) DEFAULT 'email',
    labels JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Add indexes for the new tables
CREATE INDEX idx_attribution_touchpoints_user_id ON attribution_touchpoints(user_id);
CREATE INDEX idx_attribution_touchpoints_timestamp ON attribution_touchpoints(touchpoint_timestamp);
CREATE INDEX idx_attribution_touchpoints_type ON attribution_touchpoints(touchpoint_type);
CREATE INDEX idx_attribution_touchpoints_channel ON attribution_touchpoints(channel);

CREATE INDEX idx_marketing_qualified_leads_email ON marketing_qualified_leads(email);
CREATE INDEX idx_marketing_qualified_leads_status ON marketing_qualified_leads(qualification_status);
CREATE INDEX idx_marketing_qualified_leads_created ON marketing_qualified_leads(created_at);

CREATE INDEX idx_stripe_payment_intents_customer ON stripe_payment_intents(customer);
CREATE INDEX idx_stripe_payment_intents_status ON stripe_payment_intents(status);
CREATE INDEX idx_stripe_events_type ON stripe_events(type);
CREATE INDEX idx_stripe_events_created ON stripe_events(created);
CREATE INDEX idx_stripe_prices_active ON stripe_prices(active);

CREATE INDEX idx_hubspot_engagements_engagement ON hubspot_engagements USING GIN(engagement);

CREATE INDEX idx_google_ads_campaigns_status ON google_ads_campaigns(campaign_status);
CREATE INDEX idx_facebook_campaigns_status ON marketing_facebook_campaigns(status);
CREATE INDEX idx_meta_campaigns_status ON meta_campaigns(status);
CREATE INDEX idx_linkedin_campaigns_status ON marketing_linkedin_campaigns(status);
CREATE INDEX idx_iterable_campaigns_status ON marketing_iterable_campaigns(campaign_state);

-- Add update triggers for new tables
CREATE TRIGGER update_marketing_qualified_leads_updated_at BEFORE UPDATE ON marketing_qualified_leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_google_ads_campaigns_updated_at BEFORE UPDATE ON google_ads_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_facebook_campaigns_updated_at BEFORE UPDATE ON marketing_facebook_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meta_campaigns_updated_at BEFORE UPDATE ON meta_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_linkedin_campaigns_updated_at BEFORE UPDATE ON marketing_linkedin_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_iterable_campaigns_updated_at BEFORE UPDATE ON marketing_iterable_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hubspot_engagements_updated_at BEFORE UPDATE ON hubspot_engagements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
