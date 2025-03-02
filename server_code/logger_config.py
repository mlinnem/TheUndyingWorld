import os
import logging
from logging.handlers import RotatingFileHandler


  # Create formatter (will be used by all handlers)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    

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
    
  
    # Create and configure debug file handler (captures everything)
    debug_file_handler = RotatingFileHandler(debug_log_file, maxBytes=1024*1024*30, backupCount=5)
    debug_file_handler.setFormatter(log_formatter)
    debug_file_handler.setLevel(logging.DEBUG)
    
    # Create and configure info file handler (captures INFO and above)
    info_file_handler = RotatingFileHandler(info_log_file, maxBytes=1024*1024*30, backupCount=5)
    info_file_handler.setFormatter(log_formatter)
    info_file_handler.setLevel(logging.INFO)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)  # Set default console level to INFO
    
    # Configure the default logger
    logging.basicConfig(
        level=logging.DEBUG,  # Root logger still captures everything for file logging
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
    
    # Get the logger for this module
    module_logger = logging.getLogger(module_name)
    
    # Create a new console handler specific to this module
    module_console_handler = logging.StreamHandler()
    module_console_handler.setFormatter(log_formatter)
    module_console_handler.setLevel(level)
    
    # Remove any existing console handlers for this module
    for handler in module_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            module_logger.removeHandler(handler)
    
    # Add the new console handler
    module_logger.addHandler(module_console_handler)
    # Ensure the logger's level is low enough to allow the desired messages through
    module_logger.setLevel(min(level, module_logger.level))
    
    # Prevent propagation to avoid duplicate logs
    module_logger.propagate = False
            
    logger.info(f"Set console logging level to {logging.getLevelName(level)} for {module_name}")

def setup_coaching_logger():
    """
    Set up a specialized logger for the coaching system that can be used across multiple files.
    Returns the logger instance.
    """
    # Create logs directory if it doesn't exist
    log_dir = 'persistent/conversation_logs/'
    coaching_log_file = os.path.join(log_dir, 'coaching.log')
    
    # Create coaching logger
    coach_logger = logging.getLogger('coaching')
    coach_logger.setLevel(logging.DEBUG)  # Capture everything at logger level
    
    # Create coaching file handler (DEBUG level)
    coaching_file_handler = RotatingFileHandler(
        coaching_log_file, 
        maxBytes=1024*1024*30,  # 30MB
        backupCount=5
    )
    coaching_file_handler.setFormatter(log_formatter)
    coaching_file_handler.setLevel(logging.DEBUG)  # File gets all debug messages
    
    # Create console handler specific to coaching (DEBUG level)
    coaching_console_handler = logging.StreamHandler()
    coaching_console_handler.setFormatter(log_formatter)
    coaching_console_handler.setLevel(logging.DEBUG)  # Console gets DEBUG and above for coaching
    
    # Remove any existing handlers
    coach_logger.handlers.clear()
    
    # Add the handlers
    coach_logger.addHandler(coaching_file_handler)
    coach_logger.addHandler(coaching_console_handler)
    
    # Prevent propagation to avoid duplicate logs
    coach_logger.propagate = False
    
    return coach_logger

# Call setup_logging when this module is imported
setup_logging()

# Create module logger
logger = logging.getLogger(__name__) 