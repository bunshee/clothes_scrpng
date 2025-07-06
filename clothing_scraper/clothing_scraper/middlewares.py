import logging
from scrapy import signals
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)

class CaptchaMiddleware:
    def __init__(self, captcha_api_key=None):
        self.captcha_api_key = captcha_api_key

    @classmethod
    def from_crawler(cls, crawler):
        s = cls(crawler.settings.get('CAPTCHA_API_KEY'))
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_response(self, request, response, spider):
        # Check for common CAPTCHA indicators in the response body
        captcha_indicators = [
            "I am not a robot",
            "reCAPTCHA",
            "h-captcha",
            "captcha-challenge",
            "prove you are human"
        ]

        for indicator in captcha_indicators:
            if indicator.lower() in response.text.lower():
                logger.warning(f"CAPTCHA detected on {response.url}. A CAPTCHA solving service would be needed here.")
                # In a real scenario, you would send the CAPTCHA to a solving service
                # and then retry the request with the solved CAPTCHA token.
                # For now, we'll just return the response as is, but it will likely fail.
                return response
        return response

    def spider_opened(self, spider):
        logger.info(f"CaptchaMiddleware enabled for spider {spider.name}")