-- Supply Chain Main Table
CREATE TABLE IF NOT EXISTS supply_chain_data (
    id BIGSERIAL PRIMARY KEY,
    product_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    unit_price DECIMAL(10, 2),
    warehouse_location VARCHAR(200),
    expiry_date DATE,
    manufacture_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_product_id ON supply_chain_data(product_id);
CREATE INDEX IF NOT EXISTS idx_batch_number ON supply_chain_data(batch_number);
CREATE INDEX IF NOT EXISTS idx_expiry_date ON supply_chain_data(expiry_date);
CREATE INDEX IF NOT EXISTS idx_status ON supply_chain_data(status);

-- Pipeline logs table
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100),
    status VARCHAR(50),
    records_processed INTEGER,
    errors_count INTEGER,
    execution_time_seconds DECIMAL(10, 2),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);