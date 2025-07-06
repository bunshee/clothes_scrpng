import scrapy
from scrapy_playwright.page import PageMethod
from clothing_scraper.items import ClothingItem
import random
import re # Added for price cleaning

class PullandbearSpider(scrapy.Spider):
    name = "pullandbear"
    allowed_domains = ["pullandbear.com"]

    # This is a good way to load settings.
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PullandbearSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.proxy_user = crawler.settings.get('PROXY_USER')
        spider.proxy_pass = crawler.settings.get('PROXY_PASS')
        spider.proxy_host = crawler.settings.get('PROXY_HOST')
        spider.proxy_port = crawler.settings.get('PROXY_PORT')
        return spider

    # Changed from start_requests to start for async compatibility
    async def start(self):
        # Construct the proxy URL once
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}" if self.proxy_host else None

        start_urls = [
            "https://www.pullandbear.com/fr/femme-n6221",
            "https://www.pullandbear.com/fr/homme-n6228",
            "https://www.pullandbear.com/fr/femme-n6417",
        ]

        for url in start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    # Launch options to add proxy and stealth arguments
                    "playwright_launch_options": {
                        "proxy": {
                            "server": proxy_url
                        } if proxy_url else None,
                        "args": [
                            '--disable-blink-features=AutomationControlled',
                            '--no-sandbox',
                            '--disable-infobars',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--window-size=1920,1080',
                        ],
                    },
                    # Context arguments to rotate user agents
                    "playwright_context_kwargs": {
                        "user_agent": random.choice([
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0',
                            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
                        ]),
                    }
                },
                callback=self.parse,
                dont_filter=True  # Usually needed when re-scraping or debugging
            )

    async def parse(self, response):
        page = response.playwright_page

        # Check if we landed on a blocked page right away
        if response.status == 403 or "Access Denied" in await page.content():
            self.logger.error(f"Access Denied for {page.url}. Check proxy and browser fingerprint. Aborting this page.")
            await page.close()
            return

        await page.wait_for_load_state('domcontentloaded')

        # Your excellent debugging logic
        await page.screenshot(path='pullandbear_debug_screenshot.png', full_page=True)
        with open("pullandbear_debug_page.html", "w", encoding="utf-8") as f:
            f.write(await page.content())

        await self._handle_popups_aggressively(page)

        product_grid_selector = "#ProductsByCategory"
        try:
            await page.wait_for_selector(product_grid_selector, state="visible", timeout=15000)
            self.logger.info("Product grid is visible.")
        except Exception as e:
            self.logger.error(f"Product grid not visible after 15 seconds: {e}")
            await page.screenshot(path="pullandbear_debug_screenshot.png")
            await page.close()
            return

        self.logger.info("Attempting to load all products...")
        load_more_button_selector = "button:has-text('Voir plus')"
        while await page.locator(load_more_button_selector).is_visible():
            try:
                await page.locator(load_more_button_selector).click(timeout=5000)
                self.logger.info("Clicked 'load more' button.")
                await page.wait_for_load_state("networkidle", timeout=10000)
                await self._handle_popups_aggressively(page)
            except Exception as e:
                self.logger.info(f"'Load more' button no longer visible or clickable: {e}")
                break

        product_card_selector = "div.c-tile--product"
        product_elements = await page.locator(product_card_selector).all()
        product_count = len(product_elements)
        self.logger.info(f"Found {product_count} products on the category page.")
        self.logger.info("Starting to process products...")

        for i, product_element in enumerate(product_elements):
            item = ClothingItem()
            try:
                # Wait for the name to be visible before extracting data
                name_selector = ".product-name"
                await product_element.locator(name_selector).wait_for(state="visible", timeout=5000)

                link_element = product_element.locator("a.carousel-item-container")
                product_link = await link_element.get_attribute("href") if await link_element.count() > 0 else None
                if product_link and not product_link.startswith("http"):
                    item['product_link'] = response.urljoin(product_link)
                else:
                    item['product_link'] = product_link

                name_element = product_element.locator(name_selector)
                item['name'] = await name_element.text_content() if await name_element.count() > 0 else None

                price_element = product_element.locator("price-element")
                price_text = await price_element.text_content() if await price_element.count() > 0 else None
                if price_text:
                    clean_price = re.sub(r'[^\d,\.]', '', price_text).replace(',', '.')
                    try:
                        item['price'] = float(clean_price)
                    except ValueError:
                        self.logger.warning(f"Could not convert price to float: {price_text}")
                        item['price'] = None
                else:
                    item['price'] = None

                colors = []
                color_title_elements = product_element.locator("div.color-container div.title-color")
                if await color_title_elements.count() == 0:
                    color_image_elements = product_element.locator("ul.product-card-colors__list li img")
                    for j in range(await color_image_elements.count()):
                        c_el = color_image_elements.nth(j)
                        alt_text = await c_el.get_attribute("alt")
                        if alt_text and alt_text.strip():
                            colors.append(alt_text.strip())
                else:
                    for j in range(await color_title_elements.count()):
                        c_el = color_title_elements.nth(j)
                        color_name = await c_el.text_content()
                        if color_name:
                            colors.append(color_name.strip())
                item['colors'] = [c for c in list(set(colors)) if c] if colors else None

                item['sizes'] = None # Temporarily disabled

                image_element = product_element.locator("figure.figure img.image-responsive")
                if await image_element.count() == 0:
                    image_element = product_element.locator("picture.product-card__image-container img")
                
                image_src = await image_element.get_attribute("src")
                item['image_urls'] = [image_src] if image_src else None
                
                item['description'] = None # Not available on this page

                yield item
                self.logger.info(f"  -> Processed product {i + 1}/{product_count}: {item.get('name', 'N/A')}")

            except Exception as e:
                self.logger.error(f"  Error processing product card {i + 1}: {e}")
                try:
                    self.logger.error(f"  Problematic element HTML: {await product_element.inner_html()}")
                except Exception as html_e:
                    self.logger.error(f"Could not get inner HTML of problematic element: {html_e}")

        await page.close()

    async def _handle_popups_aggressively(self, page):
        popups = {
            "cookie_consent": 'button:has-text("Accepter tout"), #onetrust-accept-btn-handler',
            "newsletter_popup": 'button[aria-label="Fermer"]',
            "localization_popup": 'button:has-text("Non")'
        }
        
        for _ in range(3):
            for popup_name, selector in popups.items():
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=500):
                        self.logger.info(f"  Closing {popup_name}...")
                        try:
                            await button.click(timeout=500)
                            await page.wait_for_load_state("networkidle", timeout=2000)
                            self.logger.info(f"  {popup_name} closed.")
                        except Exception as e:
                            self.logger.warning(f"  Could not click {popup_name} button: {e}")
                except Exception:
                    pass # Popup not found, continue
            await page.wait_for_timeout(500) # Use wait_for_timeout for async sleep