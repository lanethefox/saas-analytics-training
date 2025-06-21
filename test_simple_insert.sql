-- Simple test data to verify platform functionality
INSERT INTO raw.app_database_accounts (id, name, email, created_date, business_type, location_count)
VALUES 
(1, 'Test Bar & Grill', 'test@bar.com', '2024-01-01', 'Restaurant', 2),
(2, 'Sample Pub', 'sample@pub.com', '2024-01-15', 'Bar', 1);

INSERT INTO raw.app_database_users (id, email, first_name, last_name, role, created_date, customer_id)
VALUES
(1, 'john@test.com', 'John', 'Doe', 'Admin', '2024-01-01', 1),
(2, 'jane@test.com', 'Jane', 'Smith', 'Manager', '2024-01-01', 1),
(3, 'bob@sample.com', 'Bob', 'Johnson', 'Admin', '2024-01-15', 2);

INSERT INTO raw.app_database_locations (id, customer_id, name, address, city, state, country, zip_code, location_type, created_date)
VALUES
(1, 1, 'Test Bar Main', '123 Main St', 'New York', 'NY', 'USA', '10001', 'Restaurant', '2024-01-01'),
(2, 1, 'Test Bar Downtown', '456 Downtown Ave', 'New York', 'NY', 'USA', '10002', 'Restaurant', '2024-01-02'),
(3, 2, 'Sample Pub Location', '789 Pub St', 'Chicago', 'IL', 'USA', '60601', 'Bar', '2024-01-15');

INSERT INTO raw.app_database_devices (id, serial_number, device_type, customer_id, location_id, status, created_date)
VALUES
(1, 'TAP-001', 'Beer Tap', 1, 1, 'Active', '2024-01-01'),
(2, 'TAP-002', 'Beer Tap', 1, 1, 'Active', '2024-01-01'),
(3, 'TAP-003', 'Wine Tap', 1, 2, 'Active', '2024-01-02'),
(4, 'TAP-004', 'Beer Tap', 2, 3, 'Active', '2024-01-15');

INSERT INTO raw.app_database_subscriptions (id, customer_id, plan_name, status, start_date, current_term_start)
VALUES
(1, 1, 'Professional', 'Active', '2024-01-01', '2024-01-01'),
(2, 2, 'Starter', 'Active', '2024-01-15', '2024-01-15');