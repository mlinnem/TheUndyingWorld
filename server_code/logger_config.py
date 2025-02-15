import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Debug prints to help diagnose the issue
    print("Current working directory:", os.getcwd())
    print("Attempting to create log directory at:", 'persistent/conversation_logs/')
    
    # Create logs directory if it doesn't exist
    log_dir = 'persistent/conversation_logs/'
    try:
        os.makedirs(log_dir, exist_ok=True)
        print("Successfully created/verified log directory")
    except Exception as e:
        print(f"Error creating log directory: {e}")
        # Fallback to a local logs directory
        log_dir = os.path.join(os.getcwd(), 'logs')
        print(f"Falling back to local directory: {log_dir}")
        os.makedirs(log_dir, exist_ok=True)
    
    # Define log files for different levels
    debug_log_file = os.path.join(log_dir, 'debug.log')
    info_log_file = os.path.join(log_dir, 'info.log')
    
    # Create formatter (will be used by all handlers)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create and configure debug file handler (captures everything)
    debug_file_handler = RotatingFileHandler(debug_log_file, maxBytes=1024*1024, backupCount=5)
    debug_file_handler.setFormatter(log_formatter)
    debug_file_handler.setLevel(logging.DEBUG)
    
    # Create and configure info file handler (captures INFO and above)
    info_file_handler = RotatingFileHandler(info_log_file, maxBytes=1024*1024, backupCount=5)
    info_file_handler.setFormatter(log_formatter)
    info_file_handler.setLevel(logging.INFO)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configure the default logger
    logging.basicConfig(
        level=logging.DEBUG,  # Set root logger to capture everything
        handlers=[debug_file_handler, info_file_handler, console_handler],
        force=True  # This will remove any existing handlers
    )

def set_console_level_for_module(module_name: str, level: int | str):
    """
    Set console logging level for a specific module.
    
    Args:
        module_name: The name of the module (e.g., 'server_code.llm_communication')
        level: Logging level - can be integer (e.g., logging.DEBUG) 
              or string (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    # Convert string level to integer if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    target_logger = logging.getLogger(module_name)
    
    # Find the console handler
    for handler in target_logger.handlers + logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(level)
            
    logger.info(f"Set console logging level to {logging.getLevelName(level)} for {module_name}")

# Call setup_logging when this module is imported
setup_logging()

# Create module logger
logger = logging.getLogger(__name__) 