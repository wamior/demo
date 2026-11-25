from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR/'assets'
PRODUCT_IMAGES_DIR = ASSETS_DIR/'products'

DB_SETTINGS = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'shoe_store2',
    'user': 'postgres',
    'password': '',
    'connect_timeout': 5,
}











