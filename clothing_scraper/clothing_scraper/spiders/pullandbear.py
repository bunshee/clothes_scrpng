import scrapy
import logging
import random
import re
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
        # Check if we landed on a blocked page right away
        if response.status == 403 or "Access Denied" in response.text:
            logger.error(f"Access Denied for {response.url}. Aborting this page.")
            return

        # Extract product data
        product_selector = "legacy-product"
        try:
            # Wait for at least one product to be present
            await response.meta['page'].waitForSelector(product_selector, {'timeout': 10000}) # 10 seconds timeout
            logger.info(f"DEBUG: Products found after waiting for selector '{product_selector}'.")
        except Exception as e:
            logger.warning(f"WARNING: No products found after waiting for selector '{product_selector}' on {response.url}: {e}")
            # If no product cards are found, it's possible the page is empty or loaded differently
            # We can still proceed, but product_elements will be empty

        product_elements = response.css(product_selector)
        product_count = len(product_elements)
        logger.info(f"DEBUG: Found {product_count} product elements using selector '{product_selector}' on {response.url}")
        if product_count == 0:
            logger.warning(f"DEBUG: No products found with selector '{product_selector}'. Inspecting response body length: {len(response.body)} bytes.")
            # Save the response body to a file for inspection
            with open(f"debug_pullandbear_{response.url.split('/')[-1]}.html", "wb") as f:
                f.write(response.body)
            logger.info(f"DEBUG: Saved response body to debug_pullandbear_{response.url.split('/')[-1]}.html for inspection.")
        logger.info("Starting to process products...")

        for i, product_element in enumerate(product_elements):
            product_link = product_element.css("a.carousel-item-container::attr(href)").get()
            if product_link:
                if not product_link.startswith("http"):
                    product_link = response.urljoin(product_link)
                yield scrapy.Request(
                    product_link,
                    meta={'pyppeteer': True},
                    callback=self.parse_product_page,
                    dont_filter=True
                )
            else:
                logger.warning(f"No product link found for product card {i + 1} on {response.url}")

    async def parse_product_page(self, response):
        item = ClothingItem()
        item['product_link'] = response.url

        # Extract Name
        name = response.css(".c-product-info--header h1.title::text").get()
        item['name'] = name.strip() if name else None

        # Extract Price
        price_text = None
        # Try to get the sale price first
        price_text = response.css(".sale .number::text").get()
        if not price_text:
            # If no sale price, try the old price
            price_text = response.css(".price-old .number::text").get()

        page = response.meta.get('page')
        if page:
            try:
                await page.waitForSelector('price-element', {'timeout': 5000})
                price_element_handle = await page.querySelector('price-element')
                if price_element_handle:
                    price_text = await page.evaluate('(element) => element.textContent', price_element_handle)
                    logger.info(f"DEBUG: Raw price text from product page (Pyppeteer): {price_text}")
            except Exception as e:
                logger.warning(f"Error evaluating price with Pyppeteer for {response.url}: {e}")
        else:
            logger.warning(f"Pyppeteer page object not available in response.meta for {response.url}. Cannot extract dynamic price.")

        if price_text:
            clean_price = re.sub(r'[^\d,\.]', '', price_text).replace(',', '.')
            try:
                item['price'] = float(clean_price)
            except ValueError:
                item['price'] = None
        else:
            item['price'] = None
        logger.info(f"DEBUG: Final price extracted for {item.get('name', 'N/A')}: {item.get('price', 'None')}")

        # Extract Colors
        colors = response.css(".product-card-color-selector--popup-colors-color-name::text").getall()
        item['colors'] = list(set([c.strip() for c in colors if c.strip()])) if colors else None

        # Extract Sizes
        sizes = response.css("div.c-quick-item--size input.field::attr(title)").getall()
        item['sizes'] = list(set([s.strip() for s in sizes if s.strip()])) if sizes else None

        # Extract Image URLs
        image_urls = response.css("product-image-selector img::attr(src)").getall()
        item['image_urls'] = list(set([response.urljoin(img_url) for img_url in image_urls if img_url])) if image_urls else None

        # Description (assuming it's on the product page)
        # You'll need to provide the selector for the description on the product page
        item['description'] = None # Placeholder

        yield item