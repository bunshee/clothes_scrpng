from fastapi import FastAPI, HTTPException
import sys
import os
from typing import List
from concurrent.futures import ThreadPoolExecutor
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from api.models import ProductCreate, ProductResponse, ProductUpdate, DeleteProductResponse
from api.spiders import SpiderName
from clothing_scraper.spiders.pullandbear import PullandbearSpider
from clothing_scraper.spiders.hm import HmSpider
from clothing_scraper.spiders.jules import JulesSpider
from clothing_scraper.spiders.primark import PrimarkSpider
from clothing_scraper.spiders.canda import CandaSpider

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=2) # Adjust max_workers as needed

def run_spider_in_thread(spider_name: SpiderName):
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    spider_map = {
        SpiderName.PULLANDBEAR: PullandbearSpider,
        SpiderName.HM: HmSpider,
        SpiderName.JULES: JulesSpider,
        SpiderName.PRIMARK: PrimarkSpider,
        SpiderName.CANDA: CandaSpider,
    }

    spider_cls = spider_map.get(spider_name)
    if not spider_cls:
        raise ValueError(f"Spider '{spider_name}' not found.")

    process.crawl(spider_cls)
    process.start(stop_after_crawl=True) # Blocks until crawl finishes

@app.post("/scrape/{spider_name}")
async def scrape_products(spider_name: SpiderName):
    # Submit the blocking spider run to the thread pool
    executor.submit(run_spider_in_thread, spider_name)
    
    return {"message": f"Scraping for {spider_name} started in background."}

@app.post("/products/", response_model=ProductResponse)
def create_product(product: ProductCreate):
    db_product = db.create_product(product.model_dump())
    return db_product

@app.get("/products/", response_model=List[ProductResponse])
def read_products(skip: int = 0, limit: int = 100):
    products = db.get_products(skip=skip, limit=limit)
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
def read_product(product_id: int):
    product = db.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate):
    updated_id = db.update_product(product_id, product.model_dump(exclude_unset=True))
    if updated_id is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db.get_product(updated_id)

@app.delete("/products/{product_id}", response_model=DeleteProductResponse)
def delete_product(product_id: int):
    deleted_id = db.delete_product(product_id)
    if deleted_id is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": deleted_id, "message": "Product deleted successfully"}

@app.delete("/products/")
def delete_all_products():
    db.delete_all_products()
    return {"message": "All products deleted successfully"}
