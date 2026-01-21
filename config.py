import os
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv('ODOO_URL', 'https://gtcintl2.odoo.com')
ODOO_DB = os.getenv('ODOO_DB', 'gtcintl2')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'motasim.noor@gtc-intl.com')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'njfdsvnh654768357')

# AI settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.9'))

# OCR settings
OCR_ENGINE = os.getenv('OCR_ENGINE', 'easyocr')  # or 'tesseract'