"""
General web scraper utilities for fetching and parsing web content.
Provides common extraction patterns and a base structure for scraped data.
"""

from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional

from utils.page_downloader import get_html_source

# Logger will be configured externally
logger = logging.getLogger(__name__)


class WebScraper:
    """
    A general web scraper that can fetch content from URLs or files
    and provides common extraction utilities.
    """

    def __init__(self, addition_delay=10000, timeout=30000):
        """
        Initialize the web scraper.

        Args:
            addition_delay: Settle time for downloading source of the page
            timeout: Request timeout in seconds
        """
        self.addition_delay = addition_delay
        self.timeout = timeout

    def get_content(self, source: str, from_file: bool = False) -> Optional[str]:
        """
        Get HTML content from either a URL or a local file.

        Args:
            source: URL or file path
            from_file: If True, source is treated as a file path

        Returns:
            HTML content as string or None if error
        """
        try:
            if from_file:
                logger.info(f"Reading content from file: {source}")
                with open(source, "r", encoding="utf-8") as file:
                    return file.read()
            else:
                logger.info(f"Fetching content from URL: {source}")
                html = get_html_source(
                    source, addition_delay=self.addition_delay, timeout=self.timeout
                )
                return html

        except Exception as e:
            logger.error(f"Error getting content from {source}: {str(e)}")
            return None

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content into BeautifulSoup object.

        Args:
            html_content: HTML content as string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, "html.parser")

    def extract_text(
        self, element, selector: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract text from an element using CSS selector.

        Args:
            element: BeautifulSoup element to search within
            selector: CSS selector string
            default: Default value if not found

        Returns:
            Extracted text or default value
        """
        found_element = element.select_one(selector)
        return found_element.get_text(strip=True) if found_element else default

    def extract_attribute(
        self, element, selector: str, attribute: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract attribute value from an element using CSS selector.

        Args:
            element: BeautifulSoup element to search within
            selector: CSS selector string
            attribute: Attribute name to extract
            default: Default value if not found

        Returns:
            Attribute value or default value
        """
        found_element = element.select_one(selector)
        return found_element.get(attribute) if found_element else default

    def extract_list(self, element, selector: str, extract_text: bool = True) -> List:
        """
        Extract list of elements or their text.

        Args:
            element: BeautifulSoup element to search within
            selector: CSS selector string
            extract_text: If True, extract text from each element

        Returns:
            List of extracted values
        """
        elements = element.select(selector)
        if extract_text:
            return [
                elem.get_text(strip=True)
                for elem in elements
                if elem.get_text(strip=True)
            ]
        return elements

    def extract_key_value_pairs(
        self, element, key_selector: str, value_selector: str
    ) -> Dict:
        """
        Extract key-value pairs from elements.

        Args:
            element: BeautifulSoup element to search within
            key_selector: CSS selector for keys
            value_selector: CSS selector for values

        Returns:
            Dictionary of key-value pairs
        """
        pairs = {}
        keys = element.select(key_selector)
        values = element.select(value_selector)

        for key_elem, value_elem in zip(keys, values):
            key = key_elem.get_text(strip=True)
            value = value_elem.get_text(strip=True)
            if key and value:
                pairs[key] = value

        return pairs

    def clean_image_url(
        self, url: str, base_domain: str = "https://http2.mlstatic.com"
    ) -> str:
        """
        Clean and standardize image URLs.

        Args:
            url: Original image URL
            base_domain: Base domain for relative URLs

        Returns:
            Cleaned image URL
        """
        if not url:
            return ""

        # Remove webp format and get the base image
        if "webp" in url:
            url = url.replace(".webp", ".jpg")
            url = url.replace("D_Q_NP", "D_NQ_NP")
            url = url.replace("-R.", "-F.")

        # Ensure we have a full URL
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = base_domain + url

        return url

    def get_base_data_structure(self) -> Dict:
        """
        Return the base structure for scraped product data.

        Returns:
            Base dictionary structure for product data
        """
        return {
            "basic_info": {
                "name": None,
                "brand": None,
                "units_per_pack": None,
                "net_volume": None,
            },
            "features": {},
            "composition": {},
            "technical_specs": {},
            "images": [],
            "full_description": None,
            "source_url": None,
            "scraped_at": None,
        }


class BaseProductExtractor:
    """
    Base class for product-specific extractors.
    """

    def __init__(self):
        self.scraper = WebScraper()
        self.base_structure = self.scraper.get_base_data_structure()

    def extract(self, source: str, from_file: bool = False) -> Dict:
        """
        Extract product data from source.

        Args:
            source: URL or file path
            from_file: If True, source is treated as file path

        Returns:
            Structured product data
        """
        raise NotImplementedError("Subclasses must implement extract method")
