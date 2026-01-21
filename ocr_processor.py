import easyocr
from PIL import Image
import io
import re
import logging
from config import OCR_ENGINE

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        """Initialize OCR processor with configured engine."""
        try:
            if OCR_ENGINE == 'easyocr':
                logger.info("Initializing EasyOCR reader...")
                self.reader = easyocr.Reader(['en'])  # Add languages as needed
                logger.info("EasyOCR reader initialized successfully")
            else:
                raise ValueError(f"Unsupported OCR engine: {OCR_ENGINE}. Only 'easyocr' is supported.")
        except Exception as e:
            logger.error(f"Error initializing OCR processor: {e}")
            raise

    def extract_text(self, image_bytes):
        """Extract text from image bytes using OCR.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If image data is invalid or OCR engine unsupported
        """
        try:
            if not image_bytes:
                raise ValueError("Image bytes are empty or None")
            
            if OCR_ENGINE == 'easyocr':
                # Open image from bytes
                image = Image.open(io.BytesIO(image_bytes))
                logger.info(f"Processing image: size={image.size}, mode={image.mode}")
                
                # Perform OCR
                results = self.reader.readtext(image)
                logger.info(f"OCR extracted {len(results)} text regions")
                
                # Join all text
                text = ' '.join([res[1] for res in results])
                return text
            else:
                raise ValueError(f"Unsupported OCR engine: {OCR_ENGINE}")
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise ValueError(f"Failed to extract text from image: {e}")

    def extract_invoice_data(self, text):
        """Extract structured invoice data from text using regex.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with invoice_number, date, and total
        """
        if not text:
            logger.warning("No text provided for invoice data extraction")
            return {'invoice_number': None, 'date': None, 'total': None}
        
        # Simple regex-based extraction; enhance with AI for better accuracy
        data = {}
        
        # Extract invoice number
        match = re.search(r'Invoice\s*#?\s*:?\s*([A-Z0-9-]+)', text, re.I)
        data['invoice_number'] = match.group(1) if match else None
        if match:
            logger.info(f"Found invoice number: {data['invoice_number']}")
        
        # Extract date (various formats)
        match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
        data['date'] = match.group(1) if match else None
        if match:
            logger.info(f"Found date: {data['date']}")
        
        # Extract total amount
        match = re.search(r'Total\s*[:$]*\s*(\d+[.,]\d{2})', text, re.I)
        if match:
            total_str = match.group(1).replace(',', '.')
            try:
                data['total'] = float(total_str)
                logger.info(f"Found total: ${data['total']:.2f}")
            except ValueError:
                logger.warning(f"Could not parse total amount: {total_str}")
                data['total'] = None
        else:
            data['total'] = None
        
        # Log if any field is missing
        missing_fields = [k for k, v in data.items() if v is None]
        if missing_fields:
            logger.warning(f"Could not extract fields: {', '.join(missing_fields)}")
        
        return data