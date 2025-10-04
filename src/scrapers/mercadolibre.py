"""
MercadoLibre-specific web scraper for product data extraction.
"""

import re
import logging
from typing import Dict, List, Optional
from web_scraper import WebScraper, BaseProductExtractor

logger = logging.getLogger(__name__)


class MercadoLibreScraper(BaseProductExtractor):
    """
    MercadoLibre-specific product data scraper.
    """

    def __init__(self):
        super().__init__()

    def extract(self, source: str, from_file: bool = False) -> Dict:
        """
        Extract MercadoLibre product data from URL or file.

        Args:
            source: MercadoLibre product URL or file path
            from_file: If True, source is treated as file path

        Returns:
            Structured product data dictionary
        """
        logger.info(f"Starting MercadoLibre extraction from: {source}")

        # Get HTML content
        html_content = self.scraper.get_content(source, from_file)
        if not html_content:
            logger.error("Failed to get HTML content")
            return self.base_structure

        # Parse HTML
        soup = self.scraper.parse_html(html_content)

        # Extract raw product data
        raw_product_data = self._extract_raw_data(soup)

        # Parse into structured format
        structured_data = self._parse_structured_data(raw_product_data)

        # Add source information
        if not from_file:
            structured_data["source_url"] = source

        logger.info("MercadoLibre extraction completed successfully")
        return structured_data

    def _extract_raw_data(self, soup) -> Dict:
        """
        Extract raw product data from BeautifulSoup object.

        Args:
            soup: BeautifulSoup object of product page

        Returns:
            Dictionary with raw extracted data
        """
        product_data = {}

        # Extract product title
        product_data["title"] = self.scraper.extract_text(soup, "h1.ui-pdp-title")

        # Extract product images
        product_data["images"] = self._extract_images(soup)

        # Extract highlighted features
        product_data["highlighted_features"] = self._extract_highlighted_features(soup)

        # Extract technical specifications
        product_data["specifications"] = self._extract_specifications(soup)

        # Extract product description
        product_data["description"] = self._extract_description(soup)

        return product_data

    def _extract_images(self, soup) -> List[str]:
        """Extract product images from the gallery"""
        images = []

        # Find all image elements in the gallery
        img_elements = soup.find_all("img", class_="ui-pdp-image")

        for img in img_elements:
            src = img.get("src") or img.get("data-zoom")
            if src and not src.startswith("data:image/gif"):
                # Clean up the URL to get the highest quality version
                clean_src = self.scraper.clean_image_url(src)
                if clean_src and clean_src not in images:
                    images.append(clean_src)

        return images

    def _extract_highlighted_features(self, soup) -> List[str]:
        """Extract the highlighted features section"""
        features = []

        # Find the highlighted features list
        features_list = soup.find(
            "ul", class_="ui-vpp-highlighted-specs__features-list"
        )

        if features_list:
            feature_items = self.scraper.extract_list(
                features_list,
                "li.ui-vpp-highlighted-specs__features-list-item",
                extract_text=True,
            )
            features.extend(feature_items)

        return features

    def _extract_specifications(self, soup) -> Dict:
        """Extract detailed product specifications"""
        specs = {}

        # Extract from the key-value pairs in the attributes section
        key_value_elements = soup.find_all(
            "div", class_="ui-vpp-highlighted-specs__key-value"
        )

        for element in key_value_elements:
            labels_div = element.find(
                "div", class_="ui-vpp-highlighted-specs__key-value__labels"
            )
            if labels_div:
                key_value_text = labels_div.get_text(strip=True)
                if ":" in key_value_text:
                    key, value = key_value_text.split(":", 1)
                    specs[key.strip()] = value.strip()

        # Extract from the detailed specifications tables
        tables = soup.find_all("table", class_="andes-table")

        for table in tables:
            table_specs = self.scraper.extract_key_value_pairs(
                table, "th.andes-table__header", "td.andes-table__column"
            )
            specs.update(table_specs)

        return specs

    def _extract_description(self, soup) -> Optional[str]:
        """Extract product description"""
        description_div = soup.find("div", class_="ui-pdp-description")

        if description_div:
            content = description_div.find("p", {"data-testid": "content"})
            if content:
                return content.get_text(strip=True)

        return None

    def _parse_structured_data(self, product_data: Dict) -> Dict:
        """Parse the extracted data into a more structured format"""
        structured = self.scraper.get_base_data_structure()

        # Basic info from title
        if product_data["title"]:
            structured["basic_info"]["name"] = product_data["title"]

        # Parse highlighted features
        for feature in product_data.get("highlighted_features", []):
            if "Unidades por pack" in feature:
                structured["basic_info"]["units_per_pack"] = feature.replace(
                    "Unidades por pack:", ""
                ).strip()
            elif "Volumen neto" in feature:
                structured["basic_info"]["net_volume"] = feature.replace(
                    "Volumen neto:", ""
                ).strip()
            elif "Sabor" in feature:
                structured["features"]["flavor"] = feature.replace("Sabor", "").strip()
            elif "Beneficios" in feature:
                structured["features"]["benefits"] = feature.replace(
                    "Beneficios:", ""
                ).strip()
            elif "libre de gluten" in feature.lower():
                structured["features"]["gluten_free"] = True
            elif "vegano" in feature.lower():
                structured["features"]["vegan"] = True
            elif "Blanqueamiento" in feature:
                structured["features"]["whitening"] = True

        # Parse specifications
        specs = product_data.get("specifications", {})
        for key, value in specs.items():
            key_lower = key.lower()

            if "marca" in key_lower:
                structured["basic_info"]["brand"] = value
            elif "formato" in key_lower:
                structured["features"]["format"] = value
            elif "volumen neto" in key_lower:
                structured["basic_info"]["net_volume"] = value
            elif "sabor" in key_lower:
                structured["features"]["flavor"] = value
            elif "beneficios" in key_lower:
                structured["features"]["benefits"] = value.split(", ")
            elif "infantil" in key_lower:
                structured["features"]["for_children"] = value.lower() == "sí"
            elif "gluten" in key_lower:
                structured["features"]["gluten_free"] = value.lower() == "sí"
            elif "parabenos" in key_lower:
                structured["features"]["paraben_free"] = value.lower() == "sí"
            elif "vegano" in key_lower:
                structured["features"]["vegan"] = value.lower() == "sí"
            elif "vida útil" in key_lower:
                structured["technical_specs"]["shelf_life"] = value
            elif "número de aviso" in key_lower:
                structured["technical_specs"]["operation_notice_number"] = value

        # Extract composition from description
        if product_data["description"]:
            structured["composition"] = self._extract_composition_from_description(
                product_data["description"]
            )

        structured["images"] = product_data.get("images", [])
        structured["full_description"] = product_data.get("description")

        return structured

    def _extract_composition_from_description(self, description: str) -> Dict:
        """Extract composition information from description"""
        composition = {}

        # Look for ingredients section
        if "Ingredientes Naturales:" in description:
            parts = description.split("Ingredientes Naturales:")
            if len(parts) > 1:
                ingredients_text = parts[1].split("(No Contiene Químicos Nocivos):")[0]
                composition["natural_ingredients"] = [
                    ing.strip() for ing in ingredients_text.split(",") if ing.strip()
                ]

        # Look for what it doesn't contain
        if "(No Contiene Químicos Nocivos):" in description:
            parts = description.split("(No Contiene Químicos Nocivos):")
            if len(parts) > 1:
                excluded_text = parts[1].split("Vegana")[0]  # Stop at "Vegana"
                # Extract each "Sin X" item
                excluded_items = re.findall(r"-Sin\s+([^-\n]+)", excluded_text)
                composition["excluded_chemicals"] = [
                    item.strip() for item in excluded_items
                ]

        return composition


def main():
    """Example usage of the MercadoLibre scraper"""
    # Example usage - you would replace this with actual HTML content
    scraper = MercadoLibreScraper()

    # Read from file (current implementation)
    structured_data = scraper.extract("data/input/product_page.html", from_file=True)

    # Print the results
    print("STRUCTURED PRODUCT DATA:")
    print("=" * 50)
    import json

    print(json.dumps(structured_data, indent=2, ensure_ascii=False))

    # Example of how to use with URL (when ready)
    # url = "https://www.mercadolibre.com.mx/product-page-example"
    # structured_data = scraper.extract(url, from_file=False)


if __name__ == "__main__":
    main()
