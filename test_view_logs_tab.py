#!/usr/bin/env python3
# Test script for BSTI View Logs Tab Component
# This script validates the functionality of the View Logs Tab component

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# Add the parent directory to sys.path to import the required modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Ensure PyQt5 is available for testing
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QListWidgetItem, QMessageBox, QFileDialog
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    from PyQt5.QtGui import QPixmap
except ImportError:
    print("Warning: PyQt5 not installed. GUI tests will be skipped.")
    HAS_PYQT = False
else:
    HAS_PYQT = True

# Import the module to test (with conditional import in case of PyQt absence)
if HAS_PYQT:
    from src.components.view_logs_tab import ViewLogsTab, LogsRefreshThread, ScreenshotDialog

class TestViewLogsTab(unittest.TestCase):
    """Test cases for the View Logs Tab implementation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        if HAS_PYQT:
            # Create a QApplication instance if not already created
            if not QApplication.instance():
                cls.app = QApplication([])
            else:
                cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures for each test."""
        if not HAS_PYQT:
            self.skipTest("PyQt5 not available")
            return
            
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock logs directory and files
        self.logs_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Create a mock log file
        self.log_file = os.path.join(self.logs_dir, "test_execution.log")
        with open(self.log_file, "w") as f:
            f.write("[INFO] 2023-03-27 14:30:00 - Test execution started\n")
            f.write("[DEBUG] 2023-03-27 14:30:05 - Processing data\n")
            f.write("[INFO] 2023-03-27 14:30:10 - Test execution completed\n")
        
        # Create a mock screenshot directory
        self.screenshots_dir = os.path.join(self.temp_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Store original directory to restore it after the test
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a real QWidget as parent instead of MagicMock
        self.parent = QWidget()
        
        # Mock the logs_dir and screenshots_dir paths to use our temp directories
        with patch('src.components.view_logs_tab.os.path.expanduser', return_value=self.temp_dir), \
             patch('src.components.view_logs_tab.ViewLogsTab.setup_ui'), \
             patch('src.components.view_logs_tab.ViewLogsTab.refresh_logs'):
            # Create the ViewLogsTab instance
            self.logs_tab = ViewLogsTab(self.parent)
            
            # Now mock the UI elements that would normally be created in setup_ui
            self.logs_tab.log_list = MagicMock()
            self.logs_tab.log_title = MagicMock()
            self.logs_tab.log_details = MagicMock()
            self.logs_tab.log_content = MagicMock()
            self.logs_tab.logs = []
            self.logs_tab.current_log = None
    
    def tearDown(self):
        """Tear down test fixtures after each test."""
        if not HAS_PYQT:
            return
            
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test proper initialization of the ViewLogsTab component."""
        self.assertIsNotNone(self.logs_tab)
        # Test that the object is of the correct type
        self.assertIsInstance(self.logs_tab, ViewLogsTab)
        # Test parent is set correctly
        self.assertEqual(self.logs_tab.parent_window, self.parent)
    
    def test_refresh_logs(self):
        """Test refreshing the logs list."""
        # Mock the LogsRefreshThread
        mock_thread = MagicMock()
        self.logs_tab.refresh_thread = mock_thread
        
        # Call the refresh method
        self.logs_tab.refresh_logs()
        
        # Verify UI was updated
        self.logs_tab.log_list.clear.assert_called_once()
        self.logs_tab.log_title.setText.assert_called_with("Refreshing logs...")
        self.logs_tab.log_details.setText.assert_called_with("")
        self.logs_tab.log_content.clear.assert_called_once()
        
        # Verify thread was started
        self.assertTrue(hasattr(self.logs_tab, 'refresh_thread'))
        mock_thread.start.assert_called_once()
    
    def test_update_logs(self):
        """Test updating the logs list with fetched logs."""
        # Mock log data
        logs = [
            {
                "name": "network_scan.log",
                "timestamp": "2023-03-27 14:30:00",
                "size": 12345,
                "path": "/logs/network_scan.log",
                "content": "Network scan log content"
            },
            {
                "name": "port_scan.log",
                "timestamp": "2023-03-27 15:30:00",
                "size": 8765,
                "path": "/logs/port_scan.log",
                "content": "Port scan log content"
            }
        ]
        
        # Call the update method
        self.logs_tab.update_logs(logs)
        
        # Verify UI was updated
        self.logs_tab.log_list.clear.assert_called_once()
        self.logs_tab.log_title.setText.assert_called_with("Select a log to view")
        self.logs_tab.log_details.setText.assert_called_with("2 logs available")
        
        # Verify logs were stored
        self.assertEqual(self.logs_tab.logs, logs)
        
        # Verify items were added to the list
        self.assertEqual(self.logs_tab.log_list.addItem.call_count, 2)
    
    def test_handle_refresh_error(self):
        """Test handling errors during log refresh."""
        # Mock QMessageBox
        with patch('PyQt5.QtWidgets.QMessageBox') as mock_message_box:
            # Call the error handler
            self.logs_tab.handle_refresh_error("Test error message")
            
            # Verify UI was updated
            self.logs_tab.log_title.setText.assert_called_with("Error refreshing logs")
            self.logs_tab.log_content.setText.assert_called_with("Test error message")
            
            # Verify QMessageBox was shown
            mock_message_box.warning.assert_called_once()
    
    def test_load_log(self):
        """Test loading a log file."""
        # Setup mock item
        mock_item = MagicMock()
        log_data = {
            "name": "network_scan.log",
            "timestamp": "2023-03-27 14:30:00",
            "size": 12345,
            "path": "/logs/network_scan.log",
            "content": "Network scan log content"
        }
        mock_item.data.return_value = log_data
        
        # Call the load method
        self.logs_tab.load_log(mock_item)
        
        # Verify UI was updated
        self.logs_tab.log_title.setText.assert_called_with("network_scan.log")
        self.logs_tab.log_content.setText.assert_called_with("Network scan log content")
        
        # Verify current log was updated
        self.assertEqual(self.logs_tab.current_log, log_data)
    
    @patch('src.components.view_logs_tab.ScreenshotDialog')
    @patch('PyQt5.QtWidgets.QApplication.primaryScreen')
    def test_take_screenshot(self, mock_screen, mock_dialog):
        """Test taking a screenshot."""
        # Setup mock dialog
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.exec_.return_value = True  # Dialog accepted
        mock_dialog_instance.title_input.text.return_value = "Test Screenshot"
        mock_dialog_instance.plugin_id.text.return_value = "12345"
        mock_dialog_instance.description.text.return_value = "Test description"
        mock_dialog.return_value = mock_dialog_instance
        
        # Setup current log
        self.logs_tab.current_log = {
            "name": "network_scan.log",
            "content": "Network scan log content"
        }
        
        # Mock screen capture
        mock_screen_instance = MagicMock()
        mock_pixmap = MagicMock()
        mock_screen_instance.grabWindow.return_value = mock_pixmap
        mock_screen.return_value = mock_screen_instance
        
        # Mock QFileDialog.getSaveFileName
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName', 
                  return_value=(os.path.join(self.screenshots_dir, "test_screenshot.png"), "PNG Files (*.png)")):
            # Call the screenshot method
            self.logs_tab.take_screenshot()
            
            # Verify dialog was created
            mock_dialog.assert_called_once()
            mock_dialog_instance.exec_.assert_called_once()
            
            # Verify screenshot was saved
            mock_pixmap.save.assert_called_once()
    
    @patch('PyQt5.QtWidgets.QMessageBox')
    def test_delete_log(self, mock_message_box):
        """Test deleting a log."""
        # Setup mock message box
        mock_message_box_instance = MagicMock()
        mock_message_box_instance.exec_.return_value = mock_message_box.Yes
        mock_message_box.return_value = mock_message_box_instance
        mock_message_box.Yes = mock_message_box.Yes  # Use the class constant
        
        # Setup current log
        self.logs_tab.current_log = {
            "name": "network_scan.log",
            "path": os.path.join(self.logs_dir, "network_scan.log")
        }
        
        # Mock os.remove and refresh_logs
        with patch('os.remove') as mock_remove:
            self.logs_tab.refresh_logs = MagicMock()
            
            # Call the delete method
            self.logs_tab.delete_log()
            
            # Verify confirmation dialog was shown
            mock_message_box.question.assert_called_once()
            
            # Verify file was deleted
            mock_remove.assert_called_once_with(os.path.join(self.logs_dir, "network_scan.log"))
            
            # Verify logs were refreshed
            self.logs_tab.refresh_logs.assert_called_once()
    
    def test_logs_refresh_thread(self):
        """Test the logs refresh thread."""
        # Create a refresh thread
        thread = LogsRefreshThread()
        
        # Mock the signals
        thread.logs_updated = MagicMock()
        thread.error_signal = MagicMock()
        
        # Run the thread
        thread.run()
        
        # Verify logs were emitted
        thread.logs_updated.emit.assert_called_once()
        # We expect 4 logs from the simulation
        logs = thread.logs_updated.emit.call_args[0][0]
        self.assertEqual(len(logs), 4)

if __name__ == '__main__':
    unittest.main() 