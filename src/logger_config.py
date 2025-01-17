

import logging
logger = logging.getLogger(__name__)
from logging.handlers import RotatingFileHandler


def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = 'app.log'
    
    # Create file handler with rotation
    file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Update console handler to show all levels
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Get the root logger and set its level
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers and add our handlers
    logger.handlers = []
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Call setup_logging when this module is imported
setup_logging() 