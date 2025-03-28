import logging
import colorlog
import os
import sys

# Define the custom logging level for success
SUCCESS = 35
logging.SUCCESS = SUCCESS
logging.addLevelName(SUCCESS, "SUCCESS")

class CustomLogger(logging.Logger):
    def success(self, msg, *args, **kwargs):
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kwargs)
    
    def set_level(self, level):
        """
        Set the logging level. Accepts either a numeric level or a string level name.
        
        Args:
            level: Can be a numeric level (e.g., logging.DEBUG) or a string level name (e.g., 'DEBUG')
        """
        if isinstance(level, str):
            # Convert string level to numeric level
            try:
                numeric_level = getattr(logging, level.upper())
                self.setLevel(numeric_level)
            except AttributeError:
                self.warning(f"Invalid log level: {level}")
                self.warning("Using default level: INFO")
                self.setLevel(logging.INFO)
        else:
            # Assume it's already a numeric level
            self.setLevel(level)

# Create logger
log = CustomLogger(__name__)
log.setLevel(logging.INFO)  # Set the default level

# Define log formats with color and include only time in timestamp
formatter = colorlog.ColoredFormatter(
    '%(log_color)s[%(asctime)s] - [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'WARNING': 'yellow',
        'INFO': 'blue',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
        'SUCCESS': 'green'
    },
    secondary_log_colors={},
    style='%'
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
log.addHandler(console_handler)

def setup_file_logging():
    """
    Set up file logging. This is separated into a function to handle
    potential errors when creating the log directory.
    """
    try:
        # Ensure the directory exists
        nmb_log_dir = os.path.join("logs", "nmb")
        os.makedirs(nmb_log_dir, exist_ok=True)

        # File Handler
        nmb_log_file_path = os.path.join(nmb_log_dir, 'NMB_output.log')
        file_handler = logging.FileHandler(nmb_log_file_path)
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)
        return True
    except Exception as e:
        # Don't fail if we can't set up file logging, just log to console
        log.warning(f"Could not set up file logging: {str(e)}")
        log.warning("Logging to console only")
        return False

# Try to set up file logging
setup_file_logging()
