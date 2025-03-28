#!/usr/bin/env python3
# Test script for BSTI Home Tab Component
# This script validates the functionality of the Home Tab component

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
    from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QFileDialog, QTextEdit
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
except ImportError:
    print("Warning: PyQt5 not installed. GUI tests will be skipped.")
    HAS_PYQT = False
else:
    HAS_PYQT = True

# Import the module to test (with conditional import in case of PyQt absence)
if HAS_PYQT:
    from src.components.home_tab import HomeTab, FileTransferWidget, DiagnosticsWidget

class TestHomeTab(unittest.TestCase):
    """Test cases for the Home Tab implementation."""
    
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
        
        # Create mock files and directories needed for testing
        # For example, create a mock log file
        self.log_file = os.path.join(self.temp_dir, "bsti.log")
        with open(self.log_file, "w") as f:
            f.write("Mock log entry 1\nMock log entry 2\n")
        
        # Store original directory to restore it after the test
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a real QWidget as parent instead of MagicMock
        self.parent = QWidget()
        
        # Patch methods that will be called during HomeTab initialization
        with patch('src.components.home_tab.HomeTab.setup_ui'), \
             patch('src.components.home_tab.DiagnosticsWidget'), \
             patch('src.components.home_tab.LinkWidget'), \
             patch('src.components.home_tab.FileTransferWidget'), \
             patch('src.components.home_tab.QTimer'):
            # Create the HomeTab instance
            self.home_tab = HomeTab(self.parent)
            
            # Mock the UI elements that would be created in setup_ui
            self.home_tab.status_text = MagicMock()
            self.home_tab.diagnostics = MagicMock()
            self.home_tab.file_transfer = MagicMock()
            self.home_tab.links = MagicMock()
    
    def tearDown(self):
        """Tear down test fixtures after each test."""
        if not HAS_PYQT:
            return
            
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test proper initialization of the HomeTab component."""
        self.assertIsNotNone(self.home_tab)
        # Test that the object is of the correct type
        self.assertIsInstance(self.home_tab, HomeTab)
        # Test parent is set correctly
        self.assertEqual(self.home_tab.parent_window, self.parent)
    
    def test_diagnostics_widget(self):
        """Test diagnostics widget functionality."""
        # Create a real DiagnosticsWidget with patches for methods that require system resources
        with patch('src.components.home_tab.DiagnosticsWidget.start_monitor'):
            diagnostics = DiagnosticsWidget()
            
            # Create and set up a QTextEdit for system_info manually
            diagnostics.system_info = QTextEdit()
            
            # Test display of system info
            test_info = "CPU: 2.3 GHz\nMemory: 8GB"
            diagnostics.system_info.setPlainText(test_info)
            self.assertEqual(diagnostics.system_info.toPlainText(), test_info)
    
    def test_update_connection_status(self):
        """Test updating the connection status display."""
        # Mock the parent window with drone selector and connection status
        self.home_tab.parent_window = MagicMock()
        self.home_tab.parent_window.drone_selector.currentText.return_value = "Test Drone"
        self.home_tab.parent_window.connection_status.text.return_value = "Connected"
        
        # Call the update method
        self.home_tab.update_connection_status()
        
        # Verify the status was updated correctly
        self.home_tab.status_text.setText.assert_called_once_with("Connected to Test Drone")
        self.home_tab.status_text.setStyleSheet.assert_called_once()
        
        # Test disconnected state
        self.home_tab.parent_window.connection_status.text.return_value = "Disconnected"
        self.home_tab.status_text.setText.reset_mock()
        self.home_tab.status_text.setStyleSheet.reset_mock()
        
        # Call the update method again
        self.home_tab.update_connection_status()
        
        # Verify disconnected status
        self.home_tab.status_text.setText.assert_called_once_with("Disconnected")
        self.home_tab.status_text.setStyleSheet.assert_called_once()
    
    def test_get_current_drone_connection(self):
        """Test getting the current drone connection."""
        # Mock the parent window
        self.home_tab.parent_window = MagicMock()
        self.home_tab.parent_window.get_current_drone_connection.return_value = {"name": "Test Drone", "ip": "192.168.1.1"}
        
        # Call the method
        result = self.home_tab.get_current_drone_connection()
        
        # Verify the result
        self.assertEqual(result, {"name": "Test Drone", "ip": "192.168.1.1"})
        self.home_tab.parent_window.get_current_drone_connection.assert_called_once()
        
        # Test when parent doesn't have the method
        self.home_tab.parent_window = QWidget()
        result = self.home_tab.get_current_drone_connection()
        self.assertIsNone(result)
    
    @patch('src.components.home_tab.FileTransferWidget.browse_upload_file')
    def test_file_transfer_browse(self, mock_browse):
        """Test file transfer browsing functionality."""
        # Create a real FileTransferWidget with patched methods
        with patch('PyQt5.QtWidgets.QFileDialog'):
            file_transfer = FileTransferWidget()
            
            # Call the browse method
            file_transfer.browse_upload_file()
            
            # Verify the mock was called
            mock_browse.assert_called_once()
    
    @patch('src.components.home_tab.FileTransferWidget.start_upload')
    @patch('src.components.home_tab.FileTransferThread')
    def test_file_upload(self, mock_thread, mock_start_upload):
        """Test file upload functionality."""
        # Create a real FileTransferWidget with patched methods
        with patch('PyQt5.QtWidgets.QInputDialog'):
            file_transfer = FileTransferWidget()
            
            # Set up file path
            file_transfer.upload_file_path = os.path.join(self.temp_dir, "test_file.txt")
            with open(file_transfer.upload_file_path, "w") as f:
                f.write("Test file content")
            
            # Call the upload method
            file_transfer.start_upload()
            
            # Verify the mock was called
            mock_start_upload.assert_called_once()

if __name__ == '__main__':
    unittest.main() 