import scrapy

class ClothingItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    sizes = scrapy.Field()
    colors = scrapy.Field()
    image_urls = scrapy.Field()
    product_link = scrapy.Field()
    description = scrapy.Field()