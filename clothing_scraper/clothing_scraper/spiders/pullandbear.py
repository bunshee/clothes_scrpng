import scrapy
import logging
import random
import re
import json
from clothing_scraper.items import ClothingItem # Assuming ClothingItem is defined here or in items.py

logger = logging.getLogger(__name__)

class PullandbearSpider(scrapy.Spider):
    name = "pullandbear"
    allowed_domains = ["pullandbear.com"]

    async def start(self):
        start_urls = [
            "https://www.pullandbear.com/fr/femme/soldes/vetements/pantalons-n7104",
            "https://www.pullandbear.com/fr/femme/soldes/vetements/robes-et-combinaisons-n7102",
            "https://www.pullandbear.com/fr/femme/soldes/vetements/t-shirts-et-tops-n7097?celement=1030207188",
            "https://www.pullandbear.com/fr/femme/soldes/vetements/jupes-et-shorts-n7103",
            "https://www.pullandbear.com/fr/femme/soldes/chaussures-n7106",
            "https://www.pullandbear.com/fr/homme/soldes/vetements/t-shirts-et-polos-n7087",
            "https://www.pullandbear.com/fr/homme/soldes/vetements/bermudas-n7092",
            "https://www.pullandbear.com/fr/homme/soldes/vetements/jeans-n7818",
            "https://www.pullandbear.com/fr/homme/soldes/vetements/sweats-n7089",
            "https://www.pullandbear.com/fr/homme/soldes/chaussures-n7093",
        ]

        for url in start_urls:
            yield scrapy.Request(
                url,
                meta={'pyppeteer': True},
                callback=self.parse,
                dont_filter=True
            )

    async def parse(self, response):
        if response.status == 403 or "Access Denied" in response.text:
            logger.error(f"Access Denied for {response.url}. Aborting this page.")
            return

        product_selector = "grid-product"
        try:
            await response.meta['page'].waitForSelector(product_selector, {'timeout': 60000})
        except Exception as e:
            logger.warning(f"WARNING: No products found after waiting for selector '{product_selector}' on {response.url}: {e}")
            return

        # Use page.evaluate to get all product info at once
        try:
            products_info = await response.meta['page'].evaluate('''() => {
                const products = Array.from(document.querySelectorAll('grid-product'));
                return products.map(p => p.productInfo);
            }''')
        except Exception as e:
            logger.error(f"Error evaluating JavaScript on {response.url}: {e}")
            return

        logger.info(f"Found {len(products_info)} products on {response.url}.")

        for product_json in products_info:
            if not product_json:
                continue

            item = ClothingItem()
            item['name'] = product_json.get('name')
            
            price = product_json.get('price')
            if price:
                # The price is in cents, so we divide by 100
                item['price'] = float(price) / 100
            else:
                item['price'] = None

            product_id = product_json.get('id')
            if product_id:
                # Construct the product link from the product id
                item['product_link'] = f"https://www.pullandbear.com/fr/en/product-p{product_id}.html"
            else:
                item['product_link'] = None

            xmedia = product_json.get('xmedia')
            if xmedia:
                item['image_urls'] = [f"https://static.pullandbear.net/2/photos{i.get('path')}/{i.get('name')}.jpg" for i in xmedia if i.get('path') and i.get('name')]
            else:
                item['image_urls'] = []

            detail = product_json.get('detail', {})
            item['colors'] = [c.get('name') for c in detail.get('colors', [])]
            item['sizes'] = [s.get('name') for s in detail.get('sizes', [])]
            item['description'] = detail.get('longDescription')

            yield item
            logger.info(f"  -> Processed product: {item.get('name', 'N/A')}")
