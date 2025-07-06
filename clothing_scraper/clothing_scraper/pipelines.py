import psycopg2

class DatabasePipeline:
    def open_spider(self, spider):
        db_settings = spider.settings.getdict('DATABASE')
        self.conn = psycopg2.connect(
            host=db_settings['host'],
            port=db_settings['port'],
            user=db_settings['user'],
            password=db_settings['password'],
            dbname=db_settings['dbname']
        )
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        sql = """
            INSERT INTO products (name, description, price, sizes, colors, image_urls, product_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_link) DO NOTHING;
        """
        price_str = item.get('price')
        price = None
        if price_str:
            price_str = price_str.replace('€', '').replace(',', '.').strip()
            if price_str:
                try:
                    price = float(price_str)
                except ValueError:
                    price = None

        self.cur.execute(sql, (
            item.get('name'),
            item.get('description'),
            price,
            item.get('sizes'),
            item.get('colors'),
            item.get('image_urls'),
            item.get('product_link')
        ))
        self.conn.commit()
        return item