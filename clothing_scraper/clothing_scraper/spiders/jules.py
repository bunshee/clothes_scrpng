import scrapy
import logging
import random
import re

logger = logging.getLogger(__name__)

class JulesSpider(scrapy.Spider):
    name = "jules"
    allowed_domains = ["jules.com"]
    start_urls = ["https://www.jules.com/"]

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

        # Extract product data
        product_selector = "div.product-tile"
        product_elements = response.css(product_selector)
        logger.info(f"Found {len(product_elements)} products on {response.url}.")

        for product_element in product_elements:
            item = ClothingItem()
            try:
                # Name
                name = product_element.css(".product-tile__name::text").get()
                item['name'] = name.strip() if name else None

                # Product Link
                product_link = product_element.css("a.product-tile__link::attr(href)").get()
                if product_link and not product_link.startswith("http"):
                    item['product_link'] = response.urljoin(product_link)
                else:
                    item['product_link'] = product_link

                # Price
                price_text = product_element.css(".product-tile__price::text").get()
                if price_text:
                    clean_price = re.sub(r'[^\d,\.]', '', price_text).replace(',', '.')
                    try:
                        item['price'] = float(clean_price)
                    except ValueError:
                        item['price'] = None
                else:
                    item['price'] = None

                # Image URLs
                image_src = product_element.css("img.product-tile__image::attr(src)").get()
                item['image_urls'] = [image_src] if image_src else None

                item['colors'] = None
                item['sizes'] = None
                item['description'] = None

                yield item
                logger.info(f"  -> Processed product: {item.get('name', 'N/A')}")

            except Exception as e:
                logger.error(f"Error processing product card: {e}")