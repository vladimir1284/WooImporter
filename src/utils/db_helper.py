import datetime
from models.models import (
    InputFiles,
    ProcessingLogs,
    ProductBenefits,
    ProductCategories,
    ProductExcludedChemicals,
    ProductImages,
    ProductNaturalIngredients,
    Products,
)
from peewee import DatabaseError


class ProductManager:
    @staticmethod
    def create_input_file(filename, file_path, file_type, origin_info=None):
        return InputFiles.create(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            origin_info=origin_info,
            status="pending",
        )

    @staticmethod
    def update_input_file_status(file_id, status, error_message=None):
        update_data = {"status": status}
        if status == "processed":
            update_data["processed_at"] = datetime.datetime.now()
        if error_message:
            update_data["error_message"] = error_message

        InputFiles.update(update_data).where(InputFiles.id == file_id).execute()

    @staticmethod
    def create_product(input_file_id, **product_data):
        return Products.create(input_file_id=input_file_id, **product_data)

    @staticmethod
    def add_product_benefits(product_id, benefits):
        for benefit in benefits:
            ProductBenefits.create(product_id=product_id, benefit=benefit)

    @staticmethod
    def add_natural_ingredients(product_id, ingredients):
        for ingredient in ingredients:
            ProductNaturalIngredients.create(
                product_id=product_id, ingredient=ingredient
            )

    @staticmethod
    def add_categories(product_id, categories):
        for category in categories:
            ProductCategories.create(product_id=product_id, category=category)

    @staticmethod
    def add_excluded_chemicals(product_id, chemicals):
        for chemical in chemicals:
            ProductExcludedChemicals.create(product_id=product_id, chemical=chemical)

    @staticmethod
    def add_product_images(product_id, image_urls):
        for order, url in enumerate(image_urls):
            ProductImages.create(
                product_id=product_id, image_url=url, display_order=order
            )

    @staticmethod
    def log_message(
        input_file_id=None, product_id=None, log_level="info", message="", details=None
    ):
        ProcessingLogs.create(
            input_file_id=input_file_id,
            product_id=product_id,
            log_level=log_level,
            message=message,
            details=details,
        )

    @staticmethod
    def store_product_from_json(input_file_id, product_json):
        """
        Store a product from JSON data using transaction for data consistency

        Args:
            input_file_id (int): ID of the input file
            product_json (dict): Product data in the specified JSON format

        Returns:
            tuple: (success: bool, product_id: int, error_message: str)
        """
        try:
            with Products._meta.database.atomic() as transaction:
                # Extract basic info
                basic_info = product_json.get("basic_info", {})
                features = product_json.get("features", {})
                composition = product_json.get("composition", {})
                technical_specs = product_json.get("technical_specs", {})

                # Create main product record
                product_data = {
                    "name": basic_info.get("name"),
                    "brand": basic_info.get("brand"),
                    "units_per_pack": basic_info.get("units_per_pack"),
                    "net_volume": basic_info.get("net_volume"),
                    "flavor": features.get("flavor"),
                    "gluten_free": features.get("gluten_free", False),
                    "vegan": features.get("vegan", False),
                    "whitening": features.get("whitening", False),
                    "format": features.get("format"),
                    "for_children": features.get("for_children", False),
                    "paraben_free": features.get("paraben_free", False),
                    "operation_notice_number": technical_specs.get(
                        "operation_notice_number"
                    ),
                    "shelf_life": technical_specs.get("shelf_life"),
                    "full_description": product_json.get("full_description"),
                    "source_url": product_json.get("source_url"),
                    "scraped_at": product_json.get("scraped_at"),
                    "status": "scraped",  # Since we're storing scraped data
                }

                product = ProductManager.create_product(input_file_id, **product_data)
                product_id = product.id

                # Add benefits (from features.benefits)
                benefits = features.get("benefits", [])
                if benefits:
                    ProductManager.add_product_benefits(product_id, benefits)

                # Add natural ingredients
                natural_ingredients = composition.get("natural_ingredients", [])
                if natural_ingredients:
                    ProductManager.add_natural_ingredients(
                        product_id, natural_ingredients
                    )

                # Add excluded chemicals
                excluded_chemicals = composition.get("excluded_chemicals", [])
                if excluded_chemicals:
                    ProductManager.add_excluded_chemicals(
                        product_id, excluded_chemicals
                    )

                # Add categories
                categories = product_json.get("categories", [])
                if categories:
                    ProductManager.add_categories(product_id, categories)

                # Add images
                images = product_json.get("images", [])
                if images:
                    ProductManager.add_product_images(product_id, images)

                # Log successful creation
                ProductManager.log_message(
                    input_file_id=input_file_id,
                    product_id=product_id,
                    log_level="info",
                    message=f"Product successfully stored from JSON: {basic_info.get('name', 'Unknown')}",
                    details=f"Created product with {len(benefits)} benefits, {len(natural_ingredients)} ingredients, {len(excluded_chemicals)} excluded chemicals, {len(categories)} categories, and {len(images)} images",
                )

                return True, product_id, None

        except DatabaseError as e:
            # Log database error
            error_msg = f"Database error while storing product: {str(e)}"
            ProductManager.log_message(
                input_file_id=input_file_id,
                log_level="error",
                message=error_msg,
                details=str(e),
            )
            return False, None, error_msg

        except Exception as e:
            # Log general error
            error_msg = f"Unexpected error while storing product: {str(e)}"
            ProductManager.log_message(
                input_file_id=input_file_id,
                log_level="error",
                message=error_msg,
                details=str(e),
            )
            return False, None, error_msg

    @staticmethod
    def store_multiple_products_from_json(input_file_id, products_json_list):
        """
        Store multiple products from a list of JSON data

        Args:
            input_file_id (int): ID of the input file
            products_json_list (list): List of product JSON data

        Returns:
            dict: Results with success count and errors
        """
        success_count = 0
        error_count = 0
        errors = []

        for i, product_json in enumerate(products_json_list):
            success, product_id, error_message = ProductManager.store_product_from_json(
                input_file_id, product_json
            )

            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(
                    {
                        "index": i,
                        "error": error_message,
                        "product_data": product_json.get("basic_info", {}).get(
                            "name", "Unknown"
                        ),
                    }
                )

        # Update input file statistics
        try:
            InputFiles.update(
                processed_products=success_count,
                error_products=error_count,
                total_products=success_count + error_count,
            ).where(InputFiles.id == input_file_id).execute()

            # Log batch results
            ProductManager.log_message(
                input_file_id=input_file_id,
                log_level="info",
                message=f"Batch processing completed: {success_count} successful, {error_count} failed",
                details=f"Total products processed: {success_count + error_count}",
            )

        except Exception as e:
            ProductManager.log_message(
                input_file_id=input_file_id,
                log_level="error",
                message=f"Error updating input file statistics: {str(e)}",
                details=str(e),
            )

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors,
        }
