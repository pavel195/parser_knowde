CREATE USER knowde_user WITH PASSWORD 'postgres';
CREATE DATABASE knowde_db;
GRANT ALL PRIVILEGES ON DATABASE knowde_db TO knowde_user;

\c knowde_db

-- Создаем необходимые таблицы
CREATE TABLE IF NOT EXISTS brands (
    brand_name VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    products_extracted BOOLEAN DEFAULT FALSE,
    products_count INTEGER DEFAULT 0,
    last_processed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(255) PRIMARY KEY,
    brand_name VARCHAR(255) REFERENCES brands(brand_name),
    data JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Даем права на таблицы
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO knowde_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO knowde_user; 

-- После создания таблиц добавим проверку
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('brands', 'products', 'extraction_jobs')
ORDER BY table_name, ordinal_position; 