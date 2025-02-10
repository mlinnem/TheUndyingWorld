import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Debug prints to help diagnose the issue
    print("Current working directory:", os.getcwd())
    print("Attempting to create log directory at:", '/persistent/conversation_logs/')
    
    # Create logs directory if it doesn't exist
    log_dir = '/persistent/conversation_logs/'
    try:
        os.makedirs(log_dir, exist_ok=True)
        print("Successfully created/verified log directory")
    except Exception as e:
        print(f"Error creating log directory: {e}")
        # Fallback to a local logs directory
        log_dir = os.path.join(os.getcwd(), 'logs')
        print(f"Falling back to local directory: {log_dir}")
        os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'app.log')
    print("Log file path:", log_file)
    
    # Create formatter
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create and configure file handler
    file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Configure the default logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler],
        force=True  # This will remove any existing handlers
    )

# Call setup_logging when this module is imported
setup_logging()

# Create module logger
logger = logging.getLogger(__name__) 