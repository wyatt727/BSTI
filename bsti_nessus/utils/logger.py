"""
Logging utility for the BSTI Nessus to Plextrac converter.
"""
import logging
import sys
import os
from typing import Optional

class CustomLogger(logging.Logger):
    """
    Custom logger class with additional log levels and colored output.
    """
    SUCCESS = 25  # Between INFO and WARNING

    def __init__(self, name: str, level: int = logging.NOTSET):
        """Initialize the custom logger with a name and default level."""
        super().__init__(name, level)
        # Add our custom log level
        logging.addLevelName(self.SUCCESS, 'SUCCESS')

    def success(self, msg: str, *args, **kwargs):
        """Log a message with SUCCESS level."""
        if self.isEnabledFor(self.SUCCESS):
            self._log(self.SUCCESS, msg, args, **kwargs)

# For backward compatibility
Logger = CustomLogger

# Register our custom logger class
logging.setLoggerClass(CustomLogger)

# Create our logger instance
log = logging.getLogger('bsti_nessus')

def setup_logging(verbosity: Optional[int] = None, log_file: Optional[str] = None):
    """
    Set up logging configuration based on verbosity level.
    
    Args:
        verbosity (int, optional): 0=Warning, 1=Info, 2=Debug
        log_file (str, optional): Path to log file
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
    
    # Create a formatter with ANSI color codes for console output
    class ColoredFormatter(logging.Formatter):
        """
        Logging formatter with colored output.
        """
        COLORS = {
            'DEBUG': '\033[36m',      # cyan
            'INFO': '\033[32m',       # green
            'SUCCESS': '\033[1;32m',  # bold green
            'WARNING': '\033[33m',    # yellow
            'ERROR': '\033[31m',      # red
            'CRITICAL': '\033[1;31m', # bold red
            'RESET': '\033[0m',       # reset
        }
        
        def format(self, record):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname_colored = f"{color}[{record.levelname}]{self.COLORS['RESET']}"
            return super().format(record)
    
    # Create formatters
    console_formatter = ColoredFormatter('%(levelname_colored)s %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add the handler to the logger
    log.handlers = []  # Clear existing handlers
    log.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', 
                                        datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        log.addHandler(file_handler)
    
    log.debug("Logging initialized with verbosity level %s", verbosity) 