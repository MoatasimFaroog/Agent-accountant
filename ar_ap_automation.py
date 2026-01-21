from odoo_client import OdooClient
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ARAPAgent:
    def __init__(self, client):
        self.client = client

    def monitor_ar(self):
        """Monitor accounts receivable and send follow-up emails for overdue invoices."""
        try:
            logger.info("Monitoring accounts receivable...")
            # Fetch overdue out_invoices
            overdue = self.client.search_read('account.move', [
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '=', 'not_paid'),
                ('invoice_date_due', '<', datetime.now().date().isoformat())
            ], ['id', 'partner_id', 'amount_total', 'name'])
            
            logger.info(f"Found {len(overdue)} overdue invoices")
            for inv in overdue:
                self.send_followup_email(inv)
        except Exception as e:
            logger.error(f"Error monitoring AR: {e}")

    def send_followup_email(self, invoice):
        """Send follow-up email for overdue invoice.
        
        Args:
            invoice: Invoice record dict with partner_id, amount_total, etc.
        """
        try:
            # Validate partner_id
            if not invoice.get('partner_id'):
                logger.warning(f"Invoice {invoice.get('id', 'Unknown')} has no partner. Skipping email.")
                return
            
            partner_id = invoice['partner_id'][0] if isinstance(invoice['partner_id'], list) else invoice['partner_id']
            
            # Fetch partner to check if email exists
            partners = self.client.search_read('res.partner', [('id', '=', partner_id)], ['email', 'name'])
            if not partners or not partners[0].get('email'):
                logger.warning(f"Partner {partner_id} has no email address. Cannot send follow-up for invoice {invoice.get('id', 'Unknown')}.")
                return
            
            partner_email = partners[0]['email']
            partner_name = partners[0].get('name', 'Customer')
            
            # Use Odoo's mail.thread to send email
            message = f"Dear {partner_name},\n\nThis is a reminder that Invoice {invoice.get('name', invoice.get('id', 'Unknown'))} is overdue. Amount: ${invoice.get('amount_total', 0):.2f}\n\nPlease process the payment at your earliest convenience.\n\nThank you."
            
            logger.info(f"Sending follow-up email to {partner_email} for invoice {invoice.get('id', 'Unknown')}")
            
            self.client.execute('mail.thread', 'message_post', [partner_id], {
                'body': message,
                'message_type': 'email',
                'partner_ids': [partner_id],
                'subject': f"Payment Reminder: Invoice {invoice.get('name', invoice.get('id', 'Unknown'))}"
            })
            
            logger.info(f"Follow-up email sent successfully for invoice {invoice.get('id', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error sending follow-up email for invoice {invoice.get('id', 'Unknown')}: {e}")

    def schedule_ap_payments(self):
        """Schedule payments for accounts payable invoices due soon."""
        try:
            logger.info("Scheduling AP payments...")
            # Fetch in_invoices due soon
            due_soon = self.client.search_read('account.move', [
                ('move_type', '=', 'in_invoice'),
                ('payment_state', '=', 'not_paid'),
                ('invoice_date_due', '<=', (datetime.now() + timedelta(days=7)).date().isoformat())
            ], ['id', 'invoice_date_due', 'name', 'amount_total'])
            
            logger.info(f"Found {len(due_soon)} invoices due within 7 days")
            # Schedule payments (simplified: mark for payment)
            for inv in due_soon:
                logger.info(f"Schedule payment for invoice {inv.get('name', inv.get('id', 'Unknown'))} due {inv.get('invoice_date_due', 'Unknown')} - Amount: ${inv.get('amount_total', 0):.2f}")
        except Exception as e:
            logger.error(f"Error scheduling AP payments: {e}")

    def run(self):
        """Run AR/AP automation tasks."""
        try:
            logger.info("Starting AR/AP automation...")
            self.monitor_ar()
            self.schedule_ap_payments()
            logger.info("AR/AP automation completed")
        except Exception as e:
            logger.error(f"Error in AR/AP automation: {e}")