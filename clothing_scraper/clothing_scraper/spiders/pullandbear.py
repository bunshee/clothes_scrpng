import scrapy
import logging
import random
import re

logger = logging.getLogger(__name__)

class PullandbearSpider(scrapy.Spider):
    name = "pullandbear"
    allowed_domains = ["pullandbear.com"]

    async def start(self):
        start_urls = [
            "https://www.pullandbear.com/fr/femme-n6221",
            "https://www.pullandbear.com/fr/homme-n6228",
            "https://www.pullandbear.com/fr/femme-n6417",
        ]

        for url in start_urls:
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

        # Extract product data
        product_card_selector = "div.c-tile--product"
        product_elements = response.css(product_card_selector)
        product_count = len(product_elements)
        logger.info(f"Found {product_count} products on the category page.")
        logger.info("Starting to process products...")

        for i, product_element in enumerate(product_elements):
            item = ClothingItem()
            try:
                # Name
                name = product_element.css(".product-name::text").get()
                item['name'] = name.strip() if name else None

                # Product Link
                product_link = product_element.css("a.carousel-item-container::attr(href)").get()
                if product_link and not product_link.startswith("http"):
                    item['product_link'] = response.urljoin(product_link)
                else:
                    item['product_link'] = product_link

                # Price
                price_text = product_element.css("price-element::text").get()
                if price_text:
                    clean_price = re.sub(r'[^\d,\.]', '', price_text).replace(',', '.')
                    try:
                        item['price'] = float(clean_price)
                    except ValueError:
                        item['price'] = None
                else:
                    item['price'] = None

                # Colors
                colors = []
                color_image_alts = product_element.css("ul.product-card-colors__list li img::attr(alt)").getall()
                colors.extend([c.strip() for c in color_image_alts if c and c.strip()])
                color_title_texts = product_element.css("div.color-container div.title-color::text").getall()
                colors.extend([c.strip() for c in color_title_texts if c and c.strip()])
                item['colors'] = list(set(colors)) if colors else None

                item['sizes'] = None
                item['description'] = None

                yield item
                logger.info(f"  -> Processed product {i + 1}/{product_count}: {item.get('name', 'N/A')}")

            except Exception as e:
                logger.error(f"  Error processing product card {i + 1} on {response.url}: {e}")