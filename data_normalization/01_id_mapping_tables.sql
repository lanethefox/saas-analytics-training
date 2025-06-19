-- 01_id_mapping_tables.sql
-- Phase 1: Create ID Mapping Infrastructure
-- ==========================================
-- This script creates the mapping tables needed to reconcile
-- account IDs across all entities in the platform

-- Create schema for normalized data
CREATE SCHEMA IF NOT EXISTS normalized;

-- Drop existing mapping tables if they exist
DROP TABLE IF EXISTS normalized.account_id_mapping CASCADE;
DROP TABLE IF EXISTS normalized.id_generation_rules CASCADE;

-- ========================================
-- Master Account ID Mapping Table
-- ========================================
CREATE TABLE normalized.account_id_mapping (
    -- Original IDs from different sources
    customer_account_id VARCHAR(50),          -- From entity_customers (0-99)
    subscription_account_id VARCHAR(50),      -- From entity_subscriptions (10000000+)
    user_account_id INTEGER,                  -- From entity_users
    location_account_id INTEGER,              -- From entity_locations
    
    -- New normalized ID
    normalized_account_id VARCHAR(50) PRIMARY KEY,
    
    -- Metadata
    mapping_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mapping_source VARCHAR(50),
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    
    -- Mapping logic used
    mapping_method VARCHAR(100),
    manual_override BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Create indexes for performance
CREATE INDEX idx_map_customer_id ON normalized.account_id_mapping(customer_account_id);
CREATE INDEX idx_map_subscription_id ON normalized.account_id_mapping(subscription_account_id);
CREATE INDEX idx_map_user_id ON normalized.account_id_mapping(user_account_id);
CREATE INDEX idx_map_location_id ON normalized.account_id_mapping(location_account_id);

-- ========================================
-- ID Generation Rules Table
-- ========================================
CREATE TABLE normalized.id_generation_rules (
    rule_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    id_pattern VARCHAR(100) NOT NULL,
    id_prefix VARCHAR(10),
    id_length INTEGER DEFAULT 10,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert standard ID generation rules
INSERT INTO normalized.id_generation_rules (entity_type, id_pattern, id_prefix, id_length, description)
VALUES 
    ('account', 'ACC{YYYYMMDD}{SEQ}', 'ACC', 15, 'Account ID: ACC + date + sequence'),
    ('subscription', 'SUB{YYYYMMDD}{SEQ}', 'SUB', 15, 'Subscription ID: SUB + date + sequence'),
    ('device', 'DEV{YYYYMMDD}{SEQ}', 'DEV', 15, 'Device ID: DEV + date + sequence'),
    ('user', 'USR{YYYYMMDD}{SEQ}', 'USR', 15, 'User ID: USR + date + sequence'),
    ('location', 'LOC{YYYYMMDD}{SEQ}', 'LOC', 15, 'Location ID: LOC + date + sequence');

-- ========================================
-- Populate Initial Mapping Table
-- ========================================

-- Step 1: Map customers to their potential subscriptions
WITH customer_base AS (
    SELECT 
        account_id::VARCHAR as customer_account_id,
        company_name,
        customer_tier,
        created_at
    FROM entity.entity_customers
),
subscription_candidates AS (
    SELECT 
        account_id::VARCHAR as subscription_account_id,
        MIN(monthly_recurring_revenue) as min_mrr,
        MAX(monthly_recurring_revenue) as max_mrr,
        COUNT(*) as sub_count,
        STRING_AGG(DISTINCT subscription_status, ', ') as statuses
    FROM entity.entity_subscriptions
    GROUP BY account_id
),
-- Create mapping based on logical rules
mapping_logic AS (
    SELECT 
        c.customer_account_id,
        -- Map subscription IDs by adding 10000000 to customer ID
        CASE 
            WHEN c.customer_account_id ~ '^[0-9]+$' 
            THEN (10000000 + c.customer_account_id::INTEGER)::VARCHAR
            ELSE NULL
        END as derived_subscription_id,
        c.customer_tier,
        c.created_at
    FROM customer_base c
)
INSERT INTO normalized.account_id_mapping (
    customer_account_id,
    subscription_account_id,
    normalized_account_id,
    mapping_method,
    confidence_score
)
SELECT 
    m.customer_account_id,
    m.derived_subscription_id,
    'ACC' || LPAD(m.customer_account_id, 10, '0') as normalized_account_id,
    'Derived: customer_id + 10000000' as mapping_method,
    CASE 
        WHEN s.subscription_account_id IS NOT NULL THEN 0.95
        ELSE 0.50
    END as confidence_score
FROM mapping_logic m
LEFT JOIN subscription_candidates s 
    ON m.derived_subscription_id = s.subscription_account_id;

-- Step 2: Add orphaned subscriptions (no matching customer)
INSERT INTO normalized.account_id_mapping (
    subscription_account_id,
    normalized_account_id,
    mapping_method,
    confidence_score
)
SELECT DISTINCT
    s.account_id::VARCHAR,
    'ACC' || LPAD(
        CASE 
            WHEN s.account_id ~ '^[0-9]+$' AND s.account_id::BIGINT >= 10000000
            THEN (s.account_id::BIGINT - 10000000)::VARCHAR
            ELSE s.account_id
        END, 10, '0'
    ) as normalized_account_id,
    'Orphaned subscription - reverse engineered' as mapping_method,
    0.70 as confidence_score
FROM entity.entity_subscriptions s
WHERE NOT EXISTS (
    SELECT 1 
    FROM normalized.account_id_mapping m 
    WHERE m.subscription_account_id = s.account_id::VARCHAR
)
AND s.account_id IS NOT NULL;

-- Step 3: Map users to accounts
UPDATE normalized.account_id_mapping m
SET user_account_id = u.mapped_user_id
FROM (
    SELECT DISTINCT
        u.account_id as mapped_user_id,
        CASE 
            WHEN u.account_id < 100 THEN u.account_id::VARCHAR
            WHEN u.account_id >= 10000000 THEN (u.account_id - 10000000)::VARCHAR
            ELSE u.account_id::VARCHAR
        END as derived_customer_id
    FROM entity.entity_users u
    WHERE u.account_id IS NOT NULL
) u
WHERE m.customer_account_id = u.derived_customer_id
   OR m.normalized_account_id = 'ACC' || LPAD(u.derived_customer_id, 10, '0');

-- Step 4: Map locations to accounts
UPDATE normalized.account_id_mapping m
SET location_account_id = l.mapped_location_id
FROM (
    SELECT DISTINCT
        l.account_id as mapped_location_id,
        CASE 
            WHEN l.account_id < 100 THEN l.account_id::VARCHAR
            WHEN l.account_id >= 10000000 THEN (l.account_id - 10000000)::VARCHAR
            ELSE l.account_id::VARCHAR
        END as derived_customer_id
    FROM entity.entity_locations l
    WHERE l.account_id IS NOT NULL
) l
WHERE m.customer_account_id = l.derived_customer_id
   OR m.normalized_account_id = 'ACC' || LPAD(l.derived_customer_id, 10, '0');

-- ========================================
-- Create validation views
-- ========================================

-- View to check mapping completeness
CREATE OR REPLACE VIEW normalized.mapping_validation AS
SELECT 
    COUNT(*) as total_mappings,
    COUNT(customer_account_id) as mapped_customers,
    COUNT(subscription_account_id) as mapped_subscriptions,
    COUNT(user_account_id) as mapped_users,
    COUNT(location_account_id) as mapped_locations,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN confidence_score < 0.8 THEN 1 END) as low_confidence_mappings
FROM normalized.account_id_mapping;

-- View to identify unmapped entities
CREATE OR REPLACE VIEW normalized.unmapped_entities AS
SELECT 'customer' as entity_type, COUNT(*) as unmapped_count
FROM entity.entity_customers c
WHERE NOT EXISTS (
    SELECT 1 FROM normalized.account_id_mapping m 
    WHERE m.customer_account_id = c.account_id::VARCHAR
)
UNION ALL
SELECT 'subscription', COUNT(*)
FROM entity.entity_subscriptions s
WHERE NOT EXISTS (
    SELECT 1 FROM normalized.account_id_mapping m 
    WHERE m.subscription_account_id = s.account_id::VARCHAR
)
AND s.account_id IS NOT NULL
UNION ALL
SELECT 'user', COUNT(*)
FROM entity.entity_users u
WHERE NOT EXISTS (
    SELECT 1 FROM normalized.account_id_mapping m 
    WHERE m.user_account_id = u.account_id
)
AND u.account_id IS NOT NULL
UNION ALL
SELECT 'location', COUNT(*)
FROM entity.entity_locations l
WHERE NOT EXISTS (
    SELECT 1 FROM normalized.account_id_mapping m 
    WHERE m.location_account_id = l.account_id
)
AND l.account_id IS NOT NULL;

-- ========================================
-- Summary Report
-- ========================================
SELECT 'ID Mapping Infrastructure Created Successfully' as status;
SELECT * FROM normalized.mapping_validation;
SELECT * FROM normalized.unmapped_entities WHERE unmapped_count > 0;
