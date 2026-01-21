-- Additional Performance Indexes

-- Supply Chain Data Table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_supply_warehouse_product 
ON supply_chain_data(warehouse_location, product_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_supply_status_expiry 
ON supply_chain_data(status, expiry_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_supply_created 
ON supply_chain_data(created_at DESC);

-- Pipeline Logs
CREATE INDEX IF NOT EXISTS idx_pipeline_status 
ON pipeline_logs(status);

CREATE INDEX IF NOT EXISTS idx_pipeline_created 
ON pipeline_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_name_status 
ON pipeline_logs(pipeline_name, status);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_fact_warehouse_date 
ON fact_inventory_movements(warehouse_key, movement_date_key);

CREATE INDEX IF NOT EXISTS idx_fact_product_date 
ON fact_inventory_movements(product_key, movement_date_key);

-- Text search index
CREATE INDEX IF NOT EXISTS idx_product_name_search 
ON dim_products USING gin(to_tsvector('english', product_name));