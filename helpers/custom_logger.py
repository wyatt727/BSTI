import logging
import sys
import os
from typing import Optional

# Create a custom logger class that has the success method
class CustomLogger(logging.Logger):
    SUCCESS = 25  # Custom log level between INFO and WARNING
    
    def __init__(self, name):
        super().__init__(name)
        logging.addLevelName(self.SUCCESS, 'SUCCESS')
    
    def success(self, msg, *args, **kwargs):
        """Log a message with SUCCESS level."""
        self.log(self.SUCCESS, msg, *args, **kwargs)

# Register our custom logger class
logging.setLoggerClass(CustomLogger)

# Create our logger instance
log = logging.getLogger('n2p_ng')

def setup_logging(verbosity: Optional[int] = None):
    """
    Set up logging configuration based on verbosity level.
    
    Args:
        verbosity (int, optional): 0=Warning, 1=Info, 2=Debug
    """
    # Create a StreamHandler for console output
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set the verbosity level
    if verbosity == 2:
        log.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    elif verbosity == 1:
        log.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
    else:  # Default
        log.setLevel(logging.WARNING)
        console_handler.setLevel(logging.WARNING)
    
    # Create a formatter
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    log.handlers = []  # Clear existing handlers
    log.addHandler(console_handler)
    
    log.debug("Logging initialized with verbosity level %s", verbosity)

# Initialize the logger with functions that conform to the existing API
def debug(message, *args, **kwargs):
    log.debug(message, *args, **kwargs)

def info(message, *args, **kwargs):
    log.info(message, *args, **kwargs)

def warning(message, *args, **kwargs):
    log.warning(message, *args, **kwargs)

def error(message, *args, **kwargs):
    log.error(message, *args, **kwargs)

def critical(message, *args, **kwargs):
    log.critical(message, *args, **kwargs)

def success(message, *args, **kwargs):
    """
    Custom log level for success messages, rendered at info level with [SUCCESS] prefix.
    """
    log.info(f"[SUCCESS] {message}", *args, **kwargs)