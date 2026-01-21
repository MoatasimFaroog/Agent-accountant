import xmlrpc.client
import logging
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OdooClient:
    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = self.authenticate()

    def authenticate(self):
        try:
            logger.info(f"Attempting to authenticate with Odoo at {self.url}")
            logger.info(f"Database: {self.db}, Username: {self.username}")
            uid = self.common.authenticate(self.db, self.username, self.password, {})
            if not uid:
                error_msg = (
                    "Authentication failed: Please check your credentials.\n"
                    f"  - ODOO_URL: {self.url}\n"
                    f"  - ODOO_DB: {self.db}\n"
                    f"  - ODOO_USERNAME: {self.username}\n"
                    "  - ODOO_PASSWORD: [hidden]\n"
                    "Ensure these values are correct in your .env file or environment variables."
                )
                logger.error(error_msg)
                raise Exception(error_msg)
            logger.info(f"Authentication successful. User ID: {uid}")
            return uid
        except xmlrpc.client.Fault as fault:
            error_msg = (
                f"XML-RPC Fault during authentication: {fault.faultString} (Code: {fault.faultCode})\n"
                "This usually means the Odoo URL, database name, or credentials are incorrect."
            )
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error connecting to Odoo: {str(e)}\nPlease check your ODOO_URL and network connection."
            logger.error(error_msg)
            raise Exception(error_msg)

    def execute(self, model, method, *args):
        try:
            return self.models.execute_kw(self.db, self.uid, self.password, model, method, *args)
        except xmlrpc.client.Fault as fault:
            raise Exception(f"XML-RPC Fault occurred: {fault.faultString} (Code: {fault.faultCode})")
        except Exception as e:
            raise Exception(f"An error occurred during execution: {e}")

    def clean_domain(self, domain):
        """Clean and validate domain before sending to Odoo.
        
        Args:
            domain: List of domain conditions
            
        Returns:
            Cleaned domain list
            
        Raises:
            ValueError: If domain is invalid
        """
        if not isinstance(domain, list):
            raise ValueError("Domain must be a list of conditions.")
        
        # Remove invalid items (e.g., False, None, empty lists)
        cleaned = []
        for cond in domain:
            if not cond:  # Skip False, None, empty strings, empty lists
                logger.warning(f"Skipping invalid domain condition: {cond}")
                continue
            if isinstance(cond, (list, tuple)):
                # Validate tuple format (field, operator, value)
                if len(cond) == 3:
                    cleaned.append(cond)
                else:
                    logger.warning(f"Skipping invalid domain tuple (expected 3 elements): {cond}")
            elif cond in ('&', '|', '!'):  # Logical operators
                cleaned.append(cond)
            else:
                logger.warning(f"Skipping unexpected domain item: {cond}")
        
        logger.info(f"Cleaned domain: {cleaned}")
        return cleaned

    def search_read(self, model, domain, fields=None):
        """Search and read records from Odoo.
        
        Args:
            model: Odoo model name
            domain: Search domain (list of conditions)
            fields: Fields to retrieve (list of field names)
            
        Returns:
            List of records
        """
        try:
            cleaned_domain = self.clean_domain(domain)
            logger.info(f"Executing search_read on model '{model}' with domain: {cleaned_domain}")
            result = self.execute(model, 'search_read', [cleaned_domain], {'fields': fields or []})
            logger.info(f"Retrieved {len(result)} records from {model}")
            return result
        except Exception as e:
            logger.error(f"Error in search_read with model {model}: {e}")
            raise Exception(f"Error in search_read with model {model}: {e}")

    def create(self, model, data):
        return self.execute(model, 'create', data)

    def write(self, model, ids, data):
        return self.execute(model, 'write', ids, data)

    def unlink(self, model, ids):
        return self.execute(model, 'unlink', ids)