import psycopg2
from psycopg2.extras import RealDictCursor
import yaml
import os

# Get the absolute path of the project's root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_connection():
    """Establishes a connection to the PostgreSQL database using credentials from config.yaml."""
    config_path = os.path.join(PROJECT_ROOT, 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    db_config = config['database']
    conn = psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        dbname=db_config['dbname']
    )
    return conn

def create_tables():
    """Creates the database tables based on the schema.sql file."""
    conn = get_db_connection()
    cur = conn.cursor()
    schema_path = os.path.join(PROJECT_ROOT, 'database', 'schema.sql')
    with open(schema_path, 'r') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()

def create_product(product: dict):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        sql = """
            INSERT INTO products (name, description, price, sizes, colors, image_urls, product_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """
        cur.execute(sql, (
            product.get('name'),
            product.get('description'),
            product.get('price'),
            product.get('sizes'),
            product.get('colors'),
            product.get('image_urls'),
            product.get('product_link')
        ))
        product_id = cur.fetchone()[0]
        conn.commit()
        return {**product, "id": product_id}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_product(product_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def get_products(skip: int = 0, limit: int = 100):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM products OFFSET %s LIMIT %s;", (skip, limit,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def update_product(product_id: int, product: dict):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Build SET clause dynamically
        set_clauses = []
        values = []
        for key, value in product.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        if not set_clauses:
            return None # No fields to update

        sql = f"UPDATE products SET {". ".join(set_clauses)} WHERE id = %s RETURNING id;"
        values.append(product_id)
        
        cur.execute(sql, tuple(values))
        updated_id = cur.fetchone()
        conn.commit()
        return updated_id[0] if updated_id else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def delete_product(product_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE id = %s RETURNING id;", (product_id,))
        deleted_id = cur.fetchone()
        conn.commit()
        return deleted_id[0] if deleted_id else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("Creating database tables...")
    create_tables()
    print("Tables created successfully.")
