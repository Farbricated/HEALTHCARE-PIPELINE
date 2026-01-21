-- Drop existing tables if recreating
-- DROP TABLE IF EXISTS fact_inventory_movements CASCADE;
-- DROP TABLE IF EXISTS dim_products CASCADE;
-- DROP TABLE IF EXISTS dim_warehouses CASCADE;
-- DROP TABLE IF EXISTS dim_suppliers CASCADE;
-- DROP TABLE IF EXISTS dim_date CASCADE;

-- Dimension: Products
CREATE TABLE IF NOT EXISTS dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    unit_of_measure VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dimension: Warehouses
CREATE TABLE IF NOT EXISTS dim_warehouses (
    warehouse_key SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(100) UNIQUE NOT NULL,
    warehouse_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    capacity INTEGER,
    manager_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dimension: Suppliers
CREATE TABLE IF NOT EXISTS dim_suppliers (
    supplier_key SERIAL PRIMARY KEY,
    supplier_id VARCHAR(100) UNIQUE NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    rating DECIMAL(3,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week_of_year INTEGER,
    day_of_month INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);

-- Fact: Inventory Movements
CREATE TABLE IF NOT EXISTS fact_inventory_movements (
    movement_id BIGSERIAL PRIMARY KEY,
    product_key INTEGER REFERENCES dim_products(product_key),
    warehouse_key INTEGER REFERENCES dim_warehouses(warehouse_key),
    supplier_key INTEGER REFERENCES dim_suppliers(supplier_key),
    movement_date_key INTEGER REFERENCES dim_date(date_key),
    
    -- Movement details
    batch_number VARCHAR(100),
    movement_type VARCHAR(50), -- 'IN', 'OUT', 'TRANSFER', 'ADJUSTMENT', 'EXPIRED'
    quantity_change INTEGER,
    unit_price DECIMAL(10, 2),
    total_value DECIMAL(15, 2),
    
    -- Additional info
    expiry_date DATE,
    manufacture_date DATE,
    days_until_expiry INTEGER,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Materialized View: Current Inventory
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_current_inventory AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    w.warehouse_name,
    w.location,
    SUM(f.quantity_change) as current_quantity,
    AVG(f.unit_price) as avg_unit_price,
    SUM(f.total_value) as total_value,
    MIN(f.expiry_date) as earliest_expiry,
    MAX(f.created_at) as last_updated
FROM fact_inventory_movements f
JOIN dim_products p ON f.product_key = p.product_key
JOIN dim_warehouses w ON f.warehouse_key = w.warehouse_key
WHERE p.is_active = true
GROUP BY p.product_id, p.product_name, p.category, w.warehouse_name, w.location
HAVING SUM(f.quantity_change) > 0;

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_fact_product ON fact_inventory_movements(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_warehouse ON fact_inventory_movements(warehouse_key);
CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_inventory_movements(movement_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_movement_type ON fact_inventory_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_fact_expiry ON fact_inventory_movements(expiry_date);
CREATE INDEX IF NOT EXISTS idx_fact_batch ON fact_inventory_movements(batch_number);

CREATE INDEX IF NOT EXISTS idx_mv_product ON mv_current_inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_mv_warehouse ON mv_current_inventory(warehouse_name);

-- Partitioning for fact table (by date for better performance)
-- Note: This requires PostgreSQL 10+
-- CREATE TABLE fact_inventory_movements_2024 PARTITION OF fact_inventory_movements
-- FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_current_inventory()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_current_inventory;
END;
$$ LANGUAGE plpgsql;

-- Function to populate date dimension
CREATE OR REPLACE FUNCTION populate_date_dimension(start_date DATE, end_date DATE)
RETURNS void AS $$
DECLARE
    current_date DATE := start_date;
BEGIN
    WHILE current_date <= end_date LOOP
        INSERT INTO dim_date (
            date_key,
            date,
            year,
            quarter,
            month,
            month_name,
            week_of_year,
            day_of_month,
            day_of_week,
            day_name,
            is_weekend,
            is_holiday
        ) VALUES (
            TO_CHAR(current_date, 'YYYYMMDD')::INTEGER,
            current_date,
            EXTRACT(YEAR FROM current_date),
            EXTRACT(QUARTER FROM current_date),
            EXTRACT(MONTH FROM current_date),
            TO_CHAR(current_date, 'Month'),
            EXTRACT(WEEK FROM current_date),
            EXTRACT(DAY FROM current_date),
            EXTRACT(DOW FROM current_date),
            TO_CHAR(current_date, 'Day'),
            EXTRACT(DOW FROM current_date) IN (0, 6),
            false  -- Customize for actual holidays
        )
        ON CONFLICT (date_key) DO NOTHING;
        
        current_date := current_date + INTERVAL '1 day';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Populate date dimension for 2024-2027
SELECT populate_date_dimension('2024-01-01'::DATE, '2027-12-31'::DATE);

-- Data Quality Checks Table
CREATE TABLE IF NOT EXISTS data_quality_checks (
    check_id BIGSERIAL PRIMARY KEY,
    check_name VARCHAR(255),
    check_type VARCHAR(100),
    table_name VARCHAR(100),
    column_name VARCHAR(100),
    expected_value TEXT,
    actual_value TEXT,
    status VARCHAR(50),
    error_message TEXT,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);