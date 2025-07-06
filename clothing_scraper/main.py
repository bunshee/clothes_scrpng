import argparse
import uvicorn
import os
import sys
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the project root to the Python path to allow for absolute imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from database.db import create_tables
from api.spiders import SpiderName
from clothing_scraper.spiders.pullandbear import PullandbearSpider
from clothing_scraper.spiders.hm import HmSpider
from clothing_scraper.spiders.jules import JulesSpider
from clothing_scraper.spiders.primark import PrimarkSpider
from clothing_scraper.spiders.canda import CandaSpider

def main():
    parser = argparse.ArgumentParser(description="Clothing Scraper and API")
    parser.add_argument("action", choices=["scrape", "api", "setup"], help="Action to perform")
    parser.add_argument("--spider", type=SpiderName, choices=list(SpiderName), help="Specify which spider to run (e.g., pullandbear, hm)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        logging.getLogger('pyppeteer').setLevel(logging.WARNING)
        logging.getLogger('websockets').setLevel(logging.WARNING)

    if args.action == "setup":
        print("Setting up the database...")
        create_tables()
        print("Database setup complete.")
    elif args.action == "scrape":
        print("Starting the scraper...")
        process = CrawlerProcess(get_project_settings())
        if args.spider == SpiderName.PULLANDBEAR:
            process.crawl(PullandbearSpider)
        elif args.spider == SpiderName.HM:
            process.crawl(HmSpider)
        elif args.spider == SpiderName.JULES:
            process.crawl(JulesSpider)
        elif args.spider == SpiderName.PRIMARK:
            process.crawl(PrimarkSpider)
        elif args.spider == SpiderName.CANDA:
            process.crawl(CandaSpider)
        else:
            print("Please specify a spider to run using --spider (e.g., --spider pullandbear or --spider hm)")
            return
        process.start()
        print("Scraping complete.")
    elif args.action == "api":
        print("Starting the API...")
        uvicorn.run("api.main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()