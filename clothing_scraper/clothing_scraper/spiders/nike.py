import json
import logging

import scrapy

from clothing_scraper.items import ClothingItem
from api.spiders import PageType
from api.start_urls_enum import SpiderStartUrls

logger = logging.getLogger(__name__)


class NikeSpider(scrapy.Spider):
    name = "nike"
    allowed_domains = ["nike.com"]

    start_urls = SpiderStartUrls.NIKE.value

    async def parse(self, response):
        if response.status == 403 or "Access Denied" in response.text:
            logger.error(f"Access Denied for {response.url}. Aborting this page.")
            return

        # Nike uses infinite scrolling, so we need to scroll down to load all products
        # The product selector is 'product-card'
        product_selector = ".product-card"
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

            # Extract product name
            name_element = await product_element.querySelector('.product-card__title')
            item["name"] = (await (await name_element.getProperty('innerText')).jsonValue()).strip() if name_element else None

            # Extract product link
            product_link_element = await product_element.querySelector('.product-card__link-overlay')
            product_link = await (await product_link_element.getProperty('href')).jsonValue() if product_link_element else None
            item["product_link"] = response.urljoin(product_link) if product_link else None

            # Extract image URLs
            image_element = await product_element.querySelector('.product-card__hero-image')
            image_url = await (await image_element.getProperty('src')).jsonValue() if image_element else None
            item["image_urls"] = [response.urljoin(image_url)] if image_url else []

            # Extract price
            price_element = await product_element.querySelector('.product-price.is--current-price')
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

            # Sizes and colors are typically on the product detail page, not the listing page.
            # For now, we'll leave them as empty lists or None.
            item["sizes"] = []
            item["colors"] = []
            item["description"] = None
            item["page_type"] = PageType.PRODUCT

            yield item
            logger.info(f"  -> Processed product: {item.get('name', 'N/A')}")