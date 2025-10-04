import datetime
from models.models import InputFiles, ProcessingLogs, ProductBenefits, ProductExcludedChemicals, ProductImages, ProductNaturalIngredients, Products


class ProductManager:
    @staticmethod
    def create_input_file(filename, file_path, file_type, origin_info=None):
        return InputFiles.create(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            origin_info=origin_info,
            status="pending"
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
