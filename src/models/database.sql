-- Tabla para registrar archivos de entrada
CREATE TABLE input_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('html', 'csv')),
    file_size INTEGER,
    -- Para HTML: path local, para CSV: descripción del origen
    origin_info TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 
        'processing', 
        'processed', 
        'download_error', 
        'upload_error', 
        'failed'
    )),
    total_products INTEGER DEFAULT 0,
    processed_products INTEGER DEFAULT 0,
    error_products INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    error_message TEXT
);

-- Tabla principal de productos
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_file_id INTEGER NOT NULL,
    -- Información básica de tracking
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',
        'scraping', 
        'scraped',
        'image_downloading',
        'image_downloaded', 
        'image_error',
        'uploading',
        'uploaded',
        'upload_error',
        'failed'
    )),
    source_url TEXT,
    scraped_at DATETIME,
    
    -- Información básica del producto
    name TEXT,
    brand TEXT,
    units_per_pack TEXT,
    net_volume TEXT,
    
    -- Características
    flavor TEXT,
    gluten_free BOOLEAN DEFAULT FALSE,
    vegan BOOLEAN DEFAULT FALSE,
    whitening BOOLEAN DEFAULT FALSE,
    format TEXT,
    for_children BOOLEAN DEFAULT FALSE,
    paraben_free BOOLEAN DEFAULT FALSE,
    
    -- Especificaciones técnicas
    operation_notice_number TEXT,
    shelf_life TEXT,
    
    -- Descripción completa
    full_description TEXT,
    
    -- IDs externos (para sincronización)
    external_product_id TEXT,
    woocommerce_post_id INTEGER,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    error_message TEXT,
    
    FOREIGN KEY (input_file_id) REFERENCES input_files(id)
);

-- Tabla para beneficios (relación muchos-a-muchos)
CREATE TABLE product_benefits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    benefit TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Tabla para ingredientes naturales
CREATE TABLE product_natural_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    ingredient TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Tabla para químicos excluidos
CREATE TABLE product_excluded_chemicals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    chemical TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Tabla para imágenes
CREATE TABLE product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    local_path TEXT,
    download_status TEXT DEFAULT 'pending' CHECK (download_status IN (
        'pending', 'downloading', 'downloaded', 'error', 'optimized'
    )),
    download_attempts INTEGER DEFAULT 0,
    file_size INTEGER,
    optimized_path TEXT,
    width INTEGER,
    height INTEGER,
    display_order INTEGER DEFAULT 0,
    downloaded_at DATETIME,
    error_message TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Tabla para logs de procesamiento
CREATE TABLE processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_file_id INTEGER,
    product_id INTEGER,
    log_level TEXT NOT NULL CHECK (log_level IN ('info', 'warning', 'error', 'debug')),
    message TEXT NOT NULL,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (input_file_id) REFERENCES input_files(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabla para configuración de tiendas
CREATE TABLE store_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT NOT NULL,
    base_url TEXT,
    config_json TEXT NOT NULL, -- Configuración específica del scraper
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_input_files_status ON input_files(status);
CREATE INDEX idx_input_files_type ON input_files(file_type);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_input_file ON products(input_file_id);
CREATE INDEX idx_products_external_id ON products(external_product_id);
CREATE INDEX idx_images_product ON product_images(product_id);
CREATE INDEX idx_images_status ON product_images(download_status);
CREATE INDEX idx_logs_timestamp ON processing_logs(created_at);
CREATE INDEX idx_logs_product ON processing_logs(product_id);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_products_timestamp 
AFTER UPDATE ON products 
FOR EACH ROW 
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;