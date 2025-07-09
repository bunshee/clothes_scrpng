import json
import logging

import scrapy

from clothing_scraper.items import ClothingItem
from api.spiders import PageType
from api.start_urls_enum import SpiderStartUrls

logger = logging.getLogger(__name__)


class BershkaSpider(scrapy.Spider):
    name = "bershka"
    allowed_domains = ["bershka.com"]

    start_urls = SpiderStartUrls.BERSHKA.value

    async def parse(self, response):
        if response.status == 403 or "Access Denied" in response.text:
            logger.error(f"Access Denied for {response.url}. Aborting this page.")
            return

        product_selector = ".category-product-card"
        try:
            await response.meta["page"].waitForSelector(
                product_selector, {"timeout": 60000}
            )
        except Exception as e:
            logger.warning(
                f"WARNING: No products found after waiting for selector '{product_selector}' on {response.url}: {e}"
            )
            return

        previous_product_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 10  # Increased limit to prevent infinite loops

        while True:
            # Scroll to the bottom
            await response.meta["page"].evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await response.meta["page"].waitFor(3000)  # Wait for new content to load

            # Get the current number of products
            current_products = await response.meta["page"].querySelectorAll(product_selector)
            current_product_count = len(current_products)

            if current_product_count == previous_product_count:
                scroll_attempts += 1
                if scroll_attempts > max_scroll_attempts:
                    logger.info(f"Reached end of scrolling or max scroll attempts ({max_scroll_attempts}) on {response.url}.")
                    break
            else:
                scroll_attempts = 0  # Reset counter if new content loaded
            previous_product_count = current_product_count

        products = await response.meta["page"].querySelectorAll(product_selector)

        if not products:
            logger.warning(f"No products found using selector '{product_selector}' on {response.url}.")
            return

        logger.info(f"Found {len(products)} products on {response.url}.")

        for product_element in products:
            item = ClothingItem()

            # Extract product name from image alt attribute
            name_element = await product_element.querySelector('.product-image img[data-qa-anchor="productGridMainImage"]')
            name = (await (await name_element.getProperty('alt')).jsonValue()).strip() if name_element else None

            # Extract product link
            product_link_element = await product_element.querySelector('.grid-card-link')
            product_link = await (await product_link_element.getProperty('href')).jsonValue() if product_link_element else None

            if not name or not product_link:
                logger.warning(f"Could not extract name ({name}) or product link ({product_link}) for product on {response.url}. Skipping item.")
                continue # Skip this item if name or product_link is not found

            item["name"] = name
            item["product_link"] = response.urljoin(product_link) if product_link else None

            # Extract image URLs
            image_element = await product_element.querySelector('.product-image img[data-qa-anchor="productGridMainImage"]')
            image_url = None
            if image_element:
                # Try data-original first
                data_original = await (await image_element.getProperty('data-original')).jsonValue()
                if data_original:
                    image_url = data_original
                else:
                    # Fallback to src if data-original is not present and not a placeholder GIF
                    src = await (await image_element.getProperty('src')).jsonValue()
                    if src and not src.startswith('data:image/gif'):
                        image_url = src

            item["image_urls"] = [response.urljoin(image_url)] if image_url else []

            # Extract price
            price_element = await product_element.querySelector('.current-price-elem')
            if price_element:
                try:
                    price_str = await (await price_element.getProperty('innerText')).jsonValue()
                    import re
                    price_match = re.search(r'(\d+[\.,]\d+)', price_str)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '.').strip()
                        item["price"] = float(price_str)
                    else:
                        item["price"] = None
                except Exception as e:
                    logger.warning(f"Could not extract price for {item.get('name', 'N/A')}: {e}")
                    item["price"] = None
            else:
                item["price"] = None

            # Simulate hover to reveal colors and sizes
            await product_element.hover()
            await response.meta["page"].waitFor(500) # Small wait for elements to appear

            # Extract colors
            color_elements = await product_element.querySelectorAll('.color-cut')
            colors = []
            for color_element in color_elements:
                color_name = None
                # Try to get color from input's name attribute
                input_element = await color_element.querySelector('input')
                if input_element:
                    color_name = await (await input_element.getProperty('name')).jsonValue()
                
                # If not found, try to get color from image's alt attribute
                if not color_name:
                    img_element = await color_element.querySelector('img')
                    if img_element:
                        color_name = await (await img_element.getProperty('alt')).jsonValue()

                if color_name:
                    colors.append(color_name)
            item["colors"] = colors if colors else []

            # Extract sizes
            size_elements = await product_element.querySelectorAll('.ui--size-dot-list .text__label')
            sizes = []
            for size_element in size_elements:
                size_value = await (await size_element.getProperty('innerText')).jsonValue()
                if size_value:
                    sizes.append(size_value.strip())
            item["sizes"] = sizes if sizes else []

            # Move mouse away to reset hover state (optional, but good practice)
            await response.meta["page"].mouse.move(0, 0) 

            item["description"] = None
            item["page_type"] = PageType.PRODUCT

            yield item
            logger.info(f"  -> Processed product: {item.get('name', 'N/A')}")