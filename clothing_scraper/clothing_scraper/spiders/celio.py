import json
import logging
import re

import scrapy

from clothing_scraper.items import ClothingItem
from api.spiders import PageType
from api.start_urls_enum import SpiderStartUrls

logger = logging.getLogger(__name__)


class CelioSpider(scrapy.Spider):
    name = "celio"
    allowed_domains = ["celio.com"]

    start_urls = SpiderStartUrls.CELIO.value

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'clothing_scraper.downloaders_celio.UndetectedChromeDriverDownloadHandler',
            'https': 'clothing_scraper.downloaders_celio.UndetectedChromeDriverDownloadHandler',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'clothing_scraper.middlewares.CaptchaMiddleware': 543,
        },
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'PYPPETEER_HEADLESS': True,
        'PYPPETEER_LAUNCH_ARGS': [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
        ],
        'DOWNLOAD_DELAY': 10,
    }

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url, callback=self.parse, dont_filter=True
            )

    async def parse(self, response):
        if response.status == 403 or "Access Denied" in response.text:
            logger.error(f"Access Denied for {response.url}. Aborting this page.")
            return

        product_selector = ".product-grid__item .product"
        
        # No need to wait for selector with undetected_chromedriver, content is already loaded
        products = response.css(product_selector)

        if not products:
            logger.warning(f"No products found using selector '{product_selector}' on {response.url}.")
            return

        logger.info(f"Found {len(products)} products on {response.url}.")

        for product_element in products:
            item = ClothingItem()

            # Extract product name
            name = product_element.css('.product-tile__name::text').get()

            # Extract product link
            product_link = product_element.css('a.product-tile__name::attr(href)').get()

            if not name or not product_link:
                logger.warning(f"Could not extract name ({name}) or product link ({product_link}) for product on {response.url}. Skipping item.")
                continue # Skip this item if name or product_link is not found

            item["name"] = name.strip()
            item["product_link"] = response.urljoin(product_link) if product_link else None

            # Extract image URLs
            image_url = product_element.css('.product-tile__image img.tile-image::attr(src)').get()
            item["image_urls"] = [response.urljoin(image_url)] if image_url else []

            # Extract price
            price_str = product_element.css('.product-tile__price .value::text').get()
            if price_str:
                try:
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

            # Extract colors
            colors = []
            for color_element in product_element.css('.color-swatches .swatches__item'):
                color_name = color_element.css('::attr(title)').get()
                if color_name:
                    colors.append(color_name.strip())
            item["colors"] = colors if colors else []

            # Sizes are not available on the listing page
            item["sizes"] = []

            item["description"] = None
            item["page_type"] = PageType.PRODUCT

            yield item
            logger.info(f"  -> Processed product: {item.get('name', 'N/A')}")