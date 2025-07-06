import psycopg2
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

if __name__ == '__main__':
    print("Creating database tables...")
    create_tables()
    print("Tables created successfully.")
