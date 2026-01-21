import logging
from odoo_client import OdooClient
from ocr_processor import OCRProcessor
from reconciliation import ReconciliationAgent
from ar_ap_automation import ARAPAgent
from payroll_reporting import PayrollAgent
from ai_guardrails import AIGuardrails

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for AI Bookkeeper Agent."""
    try:
        logger.info("=" * 80)
        logger.info("Starting AI Bookkeeper Agent for Odoo Integration")
        logger.info("=" * 80)
        
        # Initialize Odoo client
        logger.info("Initializing Odoo client...")
        client = OdooClient()
        
        # Initialize OCR processor
        logger.info("Initializing OCR processor...")
        ocr = OCRProcessor()
        
        # Initialize agents
        logger.info("Initializing reconciliation agent...")
        recon = ReconciliationAgent(client)
        
        logger.info("Initializing AR/AP agent...")
        arap = ARAPAgent(client)
        
        logger.info("Initializing payroll agent...")
        payroll = PayrollAgent(client)
        
        logger.info("Initializing AI guardrails...")
        ai = AIGuardrails(client)

        # Example: OCR on an attachment
        # Assume attachment bytes from Odoo
        # logger.info("Processing invoice with OCR...")
        # text = ocr.extract_text(attachment_bytes)
        # data = ocr.extract_invoice_data(text)
        # bill_id = client.create('account.move', [{'move_type': 'in_invoice', ...}])
        # ai.check_and_set('account.move', bill_id, data)

        # Run automations
        logger.info("\n" + "=" * 80)
        logger.info("Running Reconciliation Agent")
        logger.info("=" * 80)
        recon.run()
        
        logger.info("\n" + "=" * 80)
        logger.info("Running AR/AP Automation Agent")
        logger.info("=" * 80)
        arap.run()
        
        logger.info("\n" + "=" * 80)
        logger.info("Running Payroll Agent")
        logger.info("=" * 80)
        payroll.run()
        
        logger.info("\n" + "=" * 80)
        logger.info("AI Bookkeeper Agent completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()