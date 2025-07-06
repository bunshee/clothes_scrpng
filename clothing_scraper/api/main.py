from fastapi import FastAPI, HTTPException
import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from api.models import ProductCreate, ProductResponse, ProductUpdate

app = FastAPI()

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

@app.delete("/products/{product_id}", response_model=ProductResponse)
def delete_product(product_id: int):
    deleted_id = db.delete_product(product_id)
    if deleted_id is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": deleted_id, "message": "Product deleted successfully"}
