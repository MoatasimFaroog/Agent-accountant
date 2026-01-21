from odoo_client import OdooClient
import logging

logger = logging.getLogger(__name__)

class PayrollAgent:
    def __init__(self, client):
        self.client = client

    def sync_payroll_entries(self):
        """Sync payroll entries by creating journal entries for processed payslips."""
        try:
            logger.info("Syncing payroll entries...")
            # Fetch payslips and create journal entries
            payslips = self.client.search_read('hr.payslip', [('state', '=', 'done')], ['id', 'employee_id', 'net'])
            
            if not payslips:
                logger.info("No completed payslips found")
                return
            
            logger.info(f"Found {len(payslips)} completed payslips")
            for slip in payslips:
                try:
                    # Create account.move for payroll
                    move_data = {
                        'move_type': 'entry',
                        'journal_id': 1,  # Assume journal ID - should be configured
                        'line_ids': [
                            (0, 0, {
                                'account_id': 1,  # Should be configured
                                'debit': slip.get('net', 0),
                                'name': f'Payroll for {slip.get("employee_id", ["Unknown"])[1] if slip.get("employee_id") else "Unknown"}'
                            }),
                            (0, 0, {
                                'account_id': 2,  # Should be configured
                                'credit': slip.get('net', 0),
                                'name': 'Payroll Expense'
                            })
                        ]
                    }
                    move_id = self.client.create('account.move', [move_data])
                    logger.info(f"Created journal entry {move_id} for payslip {slip.get('id')}")
                except Exception as e:
                    logger.error(f"Error creating journal entry for payslip {slip.get('id')}: {e}")
        except Exception as e:
            logger.error(f"Error syncing payroll entries: {e}")

    def generate_reports(self):
        """Generate financial reports (P&L and Balance Sheet)."""
        try:
            logger.info("Generating financial reports...")
            # Fetch P&L and Balance Sheet data
            # Use account.financial.report or custom query
            pl_data = self.client.execute(
                'account.financial.report',
                'get_lines',
                [1],
                {
                    'date_from': '2024-01-01',
                    'date_to': '2024-12-31'
                }
            )
            logger.info(f"P&L Report generated with {len(pl_data) if isinstance(pl_data, list) else 'N/A'} lines")
            # Similarly for Balance Sheet
        except Exception as e:
            logger.error(f"Error generating reports: {e}")

    def run(self):
        """Run payroll sync and report generation."""
        try:
            logger.info("Starting payroll agent...")
            self.sync_payroll_entries()
            self.generate_reports()
            logger.info("Payroll agent completed")
        except Exception as e:
            logger.error(f"Error in payroll agent: {e}")