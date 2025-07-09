import scrapy
import logging
import re

from clothing_scraper.items import ClothingItem
from api.spiders import PageType
from api.start_urls_enum import SpiderStartUrls

logger = logging.getLogger(__name__)

class CandaSpider(scrapy.Spider):
    name = "canda"
    allowed_domains = ["www.c-and-a.com"]
    start_urls = SpiderStartUrls.CANDA.value

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={'pyppeteer': True},
                callback=self.parse,
                dont_filter=True
            )

    async def parse(self, response):
        # Check if we landed on a blocked page right away
        if response.status == 403 or "Access Denied" in response.text:
            logger.error(f"Access Denied for {response.url}. Aborting this page.")
            return

        product_selector = "li[data-qa=\"ProductTile\"]"
        try:
            await response.meta["page"].waitForSelector(
                product_selector, {"timeout": 60000}
            )
        except Exception as e:
            logger.warning(
                f"WARNING: No products found after waiting for selector '{product_selector}' on {response.url}: {e}"
            )
            return

        # Scroll down to load all products (infinite scrolling)
        previous_product_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 10 # Limit to prevent infinite loops

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
            try:
                # Name
                name_element = await product_element.querySelector("div[data-qa=\"ProductName\"]")
                name = (await (await name_element.getProperty('innerText')).jsonValue()).strip() if name_element else None
                item['name'] = name

                # Product Link
                product_link_element = await product_element.querySelector("a[data-qa=\"Link\"]")
                product_link = await (await product_link_element.getProperty('href')).jsonValue() if product_link_element else None
                item['product_link'] = response.urljoin(product_link) if product_link else None

                # Price
                price_element = await product_element.querySelector("div[data-qa=\"ProductPrice\"]")
                if price_element:
                    price_text = await (await price_element.getProperty('innerText')).jsonValue()
                    if price_text:
                        clean_price = re.sub(r'[^\d,\.]', '', price_text).replace(',', '.')
                        try:
                            item['price'] = float(clean_price)
                        except ValueError:
                            item['price'] = None
                    else:
                        item['price'] = None
                else:
                    item['price'] = None

                # Image URLs
                image_element = await product_element.querySelector("picture img")
                image_src = await (await image_element.getProperty('src')).jsonValue() if image_element else None
                item['image_urls'] = [response.urljoin(image_src)] if image_src else []

                # Colors
                color_elements = await product_element.querySelectorAll("span[data-qa=\"ColorSwatch\"] img")
                colors = []
                for color_el in color_elements:
                    color_name = await (await color_el.getProperty('alt')).jsonValue()
                    if color_name:
                        colors.append(color_name.strip())
                item['colors'] = colors if colors else []

                item['sizes'] = [] # Sizes are not available on the listing page
                item['description'] = None

                item['page_type'] = PageType.PRODUCT
                yield item
                logger.info(f"  -> Processed product: {item.get('name', 'N/A')}")

            except Exception as e:
                logger.error(f"Error processing product card: {e}")