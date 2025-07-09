import os

import psycopg2


class DatabasePipeline:
    def open_spider(self, spider):
        # TODO add env variables
        db_host = os.environ.get("DB_HOST", "db")
        db_port = os.environ.get("DB_PORT", "5432")
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "my_pass")
        db_name = os.environ.get("DB_NAME", "postgres")

        self.conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname=db_name,
        )
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        try:
            sql = """
                INSERT INTO products (name, description, price, sizes, colors, image_urls, product_link)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_link) DO NOTHING;
            """
            price = item.get("price")

            self.cur.execute(
                sql,
                (
                    item.get("name"),
                    item.get("description"),
                    price,
                    item.get("sizes"),
                    item.get("colors"),
                    item.get("image_urls"),
                    item.get("product_link"),
                ),
            )
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            spider.logger.error(f"Database error: {e}")
            raise
        return item
