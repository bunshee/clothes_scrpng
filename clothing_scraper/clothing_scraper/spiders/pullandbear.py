import json
import logging

import scrapy

from clothing_scraper.items import (
    ClothingItem,  # Assuming ClothingItem is defined here or in items.py
)
from api.spiders import PageType
from api.start_urls_enum import SpiderStartUrls

logger = logging.getLogger(__name__)


class PullandbearSpider(scrapy.Spider):
    name = "pullandbear"
    allowed_domains = ["pullandbear.com"]

    start_urls = SpiderStartUrls.PULLANDBEAR.value

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url, meta={"pyppeteer": True}, callback=self.parse, dont_filter=True
            )

    async def parse(self, response):
        if response.status == 403 or "Access Denied" in response.text:
            logger.error(f"Access Denied for {response.url}. Aborting this page.")
            return

        product_selector = "legacy-product"
        try:
            await response.meta["page"].waitForSelector(
                product_selector, {"timeout": 60000}
            )
        except Exception as e:
            logger.warning(
                f"WARNING: No products found after waiting for selector '{product_selector}' on {response.url}: {e}"
            )
            return

        # Scroll down to load all products
        previous_product_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 20 # Increased limit to prevent infinite loops

        while True:
            # Scroll to the bottom
            await response.meta["page"].evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await response.meta["page"].waitFor(7000)  # Increased wait time for new content to load

            # Get the current number of products
            current_products = await response.meta["page"].querySelectorAll(product_selector)
            current_product_count = len(current_products)

            if current_product_count == previous_product_count:
                scroll_attempts += 1
                if scroll_attempts > max_scroll_attempts:
                    logger.info(f"Reached end of scrolling or max scroll attempts ({max_scroll_attempts}) on {response.url}.")
                    break
            else:
                scroll_attempts = 0 # Reset counter if new content loaded
            previous_product_count = current_product_count

        # Select all product containers using Pyppeteer (after all scrolling attempts)
        products = await response.meta["page"].querySelectorAll(product_selector)

        if not products:
            logger.warning(f"No products found using selector '{product_selector}' on {response.url}.")
            return

        logger.info(f"Found {len(products)} products on {response.url}.")

        for product_element in products:
            item = ClothingItem()

            # Extract product name
            name_element = await product_element.querySelector('.product-name')
            item["name"] = (await (await name_element.getProperty('innerText')).jsonValue()).strip() if name_element else None

            # Extract product link
            product_link_element = await product_element.querySelector('.carousel-item-container')
            product_link = await (await product_link_element.getProperty('href')).jsonValue() if product_link_element else None
            item["product_link"] = response.urljoin(product_link) if product_link else None

            # Extract image URLs
            image_elements = await product_element.querySelectorAll('.carousel-item img')
            image_urls = []
            for img_element in image_elements:
                src = await (await img_element.getProperty('src')).jsonValue()
                if src:
                    image_urls.append(response.urljoin(src))
            item["image_urls"] = image_urls if image_urls else []

            # Extract price using page.evaluate on the specific product element
            price_element = await product_element.querySelector('.price-container price-element')
            if price_element:
                try:
                    # Get innerHTML of the price-element
                    price_html = await (await price_element.getProperty('innerHTML')).jsonValue()
                    import re
                    price_match = re.search(r'(\d+[\.,]\d+)', price_html)
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

            # Extract sizes
            size_elements = await product_element.querySelectorAll('.c-quick-item--size input')
            sizes = []
            for size_element in size_elements:
                value = await (await size_element.getProperty('value')).jsonValue()
                if value:
                    sizes.append(value)
            item["sizes"] = sizes if sizes else []

            # Extract colors
            color_elements = await product_element.querySelectorAll('.item-color input')
            colors = []
            for color_element in color_elements:
                title = await (await color_element.getProperty('title')).jsonValue()
                if title:
                    colors.append(title)
            item["colors"] = colors if colors else []

            item["description"] = None # Description is not in this HTML snippet
            item["page_type"] = PageType.PRODUCT

            yield item
            logger.info(f"  -> Processed product: {item.get('name', 'N/A')}")