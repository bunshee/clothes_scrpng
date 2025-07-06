from typing import List, Optional
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    product_link: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    scraped_at: str # Will be datetime object from DB, but represented as string for API

    class Config:
        from_attributes = True # Allow ORM mode