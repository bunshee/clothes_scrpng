import asyncio
import random
import logging
from pyppeteer import launch
from scrapy.http import HtmlResponse
from scrapy.utils.defer import deferred_from_coro
from scrapy.utils.reactor import verify_installed_reactor

logger = logging.getLogger(__name__)

class PyppeteerDownloadHandler:
    def __init__(self, settings):
        verify_installed_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
        self.browser = None
        self.launch_options = {
            'headless': settings.getbool('PYPPETEER_HEADLESS', True),
            'args': settings.getlist('PYPPETEER_LAUNCH_ARGS', ['--no-sandbox', '--disable-setuid-sandbox']),
            'autoClose': False, # Keep browser open for multiple requests
        }
        self.user_agents = settings.getlist('USER_AGENTS', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
        ])

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    async def _launch_browser(self):
        if not self.browser:
            logger.info("Launching Pyppeteer browser...")
            self.browser = await launch(handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False, **self.launch_options)
            logger.info("Pyppeteer browser launched.")

    def download_request(self, request, spider):
        return deferred_from_coro(self._download_request_async(request, spider))

    async def _download_request_async(self, request, spider):
        await self._launch_browser()

        page = await self.browser.newPage()
        logger.debug(f"DEBUG: Pyppeteer page created for {request.url}: {page}")
        await page.setViewport({'width': 1920, 'height': 1080})
        await page.setUserAgent(random.choice(self.user_agents))

        try:
            logger.info(f"Navigating to {request.url} using Pyppeteer...")
            response = await page.goto(request.url, {'waitUntil': 'domcontentloaded', 'timeout': 120000})
            await asyncio.sleep(10) # Add a 10-second delay for dynamic content to load
            # await self._handle_popups_aggressively(page) # Temporarily commented out for debugging

            content = await page.content()
            status = response.status
            url = page.url

            response_obj = HtmlResponse(
                url=url,
                status=status,
                body=content.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            response_obj.meta['page'] = page # Attach the page object to meta
            return response_obj
        except Exception as e:
            logger.error(f"Error downloading {request.url} with Pyppeteer: {e}")
            raise

    async def _handle_popups_aggressively(self, page):
        # Simplified popup handling: just try to click the main accept button if it exists
        selector = 'button#onetrust-accept-btn-handler, button:has-text("Accepter les cookies"), button:has-text("Accepter tout")'
        try:
            button = await page.querySelector(selector)
            if button and await button.isVisible():
                logger.info(f"  Closing cookie consent popup...")
                await button.click()
                await asyncio.sleep(0.5) # Small delay after click
                logger.info(f"  Cookie consent popup closed.")
        except Exception:
            pass # Popup not found or clickable, continue

    async def close_browser(self):
        if self.browser:
            logger.info("Closing Pyppeteer browser...")
            await self.browser.close()
            self.browser = None
            logger.info("Pyppeteer browser closed.")

    def spider_closed(self):
        return deferred_from_coro(self.close_browser())