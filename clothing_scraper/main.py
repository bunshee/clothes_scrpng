import argparse
import uvicorn
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from clothing_scraper.spiders.pullandbear import PullandbearSpider
from clothing_scraper.spiders.hm import HmSpider
from clothing_scraper.spiders.jules import JulesSpider
from clothing_scraper.spiders.primark import PrimarkSpider
from clothing_scraper.spiders.canda import CandaSpider

# Add the project root to the Python path to allow for absolute imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from database.db import create_tables

def main():
    parser = argparse.ArgumentParser(description="Clothing Scraper and API")
    parser.add_argument("action", choices=["scrape", "api", "setup"], help="Action to perform")
    parser.add_argument("--spider", help="Specify which spider to run (e.g., pullandbear, hm)")
    args = parser.parse_args()

    if args.action == "setup":
        print("Setting up the database...")
        create_tables()
        print("Database setup complete.")
    elif args.action == "scrape":
        print("Starting the scraper...")
        process = CrawlerProcess(get_project_settings())
        if args.spider == "pullandbear":
            process.crawl(PullandbearSpider)
        elif args.spider == "hm":
            process.crawl(HmSpider)
        elif args.spider == "jules":
            process.crawl(JulesSpider)
        elif args.spider == "primark":
            process.crawl(PrimarkSpider)
        elif args.spider == "canda":
            process.crawl(CandaSpider)
        else:
            print("Please specify a spider to run using --spider (e.g., --spider pullandbear or --spider hm)")
            return
        process.start()
        print("Scraping complete.")
    elif args.action == "api":
        print("Starting the API...")
        uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()