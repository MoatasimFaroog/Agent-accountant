import logging
from config import OPENAI_API_KEY, CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

class AIGuardrails:
    def __init__(self, client=None):
        """Initialize AI Guardrails with optional Odoo client.
        
        Args:
            client: OdooClient instance for updating records
        """
        self.client = client
        
        # Check if OpenAI API key is configured
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured. AI categorization will not work.")
        else:
            try:
                # Use the new OpenAI client library
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.error("OpenAI library not installed. Install with: pip install openai")
                self.openai_client = None
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")
                self.openai_client = None

    def categorize_and_score(self, data):
        """Use AI to categorize transaction with confidence score.
        
        Args:
            data: Transaction data to categorize
            
        Returns:
            Tuple of (category, confidence_score)
        """
        if not self.openai_client:
            logger.error("OpenAI client not available. Cannot categorize.")
            return "Uncategorized", 0.0
        
        try:
            # Use the new chat completions API
            prompt = f"Categorize this transaction: {data}. Provide category and confidence score (0-1)."
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an accounting assistant. Categorize transactions and provide a confidence score between 0 and 1."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"AI categorization result: {result}")
            
            # Parse category and score
            # Simplified parsing - expect format like "Category: Expense, Confidence: 0.95"
            parts = result.split(',')
            category = parts[0].split(':')[-1].strip() if len(parts) > 0 else "Uncategorized"
            
            # Try to extract score
            score = 0.5  # Default
            if len(parts) > 1:
                score_str = parts[1].split(':')[-1].strip()
                try:
                    score = float(score_str)
                except ValueError:
                    logger.warning(f"Could not parse score from: {score_str}")
            
            return category, score
            
        except Exception as e:
            logger.error(f"Error in AI categorization: {e}")
            return "Uncategorized", 0.0

    def check_and_set(self, model, record_id, data):
        """Categorize data and update record based on confidence score.
        
        Args:
            model: Odoo model name
            record_id: Record ID to update
            data: Transaction data to categorize
            
        Returns:
            Category string
        """
        if not self.client:
            logger.error("Odoo client not provided. Cannot update records.")
            return "Uncategorized"
        
        category, score = self.categorize_and_score(data)
        
        try:
            if score < CONFIDENCE_THRESHOLD:
                logger.warning(f"Low confidence score ({score}) for record {record_id}. Setting to draft.")
                # Set to draft for human review
                self.client.write(model, [record_id], {'state': 'draft', 'confidence_score': score})
            else:
                logger.info(f"High confidence score ({score}) for record {record_id}.")
                self.client.write(model, [record_id], {'confidence_score': score})
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
        
        return category