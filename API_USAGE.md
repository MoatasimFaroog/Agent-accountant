# Flask API Server - Invoice Upload & OCR Processing

This API server provides REST endpoints for uploading invoice images, performing OCR extraction, and automatically creating invoices in Odoo.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your Odoo credentials:

```env
ODOO_URL=https://your-odoo.com
ODOO_DB=your_database
ODOO_USERNAME=your_email
ODOO_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key  # Optional for AI features
```

### 3. Start the Server

```bash
python api_server.py
```

The server will start on `http://localhost:5000`

### 4. Access the Web Interface

Open your browser and navigate to:
```
http://localhost:5000/static/upload.html
```

Or use the API directly with any HTTP client.

## API Endpoints

### 1. Health Check
**GET** `/health`

Check if the API server is running and components are initialized.

**Response:**
```json
{
  "status": "healthy",
  "odoo_connected": true,
  "ocr_ready": true
}
```

### 2. Upload Invoice
**POST** `/upload_invoice`

Upload an invoice image for OCR processing and optional Odoo creation.

**Parameters:**
- `file` (required): Invoice image file (PNG, JPG, JPEG, PDF, TIFF, BMP)
- `partner_id` (optional): Odoo partner/vendor ID
- `auto_create` (optional): `true` or `false` - Whether to create invoice in Odoo (default: true)

**Example using cURL:**
```bash
curl -X POST http://localhost:5000/upload_invoice \
  -F "file=@invoice.jpg" \
  -F "partner_id=123" \
  -F "auto_create=true"
```

**Example using Python:**
```python
import requests

with open('invoice.jpg', 'rb') as f:
    files = {'file': f}
    data = {
        'partner_id': '123',
        'auto_create': 'true'
    }
    response = requests.post('http://localhost:5000/upload_invoice', files=files, data=data)
    print(response.json())
```

**Success Response:**
```json
{
  "success": true,
  "filename": "invoice.jpg",
  "extracted_data": {
    "invoice_number": "INV-2024-001",
    "date": "01/15/2024",
    "total": 1250.00
  },
  "raw_text": "INVOICE #INV-2024-001...",
  "odoo_invoice_id": 12345,
  "odoo_created": true,
  "ai_category": "Expense"
}
```

### 3. Extract Text Only
**POST** `/extract_text`

Extract text from invoice image without creating invoice in Odoo.

**Parameters:**
- `file` (required): Invoice image file

**Example:**
```bash
curl -X POST http://localhost:5000/extract_text \
  -F "file=@invoice.jpg"
```

**Response:**
```json
{
  "success": true,
  "filename": "invoice.jpg",
  "text": "Full extracted text...",
  "extracted_data": {
    "invoice_number": "INV-2024-001",
    "date": "01/15/2024",
    "total": 1250.00
  }
}
```

### 4. List Partners
**GET** `/partners`

Get list of vendors/partners from Odoo.

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 50)
- `search` (optional): Search term for partner name

**Example:**
```bash
curl "http://localhost:5000/partners?limit=10&search=ABC"
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "partners": [
    {
      "id": 123,
      "name": "ABC Company",
      "email": "contact@abc.com",
      "phone": "+1234567890"
    }
  ]
}
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Error description"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (missing file, invalid parameters)
- `413` - File too large (max 16MB)
- `500` - Internal server error
- `503` - Service unavailable (Odoo/OCR not initialized)

## Production Deployment

For production use, deploy with a WSGI server like Gunicorn:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

Or use Docker:

```bash
# Build image
docker build -t ai-bookkeeper-api .

# Run container
docker run -p 5000:5000 --env-file .env ai-bookkeeper-api
```

## Security Notes

1. **Never expose this API directly to the internet without authentication**
2. Use HTTPS in production (nginx/Apache reverse proxy)
3. Implement API key authentication
4. Set up rate limiting
5. Use environment variables for all sensitive data

## Troubleshooting

### Server won't start
- Check if port 5000 is available
- Verify `.env` file exists with correct credentials
- Check logs for specific error messages

### OCR not working
- Ensure EasyOCR dependencies are installed
- Check if image file is valid and not corrupted
- Verify image format is supported

### Odoo connection failed
- Verify Odoo credentials in `.env`
- Check if Odoo server is accessible
- Ensure XML-RPC is enabled on Odoo instance

## Support

For issues or questions, check the main README.md or open an issue on the repository.
