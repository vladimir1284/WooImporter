from typing import Optional, List
from pathlib import Path
import csv
import logging

# Import your models and manager (adjust import path as needed)
from models.models import InputFiles
from utils.db_helper import ProductManager

# Logger will be configured externally
logger = logging.getLogger(__name__)


class FileProcessor:
    """Process input files and store records in database."""

    def __init__(self, input_dir: str = "data/input"):
        self.input_dir = Path(input_dir)
        self.input_dir.mkdir(parents=True, exist_ok=True)

    def get_file_type(self, filename: str) -> Optional[str]:
        """Determine file type based on extension."""
        ext = Path(filename).suffix.lower()
        if ext == ".html":
            return "html"
        elif ext == ".csv":
            return "csv"
        return None

    def get_file_info(self, file_path: Path) -> tuple:
        """Get file information including size and origin info."""
        file_size = file_path.stat().st_size

        # For HTML files, origin info is the file path
        # For CSV files, this will be populated with URLs during processing
        origin_info = str(file_path) if file_path.suffix.lower() == ".html" else None

        return file_size, origin_info

    def process_html_file(self, file_path: Path) -> bool:
        """
        Process HTML file - simply store file information in database.

        Args:
            file_path: Path to the HTML file

        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            logger.info(f"Processing HTML file: {file_path}")

            # Check if file already exists in database
            existing_file = (
                InputFiles.select()
                .where(
                    (InputFiles.filename == file_path.name)
                    & (InputFiles.file_type == "html")
                )
                .first()
            )

            if existing_file:
                logger.info(f"HTML file already exists in database: {file_path.name}")
                return True

            # Get file information
            file_size, origin_info = self.get_file_info(file_path)

            # Create database record
            input_file_record = ProductManager.create_input_file(
                filename=file_path.name,
                file_path=str(file_path),
                file_type="html",
                origin_info=origin_info,
            )

            logger.info(f"Successfully stored HTML file info: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error processing HTML file {file_path}: {e}")
            return False

    def extract_urls_from_csv(self, file_path: Path) -> List[str]:
        """
        Extract URLs from CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            List[str]: List of unique URLs found in the CSV
        """
        urls = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Look for URL in common column names
                    url = None
                    for key in ["url", "URL", "link", "Link", "website", "Website"]:
                        if key in row and row[key].strip():
                            url = row[key].strip()
                            break

                    # If no URL found in named columns, try first column
                    if not url and row:
                        first_value = list(row.values())[0].strip()
                        if first_value and first_value.startswith(
                            ("http://", "https://")
                        ):
                            url = first_value

                    if url and url not in urls:  # Avoid duplicates within the same file
                        urls.append(url)

            logger.info(f"Extracted {len(urls)} unique URLs from CSV: {file_path.name}")
            return urls

        except Exception as e:
            logger.error(f"Error extracting URLs from CSV {file_path}: {e}")
            return []

    def url_exists_in_database(self, url: str) -> bool:
        """
        Check if a URL already exists in the database.

        Args:
            url: URL to check

        Returns:
            bool: True if URL exists, False otherwise
        """
        try:
            existing_record = (
                InputFiles.select()
                .where(
                    (InputFiles.origin_info == url) & (InputFiles.file_type == "csv")
                )
                .first()
            )
            return existing_record is not None
        except Exception as e:
            logger.error(f"Error checking if URL exists in database: {e}")
            return False

    def process_csv_file(self, file_path: Path) -> bool:
        """
        Process CSV file - extract URLs and store each as separate record if not exists.

        Args:
            file_path: Path to the CSV file

        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            logger.info(f"Processing CSV file: {file_path}")

            # Extract URLs from CSV
            urls = self.extract_urls_from_csv(file_path)

            if not urls:
                logger.warning(f"No URLs found in CSV file: {file_path.name}")
                return True

            # Get file information
            file_size, _ = self.get_file_info(file_path)

            # Process each URL individually
            new_urls_count = 0
            skipped_urls_count = 0

            for url in urls:
                # Check if URL already exists in database
                if self.url_exists_in_database(url):
                    logger.debug(f"URL already exists in database, skipping: {url}")
                    skipped_urls_count += 1
                    continue

                # Create separate database record for each URL
                input_file_record = ProductManager.create_input_file(
                    filename=file_path.name,  # Original CSV filename
                    file_path=str(file_path),  # Original CSV file path
                    file_type="csv",
                    origin_info=url,  # Store individual URL
                )
                
                new_urls_count += 1

            logger.info(
                f"CSV processing completed: {new_urls_count} new URLs stored, "
                f"{skipped_urls_count} duplicate URLs skipped from file: {file_path.name}"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
            return False

    def process_file(self, file_path: Path) -> bool:
        """
        Process a single file and store in database.

        Args:
            file_path: Path to the file to process

        Returns:
            bool: True if processing completed successfully
        """
        try:
            filename = file_path.name
            file_type = self.get_file_type(filename)

            if not file_type:
                logger.warning(f"Ignoring file with unsupported format: {filename}")
                return False

            # Process based on file type
            if file_type == "html":
                return self.process_html_file(file_path)
            else:  # csv
                return self.process_csv_file(file_path)

        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            return False

    def find_files_to_process(self) -> list:
        """Find all HTML and CSV files in input directory."""
        files = []
        for ext in ["*.html", "*.csv"]:
            files.extend(self.input_dir.glob(ext))
            files.extend(
                self.input_dir.glob(ext.upper())
            )  # Handle uppercase extensions

        # Filter out files already in database (any status)
        existing_files = InputFiles.select(InputFiles.filename).where(
            InputFiles.filename.in_([f.name for f in files])
        )

        existing_filenames = [ef.filename for ef in existing_files]
        new_files = [f for f in files if f.name not in existing_filenames]

        return new_files

    def run(self):
        """Run the file processor once and exit."""
        logger.info("Starting file processor")

        files_to_process = self.find_files_to_process()

        if not files_to_process:
            logger.info("No new files to process")
            return

        logger.info(f"Found {len(files_to_process)} new files to process")

        successful_processing = 0
        for file_path in files_to_process:
            logger.info(f"Processing: {file_path.name}")
            if self.process_file(file_path):
                successful_processing += 1

        logger.info(
            f"Processing completed. Successfully processed {successful_processing}/{len(files_to_process)} files"
        )
