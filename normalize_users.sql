-- Create normalized.users table with proper account mapping
-- Core user attributes without derived metrics

DROP TABLE IF EXISTS normalized.users CASCADE;

CREATE TABLE normalized.users (
    user_id INTEGER PRIMARY KEY,
    user_key TEXT NOT NULL,
    account_id VARCHAR NOT NULL,  -- This will store the normalized customer account_id
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    user_role VARCHAR(50),
    role_type_standardized TEXT,
    user_status TEXT,
    access_level INTEGER,
    is_admin_user BOOLEAN,
    is_manager_user BOOLEAN,
    user_created_at DATE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_account FOREIGN KEY (account_id) 
        REFERENCES normalized.customers(account_id)
);

-- Create indexes for performance
CREATE INDEX idx_users_account_id ON normalized.users(account_id);
CREATE INDEX idx_users_email ON normalized.users(email);
CREATE INDEX idx_users_status ON normalized.users(user_status);
CREATE INDEX idx_users_role ON normalized.users(role_type_standardized);
CREATE INDEX idx_users_created ON normalized.users(user_created_at);

-- Insert data from entity table with proper account mapping
INSERT INTO normalized.users (
    user_id,
    user_key,
    account_id,
    email,
    first_name,
    last_name,
    full_name,
    user_role,
    role_type_standardized,
    user_status,
    access_level,
    is_admin_user,
    is_manager_user,
    user_created_at,
    last_login_at
)
SELECT 
    u.user_id,
    u.user_key,
    m.customer_account_id::VARCHAR as account_id,  -- Map to customer account_id
    u.email,
    u.first_name,
    u.last_name,
    u.full_name,
    u.user_role,
    u.role_type_standardized,
    u.user_status,
    u.access_level,
    u.is_admin_user,
    u.is_manager_user,
    u.user_created_at,
    -- Calculate last login from days_since_last_login
    CASE 
        WHEN u.days_since_last_login IS NOT NULL 
        THEN CURRENT_DATE - (u.days_since_last_login || ' days')::INTERVAL
        ELSE NULL
    END as last_login_at
FROM entity.entity_users u
-- Join with account mapping to get customer account_id
INNER JOIN normalized.account_id_mapping m 
    ON u.account_id::VARCHAR = m.subscription_account_id
-- Only include users for accounts that exist in normalized.customers
WHERE EXISTS (
    SELECT 1 FROM normalized.customers c 
    WHERE c.account_id = m.customer_account_id::VARCHAR
);

-- Show results
SELECT COUNT(*) as user_count FROM normalized.users;

-- Show sample data
SELECT 
    user_id,
    user_key,
    account_id,
    email,
    role_type_standardized,
    user_status,
    is_admin_user
FROM normalized.users
LIMIT 5;

-- Show distribution by role
SELECT 
    role_type_standardized,
    COUNT(*) as user_count,
    COUNT(DISTINCT account_id) as accounts
FROM normalized.users
GROUP BY role_type_standardized
ORDER BY user_count DESC;

-- Show users per account distribution
SELECT 
    account_count_range,
    COUNT(*) as num_accounts
FROM (
    SELECT 
        account_id,
        COUNT(*) as user_count,
        CASE 
            WHEN COUNT(*) = 1 THEN '1 user'
            WHEN COUNT(*) BETWEEN 2 AND 5 THEN '2-5 users'
            WHEN COUNT(*) BETWEEN 6 AND 10 THEN '6-10 users'
            ELSE '10+ users'
        END as account_count_range
    FROM normalized.users
    GROUP BY account_id
) user_counts
GROUP BY account_count_range
ORDER BY 
    CASE account_count_range
        WHEN '1 user' THEN 1
        WHEN '2-5 users' THEN 2
        WHEN '6-10 users' THEN 3
        ELSE 4
    END;
