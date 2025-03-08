import os
import logging
from logging.handlers import RotatingFileHandler


# Define logging categories and their default levels
class LogCategory:
    WORLD_GEN = "WORLD_GEN"
    LLM = "LLM"
    USAGE = "USAGE" # Only in normal conversation, not summarization or coaching
    CACHING = "CACHING"
    MESSAGE_FILTERING = "MESSAGE_FILTERING"
    CONVERT_MESSAGES_TO_COS = "CONVERT_MESSAGES_TO_COS"
    REVEAL_ANALYSIS = "REVEAL_ANALYSIS"
    REVEAL_LEVEL = "REVEAL_LEVEL"
    REVEAL_ROLL = "REVEAL_ROLL"
    TRACKED_OPERATIONS = "TRACKED_OPERATIONS"
    DIFFICULTY_ANALYSIS = "DIFFICULTY_ANALYSIS"
    DIFFICULTY_TARGET = "DIFFICULTY_TARGET"
    DIFFICULTY_ROLL = "DIFFICULTY_ROLL"
    SUMMARIZATION = "SUMMARIZATION"
    COACHING = "COACHING"
    ADVANCE_CONVERSATION_LOGIC = "ADVANCE_CONVERSATION_LOGIC"
    PERSISTENCE = "PERSISTENCE"


class LogLevel:
    VERBOSE_DEBUG = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

# Default levels for each category
category_levels = {
    LogCategory.WORLD_GEN: LogLevel.INFO,
    LogCategory.LLM: LogLevel.INFO,
    LogCategory.USAGE: LogLevel.INFO,
    LogCategory.DIFFICULTY_ANALYSIS: LogLevel.INFO,
    LogCategory.DIFFICULTY_TARGET: LogLevel.INFO,
    LogCategory.DIFFICULTY_ROLL: LogLevel.INFO,
    LogCategory.REVEAL_ANALYSIS: LogLevel.INFO,
    LogCategory.REVEAL_LEVEL: LogLevel.INFO,
    LogCategory.REVEAL_ROLL: LogLevel.INFO,
    LogCategory.TRACKED_OPERATIONS: LogLevel.INFO,
    LogCategory.CACHING: LogLevel.INFO,
    LogCategory.MESSAGE_FILTERING: LogLevel.WARNING,
    LogCategory.SUMMARIZATION: LogLevel.INFO,
    LogCategory.CONVERT_MESSAGES_TO_COS: LogLevel.ERROR,
    LogCategory.COACHING: LogLevel.INFO,
    LogCategory.ADVANCE_CONVERSATION_LOGIC: LogLevel.WARNING,
    LogCategory.PERSISTENCE: LogLevel.WARNING,
}

  # Create formatter (will be used by all handlers)
log_formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s', 
                                datefmt='%M:%S')
    
def setup_logging():
    # Debug prints to help diagnose the issue
    
    # Create logs directory if it doesn't exist
    log_dir = 'persistent/conversation_logs/'
    try:
        os.makedirs(log_dir, exist_ok=True)
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
    console_handler.setLevel(logging.DEBUG)  # Set to DEBUG to allow all messages through, we'll filter in the filter function
    
    # Add a filter to the console handler to respect category levels
    def category_filter(record):
        # Extract category from the message if it exists
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            message = str(record.msg)
            if message.startswith('['):
                try:
                    category = message[1:message.find(']')]
                    category_level = category_levels.get(category, logging.INFO)
                    return record.levelno >= category_level
                except:
                    pass
        # For messages without a category, use the handler's level
        return record.levelno >= logging.WARNING

    console_handler.addFilter(category_filter)
    
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

# Call setup_logging when this module is imported
setup_logging()

# Create module logger
logger = logging.getLogger(__name__) 



def set_category_level(category: str, level: int | str):
    """
    Set the logging level for a specific category.
    
    Args:
        category: The category to set (use LogCategory class constants)
        level: Logging level - can be integer or string
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    category_levels[category] = level
    logger.info(f"Set {category} logging level to {logging.getLevelName(level)}")

def log_with_category(category: str | list[str], level: int, message: str):
    """
    Log a message with different behaviors for console and file outputs:
    - Console: Only show if message meets category's level threshold
    - Info file: All messages of INFO level and above
    - Debug file: All messages of DEBUG level and above
    """
    if isinstance(category, str):
        categories = [category]
    else:
        categories = category

    # Format categories as [CAT1|CAT2|CAT3]
    category_str = '|'.join(categories)
    formatted_message = f"[{category_str}] {message}"

    # Get the root logger
    root_logger = logging.getLogger()
    
    # Create the log record once
    record = root_logger.makeRecord(
        root_logger.name,
        level,
        "(unknown file)", 0,
        formatted_message,
        None,
        None
    )
    
    # Log to each handler based on its type and level
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            # Console handler: Apply category-based filtering
            should_log = any(
                level >= category_levels.get(cat, logging.INFO)
                for cat in categories
            )
            if should_log:
                handler.handle(record)
        else:
            # File handlers: Use standard severity-based filtering
            if level >= handler.level:
                handler.handle(record)

def preview(message: str, preview_length: int = 50):
    """
    Logs a preview of a long string, showing the first N characters and remaining length.
    Special characters like newlines will be escaped (e.g., \n, \t).
    
    Args:
        message: The string to preview
        preview_length: Number of characters to show in preview (default: 50)
    """
    if not message:
        return "Empty or null message"
        
    # Escape special characters
    escaped_message = repr(message)[1:-1]  # repr() adds quotes, so we remove them
    
    text_length = len(message)
    preview = escaped_message[:preview_length]
    remaining_chars = text_length - preview_length
    
    if remaining_chars > 0:
        return f"{preview}...({remaining_chars} more chars)"
    else:
        return f"{preview}" 
