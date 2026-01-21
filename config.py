import os
from dotenv import load_dotenv

load_dotenv()

# Odoo Configuration - MUST be provided via environment variables
ODOO_URL = os.getenv('ODOO_URL', 'https://your-odoo-instance.odoo.com')
ODOO_DB = os.getenv('ODOO_DB', 'your_database')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'your_username@example.com')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'your_password')

# AI settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.9'))

# OCR settings
OCR_ENGINE = os.getenv('OCR_ENGINE', 'easyocr')  # or 'tesseract'

# Validate required configuration
if ODOO_URL.startswith('https://your-odoo') or ODOO_DB == 'your_database':
    import logging
    logging.warning(
        "WARNING: Using default placeholder values for Odoo configuration. "
        "Please set ODOO_URL, ODOO_DB, ODOO_USERNAME, and ODOO_PASSWORD environment variables."
    )