"""
Unit tests for the logger module.
"""
import pytest
import logging
import io
import sys
from unittest.mock import patch

from bsti_nessus.utils.logger import CustomLogger, setup_logging, log


@pytest.fixture
def capture_logs():
    """Fixture to capture log output for testing."""
    # Create a string IO object to capture log output
    log_capture = io.StringIO()
    # Create a handler that writes to the StringIO object
    handler = logging.StreamHandler(log_capture)
    # Add the handler to our logger
    log.handlers = []
    log.addHandler(handler)
    # Return the StringIO object for assertion
    return log_capture


class TestCustomLogger:
    """Tests for the CustomLogger class."""
    
    def test_custom_logger_initialization(self):
        """Test that CustomLogger initializes with proper attributes."""
        logger = CustomLogger("test_logger")
        assert logger.name == "test_logger"
        assert logger.level == logging.NOTSET
        assert CustomLogger.SUCCESS == 25
        
    def test_success_log_level(self):
        """Test the custom SUCCESS log level."""
        logger = CustomLogger("test_logger")
        logger.setLevel(CustomLogger.SUCCESS)
        
        # The logger should log SUCCESS messages
        assert logger.isEnabledFor(CustomLogger.SUCCESS)
        # It should not log INFO messages (which are lower level)
        assert not logger.isEnabledFor(logging.INFO)
        
    def test_success_method(self, capture_logs):
        """Test the success logging method."""
        log.setLevel(CustomLogger.SUCCESS)
        log.success("This is a success message")
        
        # Check that the message appears in the log
        log_output = capture_logs.getvalue()
        assert "This is a success message" in log_output


class TestSetupLogging:
    """Tests for the setup_logging function."""
    
    def test_verbosity_debug(self):
        """Test setup with debug verbosity."""
        setup_logging(verbosity=2)
        assert log.level == logging.DEBUG
        
    def test_verbosity_info(self):
        """Test setup with info verbosity."""
        setup_logging(verbosity=1)
        assert log.level == logging.INFO
        
    def test_verbosity_warning(self):
        """Test setup with warning verbosity."""
        setup_logging(verbosity=0)
        assert log.level == logging.WARNING
        
    @patch('os.makedirs')
    @patch('logging.FileHandler')
    def test_log_file_creation(self, mock_file_handler, mock_makedirs):
        """Test that log files are created correctly."""
        # Set up mocks
        mock_file_handler.return_value.setLevel.return_value = None
        
        # Call the function with a log file
        setup_logging(verbosity=1, log_file="logs/test.log")
        
        # Verify the file handler was created
        mock_file_handler.assert_called_once_with("logs/test.log")
        # Verify log level was set to DEBUG for file handler
        mock_file_handler.return_value.setLevel.assert_called_once_with(logging.DEBUG)
        
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('logging.FileHandler')
    def test_log_directory_creation(self, mock_file_handler, mock_exists, mock_makedirs):
        """Test that log directories are created if they don't exist."""
        # Set up mocks
        mock_exists.return_value = False
        
        # Call the function with a log file in a non-existent directory
        setup_logging(log_file="logs/nested/test.log")
        
        # Verify directory was created
        mock_makedirs.assert_called_once_with("logs/nested")


class TestLogLevels:
    """Test the different log levels."""
    
    @pytest.mark.parametrize("log_method, log_level", [
        (log.debug, logging.DEBUG),
        (log.info, logging.INFO),
        (log.success, CustomLogger.SUCCESS),
        (log.warning, logging.WARNING),
        (log.error, logging.ERROR),
        (log.critical, logging.CRITICAL),
    ])
    def test_log_levels(self, log_method, log_level, capture_logs):
        """Test that each log level produces output at appropriate level."""
        # Set the log level to ensure the message is recorded
        log.setLevel(log_level)
        
        # Log a message
        log_method(f"Test message at {logging.getLevelName(log_level)} level")
        
        # Verify the message appears in the log
        log_output = capture_logs.getvalue()
        assert f"Test message at {logging.getLevelName(log_level)} level" in log_output 