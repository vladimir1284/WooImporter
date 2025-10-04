"""
Main processing script for input files.

This script processes HTML and CSV files from the data/input directory,
stores file information in the database, and extracts URLs from CSV files.
"""

import logging
import datetime
from pathlib import Path
import logging

from models.models import create_tables
from utils.input_process import FileProcessor

# Configure logging
def setup_logging():
    """Configure logging to output to logs folder."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_file = (
        logs_dir / f"processing_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    return logging.getLogger(__name__)


logger = setup_logging()


def main():
    """Main entry point for the script."""
    create_tables()
    processor = FileProcessor()
    processor.run()


if __name__ == "__main__":
    main()
