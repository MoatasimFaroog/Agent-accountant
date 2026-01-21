# AI Bookkeeper Agent for Odoo Integration

This project implements an AI-powered agent to automate bookkeeping tasks in Odoo, focusing on Accounting and Invoicing modules. The agent uses Odoo Web Services (XML-RPC) for integration, EasyOCR for invoice processing, and OpenAI for AI-powered categorization.

## Features

1. **Data Ingestion & OCR**: Extracts data from invoice attachments using OCR and auto-fills Vendor Bills in Odoo.

2. **Automated Reconciliation**: Fetches bank statements and matches them with journal entries, populating the reconciliation widget and flagging discrepancies.

3. **AR/AP Automation**: 
   - Monitors invoice statuses
   - Sends follow-up emails for overdue AR (with validation for partner emails)
   - Schedules AP payments for upcoming due dates

4. **Payroll & Reporting**: Syncs with payroll for journal entries and generates real-time P&L and Balance Sheet reports.

5. **System Guardrails**: 
   - Implements confidence scoring using AI
   - If AI confidence < 90%, sets records to Draft for human review
   - Prevents automated edits to posted entries without audit logs

## Technical Stack

- **Python**: 3.9+
- **Odoo API**: XML-RPC for remote procedure calls
- **OCR**: EasyOCR for text extraction from invoices
- **AI**: OpenAI GPT-3.5/4 for transaction categorization
- **Libraries**: xmlrpc.client, easyocr, pandas, Pillow, python-dotenv

## Prerequisites

- Python 3.9 or higher
- Access to an Odoo instance (URL, database name, username, password)
- OpenAI API key (optional, for AI categorization features)
- Docker (optional, for containerized deployment)

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Agent-accountant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Odoo Configuration
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password

# AI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key
CONFIDENCE_THRESHOLD=0.9

# OCR Configuration
OCR_ENGINE=easyocr
```

**Important Security Notes:**
- Never commit the `.env` file to version control
- Use environment variables or secret managers for production deployments
- The `.gitignore` file is configured to exclude `.env` files

### 4. Odoo Configuration

Ensure your Odoo instance has:
- **Accounting and Invoicing modules** installed
- **XML-RPC access** enabled (usually enabled by default)
- **(Optional)** Custom field `confidence_score` added to relevant models (e.g., `account.move`) via Odoo Studio
- **(Optional)** Email templates configured for AR follow-ups

## Usage

### Run Locally

Execute the main script:

```bash
python main.py
```

The agent will:
1. Authenticate with Odoo
2. Initialize all modules (OCR, Reconciliation, AR/AP, Payroll)
3. Run automated tasks
4. Log all operations with detailed feedback

### Run with Docker

#### Build the Docker Image

```bash
docker build -t ai-bookkeeper .
```

#### Run the Container

```bash
docker run --env-file .env ai-bookkeeper
```

Or pass environment variables directly:

```bash
docker run \
  -e ODOO_URL=https://your-odoo-instance.com \
  -e ODOO_DB=your_database \
  -e ODOO_USERNAME=your_username \
  -e ODOO_PASSWORD=your_password \
  -e OPENAI_API_KEY=your_api_key \
  ai-bookkeeper
```

## Key Improvements & Bug Fixes

### 1. Domain Error Handling
- **Issue**: Invalid domain values (e.g., `False`) causing `ValueError`
- **Fix**: Added `clean_domain()` method in `OdooClient` to validate and filter domains
- **Result**: Robust domain preprocessing with logging before sending to Odoo

### 2. Authentication Error Handling
- **Issue**: Generic authentication failures without helpful error messages
- **Fix**: Enhanced `authenticate()` with detailed error messages and troubleshooting hints
- **Result**: Clear feedback when credentials or configuration are incorrect

### 3. OCR Error Handling
- **Issue**: OCR failures on corrupted or invalid image data
- **Fix**: Added validation, error handling, and detailed logging in `OCRProcessor`
- **Result**: Graceful handling of invalid images with informative error messages

### 4. AR/AP Validation
- **Issue**: Attempting to send emails to partners without email addresses
- **Fix**: Added validation for partner IDs and email addresses before sending
- **Result**: Prevents errors and logs warnings for missing contact information

### 5. AI Guardrails
- **Issue**: Deprecated OpenAI API, missing client initialization
- **Fix**: Updated to latest OpenAI API (v1.0+), added proper error handling
- **Result**: AI categorization works with current OpenAI library

### 6. Comprehensive Logging
- **Added**: Logging throughout all modules for better debugging and monitoring
- **Result**: Clear operational feedback and easier troubleshooting

### 7. Docker Improvements
- **Added**: System dependencies for EasyOCR
- **Added**: Environment variable support
- **Result**: Fully functional containerized deployment

## Modules Overview

### `config.py`
Centralizes configuration using environment variables with secure defaults.

### `odoo_client.py`
Handles all Odoo XML-RPC communication with:
- Authentication with detailed error handling
- Domain cleaning and validation
- CRUD operations (search_read, create, write, unlink)
- Comprehensive logging

### `reconciliation.py`
Automates bank reconciliation:
- Fetches bank statements and move lines
- Auto-matches by amount and reference
- Reconciles matched entries
- Flags discrepancies for manual review

### `ar_ap_automation.py`
Manages accounts receivable and payable:
- Monitors overdue AR invoices
- Sends follow-up emails (with partner validation)
- Schedules AP payments for upcoming due dates

### `ocr_processor.py`
Processes invoice images:
- Extracts text using EasyOCR
- Parses invoice number, date, and total
- Handles errors gracefully

### `ai_guardrails.py`
AI-powered categorization with confidence scoring:
- Uses OpenAI for transaction categorization
- Sets low-confidence records to Draft
- Requires human review for uncertain transactions

### `payroll_reporting.py`
Syncs payroll data:
- Creates journal entries for completed payslips
- Generates financial reports (P&L, Balance Sheet)

### `main.py`
Main orchestrator:
- Initializes all modules
- Runs automated tasks in sequence
- Provides comprehensive logging

## Logging

All modules use Python's `logging` module with the following levels:
- **INFO**: Normal operations and progress
- **WARNING**: Non-critical issues (e.g., missing email addresses)
- **ERROR**: Errors that prevent specific operations

Logs include timestamps, module names, and detailed messages for troubleshooting.

## Deployment

### Local Deployment

1. Follow the setup steps above
2. Run manually: `python main.py`
3. Or schedule with cron for periodic execution:

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/Agent-accountant && /usr/bin/python3 main.py >> /var/log/ai-bookkeeper.log 2>&1
```

### Docker Deployment

Use the provided `Dockerfile` for containerized deployment:

```bash
docker build -t ai-bookkeeper .
docker run --env-file .env ai-bookkeeper
```

### Cloud Deployment

#### AWS Lambda / Cloud Run
1. Package the application with dependencies
2. Configure environment variables in the cloud platform
3. Set up scheduled triggers (EventBridge, Cloud Scheduler)

#### Heroku
1. Create a `Procfile`:
   ```
   worker: python main.py
   ```
2. Deploy with Heroku CLI:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```
3. Configure environment variables in Heroku dashboard

## Security Best Practices

1. **Never commit secrets**: Use `.env` files (excluded by `.gitignore`)
2. **Use environment variables**: All sensitive data should come from env vars
3. **Rotate credentials**: Regularly update Odoo passwords and API keys
4. **Limit API permissions**: Use Odoo users with minimal required permissions
5. **Monitor logs**: Review logs for unauthorized access or errors

## Troubleshooting

### Authentication Errors
- Verify `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, and `ODOO_PASSWORD`
- Check that XML-RPC is enabled in Odoo
- Ensure the user has necessary permissions

### Domain Errors
- Check logs for "Domain being sent to Odoo"
- Ensure domain conditions are in the format: `[('field', 'operator', 'value')]`
- Avoid passing `False` or `None` in domains

### OCR Errors
- Ensure EasyOCR dependencies are installed
- Check that image files are valid and not corrupted
- Review logs for specific error messages

### AI Categorization Not Working
- Verify `OPENAI_API_KEY` is set correctly
- Check OpenAI API quota and status
- Review logs for API errors

### Email Sending Failures
- Verify partners have valid email addresses
- Check Odoo email configuration (outgoing mail server)
- Review logs for specific partner validation errors

## Testing

This project does not include automated tests. For manual testing:

1. **Test Authentication**: Run `python main.py` and verify connection
2. **Test Reconciliation**: Check logs for matched/unmatched transactions
3. **Test AR/AP**: Verify emails sent for overdue invoices
4. **Test OCR**: Process sample invoice images
5. **Test AI**: Verify categorization and confidence scores

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper logging and error handling
4. Test thoroughly
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for detailed error messages
3. Open an issue on the repository

## Note

This is an external agent that integrates with Odoo via XML-RPC. For deeper integration with Odoo's internal workflows, consider developing custom Odoo modules that leverage internal APIs and hooks.