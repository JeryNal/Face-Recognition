import logging
from datetime import datetime
import os

# Fix: Add directory check
def setup_logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'debug_{datetime.now().strftime("%Y%m%d")}.log')),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

def log_error(error, context=None):
    """Log errors with context"""
    logger.error(f"Error: {str(error)}, Context: {context}")

def log_info(message, context=None):
    """Log information with context"""
    logger.info(f"Info: {message}, Context: {context}") 