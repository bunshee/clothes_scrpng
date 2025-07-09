import asyncio
import random
import logging
from scrapy.http import HtmlResponse
from scrapy.utils.defer import deferred_from_coro
from scrapy.utils.reactor import verify_installed_reactor
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from twocaptcha import TwoCaptcha
import re

logger = logging.getLogger(__name__)

class UndetectedChromeDriverDownloadHandler:
    def __init__(self, settings):
        verify_installed_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
        self.driver = None
        self.headless = settings.getbool('PYPPETEER_HEADLESS', True)
        self.launch_args = settings.getlist('PYPPETEER_LAUNCH_ARGS', [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
        ])
        self.user_agent = settings.get('USER_AGENT') # Get the user agent from settings
        # You need to provide your 2Captcha API key here
        self.solver = TwoCaptcha('YOUR_2CAPTCHA_API_KEY') 

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    async def _launch_browser(self):
        if not self.driver:
            logger.info("Launching undetected_chromedriver browser...")
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            for arg in self.launch_args:
                options.add_argument(arg)
            
            self.driver = uc.Chrome(options=options)
            logger.info("undetected_chromedriver browser launched.")

    async def _handle_datadome_captcha(self, url):
        logger.info(f"DataDome CAPTCHA detected on {url}. Attempting to solve...")
        try:
            # Use the datadome method from 2Captcha
            result = self.solver.datadome(url=url, user_agent=self.user_agent)
            
            if result and result['cookie']:
                logger.info("CAPTCHA solved successfully. Injecting cookie...")
                # The result['cookie'] is a string like 'datadome=...' or '__ddg1_=...' etc.
                # We need to parse it and add each cookie individually
                cookies_str = result['cookie']
                for cookie_part in cookies_str.split(';'):
                    if '=' in cookie_part:
                        name, value = cookie_part.split('=', 1)
                        self.driver.add_cookie({'name': name.strip(), 'value': value.strip(), 'domain': '.celio.com'})
                
                logger.info("Cookies injected. Reloading page...")
                self.driver.get(url) # Reload the page with the new cookies
                await asyncio.sleep(5) # Give some time for the page to load
                return True
            else:
                logger.error(f"Failed to solve CAPTCHA: {result}")
                return False
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            return False

    def download_request(self, request, spider):
        return deferred_from_coro(self._download_request_async(request, spider))

    async def _download_request_async(self, request, spider):
        await self._launch_browser()

        try:
            logger.info(f"Navigating to {request.url} using undetected_chromedriver...")
            self.driver.get(request.url)
            await asyncio.sleep(10) # Add a 10-second delay for dynamic content to load

            # Check for DataDome CAPTCHA
            if "geo.captcha-delivery.com" in self.driver.current_url or "DataDome CAPTCHA" in self.driver.page_source:
                if not await self._handle_datadome_captcha(request.url):
                    raise Exception("CAPTCHA bypass failed")

            content = self.driver.page_source
            status = 200 # undetected_chromedriver doesn't directly expose status code, assume 200 if no error
            url = self.driver.current_url

            response_obj = HtmlResponse(
                url=url,
                status=status,
                body=content.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            return response_obj
        except Exception as e:
            logger.error(f"Error downloading {request.url} with undetected_chromedriver: {e}")
            raise

    async def close_browser(self):
        if self.driver:
            logger.info("Closing undetected_chromedriver browser...")
            self.driver.quit()
            self.driver = None
            logger.info("undetected_chromedriver browser closed.")

    def spider_closed(self):
        return deferred_from_coro(self.close_browser())
