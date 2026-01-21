"""
Flask API Server for Invoice Upload and OCR Processing
Provides REST API endpoints for uploading invoices and processing them with OCR
"""

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging
from odoo_client import OdooClient
from ocr_processor import OCRProcessor
from ai_guardrails import AIGuardrails

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff', 'bmp'}

# Initialize components
try:
    odoo_client = OdooClient()
    ocr_processor = OCRProcessor()
    ai_guardrails = AIGuardrails(odoo_client)
    logger.info("API server components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    odoo_client = None
    ocr_processor = None
    ai_guardrails = None


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    status = {
        'status': 'healthy',
        'odoo_connected': odoo_client is not None,
        'ocr_ready': ocr_processor is not None
    }
    return jsonify(status), 200


@app.route('/upload_invoice', methods=['POST'])
def upload_invoice():
    """
    Upload and process invoice image.
    
    Expects:
        - 'file': Invoice image file (PNG, JPG, JPEG, PDF, TIFF, BMP)
        - 'partner_id' (optional): Odoo partner ID for the vendor
        - 'auto_create' (optional): Whether to auto-create invoice in Odoo (default: true)
    
    Returns:
        JSON with extracted invoice data and creation status
    """
    try:
        # Check if components are initialized
        if not odoo_client or not ocr_processor:
            return jsonify({
                'error': 'Server components not initialized. Check configuration.'
            }), 503
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Read file bytes
        image_bytes = file.read()
        logger.info(f"Processing uploaded file: {file.filename} ({len(image_bytes)} bytes)")
        
        # Extract text using OCR
        text = ocr_processor.extract_text(image_bytes)
        logger.info(f"OCR text extracted: {len(text)} characters")
        
        # Extract invoice data
        invoice_data = ocr_processor.extract_invoice_data(text)
        logger.info(f"Extracted invoice data: {invoice_data}")
        
        # Get optional parameters
        partner_id = request.form.get('partner_id')
        auto_create = request.form.get('auto_create', 'true').lower() == 'true'
        
        result = {
            'success': True,
            'filename': secure_filename(file.filename),
            'extracted_data': invoice_data,
            'raw_text': text[:500] if len(text) > 500 else text  # First 500 chars
        }
        
        # Auto-create invoice in Odoo if requested
        if auto_create:
            try:
                # Prepare invoice data for Odoo
                odoo_invoice_data = {
                    'move_type': 'in_invoice',  # Vendor bill
                    'ref': invoice_data.get('invoice_number'),
                    'invoice_date': invoice_data.get('date'),
                }
                
                # Add partner if provided
                if partner_id:
                    odoo_invoice_data['partner_id'] = int(partner_id)
                
                # Add amount if available
                if invoice_data.get('total'):
                    # Note: In real implementation, you'd need to add invoice lines
                    # This is simplified for demonstration
                    odoo_invoice_data['invoice_line_ids'] = [
                        (0, 0, {
                            'name': f"Invoice {invoice_data.get('invoice_number', 'N/A')}",
                            'quantity': 1,
                            'price_unit': invoice_data.get('total', 0)
                        })
                    ]
                
                # Create invoice in Odoo
                invoice_id = odoo_client.create('account.move', [odoo_invoice_data])
                logger.info(f"Created invoice in Odoo with ID: {invoice_id}")
                
                # Use AI guardrails to check confidence
                if ai_guardrails:
                    category = ai_guardrails.check_and_set(
                        'account.move',
                        invoice_id,
                        invoice_data
                    )
                    result['ai_category'] = category
                
                result['odoo_invoice_id'] = invoice_id
                result['odoo_created'] = True
                
            except Exception as e:
                logger.error(f"Error creating invoice in Odoo: {e}")
                result['odoo_created'] = False
                result['odoo_error'] = str(e)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing invoice upload: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/extract_text', methods=['POST'])
def extract_text_only():
    """
    Extract text from image without creating invoice.
    
    Expects:
        - 'file': Invoice image file
    
    Returns:
        JSON with extracted text and invoice data
    """
    try:
        if not ocr_processor:
            return jsonify({
                'error': 'OCR processor not initialized'
            }), 503
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Read and process file
        image_bytes = file.read()
        text = ocr_processor.extract_text(image_bytes)
        invoice_data = ocr_processor.extract_invoice_data(text)
        
        return jsonify({
            'success': True,
            'filename': secure_filename(file.filename),
            'text': text,
            'extracted_data': invoice_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error extracting text: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/partners', methods=['GET'])
def list_partners():
    """
    List available partners (vendors) from Odoo.
    
    Query params:
        - limit (optional): Number of records to return (default: 50)
        - search (optional): Search term for partner name
    
    Returns:
        JSON with list of partners
    """
    try:
        if not odoo_client:
            return jsonify({'error': 'Odoo client not initialized'}), 503
        
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '')
        
        domain = [('supplier_rank', '>', 0)]  # Only vendors
        if search:
            domain.append(('name', 'ilike', search))
        
        partners = odoo_client.search_read(
            'res.partner',
            domain,
            ['id', 'name', 'email', 'phone']
        )
        
        return jsonify({
            'success': True,
            'count': len(partners),
            'partners': partners[:limit]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching partners: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'error': 'File too large. Maximum size is 16MB.'
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error. Check logs for details.'
    }), 500


if __name__ == '__main__':
    # Development server
    # For production, use gunicorn or uwsgi
    logger.info("Starting Flask API server...")
    logger.info("Available endpoints:")
    logger.info("  GET  /health - Health check")
    logger.info("  POST /upload_invoice - Upload and process invoice")
    logger.info("  POST /extract_text - Extract text only (no Odoo creation)")
    logger.info("  GET  /partners - List available vendors")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False  # Set to False in production
    )
