from fastapi import FastAPI
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db_connection

app = FastAPI()

@app.get("/products")
def get_products():
    """Fetches all products from the database and returns them as a list of dictionaries."""
    conn = get_db_connection()
    # Use RealDictCursor to get results as dictionaries
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return products
