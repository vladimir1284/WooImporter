import logging
import datetime

from models.models import InputFiles
from utils.db_helper import ProductManager
from scrapers.mercadolibre import MercadoLibreScraper

# Set up logging
logger = logging.getLogger(__name__)


def _get_pending_files():
    """
    Retrieve all pending files from the database.

    Returns:
        list: List of InputFiles instances with status 'pending'
    """
    try:
        pending_files = InputFiles.select().where(InputFiles.status == "pending")
        logger.info(f"Found {len(pending_files)} pending files")
        return list(pending_files)
    except Exception as e:
        logger.error(f"Error retrieving pending files: {str(e)}")
        return []


def process_pending_files():
    """
    Main function to retrieve and process all pending files.
    Updates status and tracks progress for each file.
    """
    pending_files = _get_pending_files()

    if not pending_files:
        logger.info("No pending files to process")
        return

    scraper = MercadoLibreScraper()

    for input_file in pending_files:
        logger.info(
            f"Processing file: {input_file.filename} (ID: {input_file.id}, Type: {input_file.file_type})"
        )

        try:
            # Update status to processing
            input_file.status = "processing"
            input_file.save()

            # Determine from_file parameter based on file type
            from_file = input_file.file_type == "html"
            logger.info(
                f"Extracting data from: {input_file.file_path} (from_file={from_file})"
            )

            # Extract data from file with appropriate from_file parameter
            structured_data = scraper.extract(input_file.file_path, from_file=from_file)

            if not structured_data:
                logger.warning(f"No data extracted from {input_file.filename}")
                input_file.status = "failed"
                input_file.error_message = "No data extracted from file"
                input_file.save()
                continue

            # Process each product
            input_file.total_products = 1
            processed_count = 0
            error_count = 0
            try:
                success, product_id, error_msg = ProductManager.store_product_from_json(
                    input_file.id, structured_data
                )

                if success:
                    processed_count += 1
                    logger.debug(f"Successfully stored product {product_id}")
                else:
                    error_count += 1
                    logger.warning(f"Failed to store product: {error_msg}")

                # Update progress
                input_file.processed_products = processed_count
                input_file.error_products = error_count
                input_file.save()

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing individual product: {str(e)}")
                input_file.error_products = error_count
                input_file.save()

            # Final status update
            if error_count == 0:
                input_file.status = "processed"
                input_file.processed_at = datetime.datetime.now()
                logger.info(
                    f"Successfully processed {input_file.filename} with {processed_count} products"
                )
            else:
                input_file.status = "processed" if processed_count > 0 else "failed"
                input_file.processed_at = datetime.datetime.now()
                logger.warning(
                    f"Completed {input_file.filename} with {processed_count} successful "
                    f"and {error_count} failed products"
                )

            input_file.save()

        except Exception as e:
            logger.error(f"Error processing file {input_file.filename}: {str(e)}")
            input_file.status = "failed"
            input_file.error_message = str(e)
            input_file.save()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    process_pending_files()
