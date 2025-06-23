-- Create device_telemetry table for IoT device monitoring data
CREATE TABLE IF NOT EXISTS raw.device_telemetry (
    id UUID PRIMARY KEY,
    device_id UUID NOT NULL,
    location_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for common queries
    CONSTRAINT fk_device_telemetry_device 
        FOREIGN KEY (device_id) 
        REFERENCES raw.app_database_devices(id),
    CONSTRAINT fk_device_telemetry_location 
        FOREIGN KEY (location_id) 
        REFERENCES raw.app_database_locations(id),
    CONSTRAINT fk_device_telemetry_customer 
        FOREIGN KEY (customer_id) 
        REFERENCES raw.app_database_accounts(id)
);

-- Create indexes for performance
CREATE INDEX idx_device_telemetry_device_id ON raw.device_telemetry(device_id);
CREATE INDEX idx_device_telemetry_timestamp ON raw.device_telemetry(timestamp);
CREATE INDEX idx_device_telemetry_device_timestamp ON raw.device_telemetry(device_id, timestamp);
CREATE INDEX idx_device_telemetry_metrics ON raw.device_telemetry USING GIN(metrics);

-- Add table comment
COMMENT ON TABLE raw.device_telemetry IS 'IoT device telemetry data including CPU, memory, network metrics and health scores';