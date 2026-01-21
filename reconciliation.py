from odoo_client import OdooClient
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ReconciliationAgent:
    def __init__(self, client):
        self.client = client

    def fetch_bank_statements(self):
        """Fetch bank statement lines from Odoo."""
        try:
            logger.info("Fetching bank statement lines...")
            lines = self.client.search_read('account.bank.statement.line', [], ['id', 'date', 'amount', 'ref'])
            logger.info(f"Fetched {len(lines)} bank statement lines")
            return pd.DataFrame(lines)
        except Exception as e:
            logger.error(f"Error fetching bank statements: {e}")
            return pd.DataFrame()

    def fetch_move_lines(self):
        """Fetch unreconciled move lines from Odoo."""
        try:
            # Create proper domain for unreconciled lines
            domain = [('reconciled', '=', False)]
            logger.info("Fetching unreconciled move lines...")
            lines = self.client.search_read('account.move.line', domain, ['id', 'date', 'debit', 'credit', 'ref'])
            logger.info(f"Fetched {len(lines)} unreconciled move lines")
            return pd.DataFrame(lines)
        except Exception as e:
            logger.error(f"Error fetching move lines: {e}")
            return pd.DataFrame()

    def auto_match(self, statements, moves):
        """Match bank statements with move lines by amount and reference.
        
        Args:
            statements: DataFrame of bank statements
            moves: DataFrame of move lines
            
        Returns:
            List of tuples (statement_id, move_id) representing matches
        """
        if statements.empty or moves.empty:
            logger.warning("Cannot perform matching: statements or moves DataFrame is empty")
            return []
            
        matches = []
        for _, stmt in statements.iterrows():
            # Match by amount and ref
            potential = moves[
                ((moves['debit'] == stmt['amount']) | (moves['credit'] == stmt['amount'])) & 
                (moves['ref'] == stmt['ref'])
            ]
            if not potential.empty:
                match = potential.iloc[0]
                matches.append((stmt['id'], match['id']))
                moves = moves.drop(match.name)  # Remove matched
                logger.info(f"Matched statement {stmt['id']} with move line {match['id']}")
        
        logger.info(f"Found {len(matches)} automatic matches")
        return matches

    def reconcile(self, matches):
        """Reconcile matched statement and move line pairs.
        
        Args:
            matches: List of tuples (statement_id, move_id)
        """
        for stmt_id, move_id in matches:
            try:
                # Use Odoo's reconciliation logic; this is simplified
                self.client.write('account.move.line', [move_id], {'reconciled': True})
                logger.info(f"Reconciled statement {stmt_id} with move line {move_id}")
                # Populate reconciliation widget (this might require custom logic)
            except Exception as e:
                logger.error(f"Error reconciling statement {stmt_id} with move {move_id}: {e}")

    def flag_discrepancies(self, unmatched_statements, unmatched_moves):
        """Log unmatched statements and moves for manual review.
        
        Args:
            unmatched_statements: DataFrame of unmatched bank statements
            unmatched_moves: DataFrame of unmatched move lines
        """
        # Log or create discrepancy records
        if not unmatched_statements.empty:
            logger.warning(f"Found {len(unmatched_statements)} unmatched bank statements:")
            for _, stmt in unmatched_statements.iterrows():
                logger.warning(f"  - Unmatched bank statement ID: {stmt['id']}, Amount: {stmt.get('amount', 'N/A')}, Ref: {stmt.get('ref', 'N/A')}")
        
        if not unmatched_moves.empty:
            logger.warning(f"Found {len(unmatched_moves)} unmatched move lines:")
            for _, move in unmatched_moves.iterrows():
                logger.warning(f"  - Unmatched move line ID: {move['id']}, Debit: {move.get('debit', 0)}, Credit: {move.get('credit', 0)}, Ref: {move.get('ref', 'N/A')}")
        
        # For custom dashboard, perhaps create records in a custom model if available

    def run(self):
        """Run the reconciliation process."""
        try:
            logger.info("Starting reconciliation process...")
            statements = self.fetch_bank_statements()
            moves = self.fetch_move_lines()
            
            if statements.empty or moves.empty:
                logger.warning("Cannot perform reconciliation: no statements or moves to process")
                return
            
            matches = self.auto_match(statements, moves)
            self.reconcile(matches)
            
            # Flag unmatched
            unmatched_stmts = statements[~statements['id'].isin([m[0] for m in matches])]
            unmatched_moves = moves[~moves['id'].isin([m[1] for m in matches])]
            self.flag_discrepancies(unmatched_stmts, unmatched_moves)
            
            logger.info("Reconciliation process completed")
        except Exception as e:
            logger.error(f"Error during reconciliation process: {e}")