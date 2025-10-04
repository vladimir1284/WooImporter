from peewee import *
import datetime

database = SqliteDatabase("data/output/products.db")  


class BaseModel(Model):
    class Meta:
        database = database


class InputFiles(BaseModel):
    filename = CharField()
    file_path = CharField()
    file_type = CharField(constraints=[Check("file_type IN ('html', 'csv')")])
    file_size = IntegerField(null=True)
    origin_info = TextField(null=True)
    status = CharField(
        default="pending",
        constraints=[
            Check(
                "status IN ('pending', 'processing', 'processed', 'download_error', 'upload_error', 'failed')"
            )
        ],
    )
    total_products = IntegerField(default=0)
    processed_products = IntegerField(default=0)
    error_products = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.datetime.now)
    processed_at = DateTimeField(null=True)
    error_message = TextField(null=True)

    class Meta:
        table_name = "input_files"


class Products(BaseModel):
    input_file = ForeignKeyField(
        InputFiles, backref="products", column_name="input_file_id"
    )

    # Tracking information
    status = CharField(
        default="pending",
        constraints=[
            Check(
                "status IN ('pending', 'scraping', 'scraped', 'image_downloading', 'image_downloaded', 'image_error', 'uploading', 'uploaded', 'upload_error', 'failed')"
            )
        ],
    )
    source_url = TextField(null=True)
    scraped_at = DateTimeField(null=True)

    # Basic product information
    name = TextField(null=True)
    brand = CharField(null=True)
    units_per_pack = CharField(null=True)
    net_volume = CharField(null=True)

    # Characteristics
    flavor = CharField(null=True)
    gluten_free = BooleanField(default=False)
    vegan = BooleanField(default=False)
    whitening = BooleanField(default=False)
    format = CharField(null=True)
    for_children = BooleanField(default=False)
    paraben_free = BooleanField(default=False)

    # Technical specifications
    operation_notice_number = CharField(null=True)
    shelf_life = CharField(null=True)

    # Full description
    full_description = TextField(null=True)

    # External IDs (for synchronization)
    external_product_id = CharField(null=True)
    woocommerce_post_id = IntegerField(null=True)

    # Metadata
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    processed_at = DateTimeField(null=True)
    error_message = TextField(null=True)

    class Meta:
        table_name = "products"


class ProductBenefits(BaseModel):
    product = ForeignKeyField(
        Products, backref="benefits", column_name="product_id", on_delete="CASCADE"
    )
    benefit = CharField()

    class Meta:
        table_name = "product_benefits"


class ProductNaturalIngredients(BaseModel):
    product = ForeignKeyField(
        Products,
        backref="natural_ingredients",
        column_name="product_id",
        on_delete="CASCADE",
    )
    ingredient = CharField()

    class Meta:
        table_name = "product_natural_ingredients"


class ProductExcludedChemicals(BaseModel):
    product = ForeignKeyField(
        Products,
        backref="excluded_chemicals",
        column_name="product_id",
        on_delete="CASCADE",
    )
    chemical = CharField()

    class Meta:
        table_name = "product_excluded_chemicals"


class ProductImages(BaseModel):
    product = ForeignKeyField(
        Products, backref="images", column_name="product_id", on_delete="CASCADE"
    )
    image_url = TextField()
    local_path = TextField(null=True)
    download_status = CharField(
        default="pending",
        constraints=[
            Check(
                "download_status IN ('pending', 'downloading', 'downloaded', 'error', 'optimized')"
            )
        ],
    )
    download_attempts = IntegerField(default=0)
    file_size = IntegerField(null=True)
    optimized_path = TextField(null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)
    display_order = IntegerField(default=0)
    downloaded_at = DateTimeField(null=True)
    error_message = TextField(null=True)

    class Meta:
        table_name = "product_images"


class ProcessingLogs(BaseModel):
    input_file = ForeignKeyField(
        InputFiles, backref="logs", column_name="input_file_id", null=True
    )
    product = ForeignKeyField(
        Products, backref="logs", column_name="product_id", null=True
    )
    log_level = CharField(
        constraints=[Check("log_level IN ('info', 'warning', 'error', 'debug')")]
    )
    message = TextField()
    details = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = "processing_logs"


class StoreConfigs(BaseModel):
    store_name = CharField()
    base_url = TextField(null=True)
    config_json = TextField()  # Store-specific scraper configuration
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = "store_configs"


# Function to create tables and indexes
def create_tables():
    with database:
        database.create_tables(
            [
                InputFiles,
                Products,
                ProductBenefits,
                ProductNaturalIngredients,
                ProductExcludedChemicals,
                ProductImages,
                ProcessingLogs,
                StoreConfigs,
            ]
        )

        # Create indexes
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_input_files_status ON input_files(status);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_input_files_type ON input_files(file_type);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_products_input_file ON products(input_file_id);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_products_external_id ON products(external_product_id);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_images_product ON product_images(product_id);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_images_status ON product_images(download_status);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON processing_logs(created_at);"
        )
        database.execute_sql(
            "CREATE INDEX IF NOT EXISTS idx_logs_product ON processing_logs(product_id);"
        )


# Function to update product timestamp (equivalent to the SQL trigger)
def update_product_timestamp(product_id):
    Products.update(updated_at=datetime.datetime.now()).where(
        Products.id == product_id
    ).execute()


# Usage example
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")
