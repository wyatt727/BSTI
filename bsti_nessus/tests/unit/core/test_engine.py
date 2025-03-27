"""
Unit tests for the Engine module.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import json
import sys
from argparse import Namespace

from bsti_nessus.core.engine import NessusEngine


class TestNessusEngine(unittest.TestCase):
    """Tests for the NessusEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock command-line arguments
        self.args = Namespace()
        self.args.username = "testuser"
        self.args.password = "testpassword"
        self.args.target_plextrac = "dev"
        self.args.directory = "/tmp/nessus"
        self.args.scope = "internal"
        self.args.screenshots = False
        self.args.non_core = False
        self.args.cleanup = False
        self.args.client = None
        
        # Create patchers
        self.config_manager_patcher = patch('bsti_nessus.core.engine.ConfigManager')
        self.plextrac_api_patcher = patch('bsti_nessus.core.engine.PlextracAPI')
        self.nessus_parser_patcher = patch('bsti_nessus.core.engine.NessusParser')
        self.log_patcher = patch('bsti_nessus.core.engine.log')
        self.exit_patcher = patch('sys.exit')
        
        # Start patchers
        self.mock_config_manager = self.config_manager_patcher.start()
        self.mock_plextrac_api = self.plextrac_api_patcher.start()
        self.mock_nessus_parser = self.nessus_parser_patcher.start()
        self.mock_log = self.log_patcher.start()
        self.mock_exit = self.exit_patcher.start()
        
        # Configure mocks
        self.mock_config_manager_instance = self.mock_config_manager.return_value
        self.mock_config_manager_instance.get.side_effect = self._mock_config_get
        
        self.mock_plextrac_api_instance = self.mock_plextrac_api.return_value
        self.mock_plextrac_api_instance.get_flaws.return_value = (True, {})
        
        self.mock_nessus_parser_instance = self.mock_nessus_parser.return_value
        
        # Create engine instance with patches to prevent certain operations
        with patch.object(NessusEngine, '_load_existing_flaws'):
            self.engine = NessusEngine(self.args)
    
    def tearDown(self):
        """Clean up after tests."""
        self.config_manager_patcher.stop()
        self.plextrac_api_patcher.stop()
        self.nessus_parser_patcher.stop()
        self.log_patcher.stop()
        self.exit_patcher.stop()
    
    def _mock_config_get(self, key, default=None):
        """Mock implementation of ConfigManager.get()."""
        config_values = {
            'file_paths.plextrac_format': 'plextrac_format.csv',
            'file_paths.processed_findings': '_processed_findings.json',
            'file_paths.existing_flaws': 'existing_flaws.json',
            'file_paths.screenshot_dir': 'screenshots'
        }
        return config_values.get(key, default)
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertEqual(self.engine.args, self.args)
        self.assertEqual(self.engine.plextrac_format_file, 'plextrac_format.csv')
        self.assertEqual(self.engine.processed_findings_file, '_processed_findings.json')
        self.assertEqual(self.engine.existing_flaws_file, 'existing_flaws.json')
        self.assertEqual(self.engine.client_name, None)
        self.assertEqual(self.engine.mode, 'internal')
        
        # Verify API instances were created with correct args
        self.mock_plextrac_api.assert_called_once_with('dev')
        self.mock_nessus_parser.assert_called_once_with(self.mock_config_manager_instance)
    
    def test_get_mode(self):
        """Test mode selection logic."""
        # Test default mode
        mode = self.engine._get_mode()
        self.assertEqual(mode, 'internal')
        
        # Test different scope
        self.args.scope = 'external'
        mode = self.engine._get_mode()
        self.assertEqual(mode, 'external')
        
        # Test web scope
        self.args.scope = 'web'
        mode = self.engine._get_mode()
        self.assertEqual(mode, 'web')
    
    def test_client_specific_config(self):
        """Test loading client-specific configuration."""
        # Set up client-specific test
        self.args.client = 'test_client'
        self.mock_config_manager_instance.load_client_config.return_value = True
        
        # Create new engine instance with client
        with patch.object(NessusEngine, '_load_existing_flaws'):
            engine = NessusEngine(self.args)
        
        # Verify client config was loaded
        self.mock_config_manager_instance.load_client_config.assert_called_once_with('test_client')
        self.assertEqual(engine.client_name, 'test_client')
        self.mock_log.info.assert_any_call("Loaded client-specific configuration for test_client")
    
    @patch('os.path.exists')
    @patch.object(NessusEngine, '_load_existing_flaws')  # Patch internal methods to avoid execution
    @patch.object(NessusEngine, 'convert_nessus_to_plextrac')
    def test_run_successful(self, mock_convert, mock_load_flaws, mock_exists):
        """Test successful execution of the run method."""
        # Configure mocks
        self.mock_plextrac_api_instance.authenticate.return_value = (True, "test-token")
        mock_exists.return_value = True
        self.mock_plextrac_api_instance.upload_nessus_file.return_value = (True, {"flaws": []})
        
        # Run the engine
        self.engine.run()
        
        # Verify authentication was performed
        self.mock_plextrac_api_instance.authenticate.assert_called_once_with(
            username="testuser",
            password="testpassword"
        )
        
        # Verify convert method was called
        mock_convert.assert_called_once()
        
        # Verify upload was performed
        self.mock_plextrac_api_instance.upload_nessus_file.assert_called_once_with(
            "plextrac_format.csv"
        )
        
        # Verify no screenshot upload was attempted
        self.mock_plextrac_api_instance.upload_screenshot.assert_not_called()
        
        # Verify non-core fields were not updated
        self.mock_plextrac_api_instance.update_flaw.assert_not_called()
        
        # Verify sys.exit was not called
        self.mock_exit.assert_not_called()
    
    @patch('os.path.exists')
    @patch.object(NessusEngine, '_load_existing_flaws')
    @patch.object(NessusEngine, 'convert_nessus_to_plextrac')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_run_with_screenshots(self, mock_json_load, mock_file, mock_convert, mock_load_flaws, mock_exists):
        """Test run method with screenshot uploads."""
        # Configure mocks
        self.mock_plextrac_api_instance.authenticate.return_value = (True, "test-token")
        mock_exists.return_value = True
        self.mock_plextrac_api_instance.upload_nessus_file.return_value = (True, {"flaws": []})
        
        # Mock JSON data for processed findings
        mock_findings = {
            "flaws": {
                "123": {"id": "123", "title": "Test Flaw 1"},
                "456": {"id": "456", "title": "Test Flaw 2"}
            }
        }
        mock_json_load.return_value = mock_findings
        
        # Enable screenshots
        self.args.screenshots = True
        
        # Run the engine
        self.engine.run()
        
        # Verify screenshot upload was attempted
        self.mock_log.info.assert_any_call("Uploading screenshots for findings")
        mock_file.assert_called_with(self.engine.processed_findings_file, 'r')
        
        # Verify sys.exit was not called
        self.mock_exit.assert_not_called()
    
    @patch('os.path.exists')
    @patch.object(NessusEngine, '_load_existing_flaws')
    @patch.object(NessusEngine, 'convert_nessus_to_plextrac')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_run_with_non_core_fields(self, mock_json_load, mock_file, mock_convert, mock_load_flaws, mock_exists):
        """Test run method with non-core field updates."""
        # Configure mocks
        self.mock_plextrac_api_instance.authenticate.return_value = (True, "test-token")
        mock_exists.return_value = True
        self.mock_plextrac_api_instance.upload_nessus_file.return_value = (True, {"flaws": []})
        
        # Mock JSON data for processed findings
        mock_findings = {
            "flaws": {
                "123": {"id": "123", "title": "Test Flaw 1", "cwe": "CWE-22"},
                "456": {"id": "456", "title": "Test Flaw 2", "cwe": "CWE-89"}
            }
        }
        mock_json_load.return_value = mock_findings
        
        # Enable non-core updates
        self.args.non_core = True
        
        # Run the engine
        self.engine.run()
        
        # Verify non-core update was attempted - use the actual log message used in the code
        self.mock_log.info.assert_any_call("Updating non-core fields for uploaded findings")
        mock_file.assert_called_with(self.engine.processed_findings_file, 'r')
        
        # Verify sys.exit was not called
        self.mock_exit.assert_not_called()
    
    def test_authentication_failure(self):
        """Test handling of authentication failures."""
        # Configure authentication to fail
        self.mock_plextrac_api_instance.authenticate.return_value = (False, None)
        
        # Run the engine - this will call sys.exit(1)
        self.engine.run()
        
        # Verify error was logged and exit was called
        self.mock_log.error.assert_any_call("Failed to authenticate with Plextrac API")
        self.mock_exit.assert_called_once_with(1)
    
    @patch('os.path.exists')
    @patch.object(NessusEngine, '_load_existing_flaws')
    @patch.object(NessusEngine, 'convert_nessus_to_plextrac')
    def test_upload_failure(self, mock_convert, mock_load_flaws, mock_exists):
        """Test handling of upload failures."""
        # Configure mocks
        self.mock_plextrac_api_instance.authenticate.return_value = (True, "test-token")
        mock_exists.return_value = True
        self.mock_plextrac_api_instance.upload_nessus_file.return_value = (False, None)
        
        # Run the engine
        self.engine.run()
        
        # Verify error was logged
        self.mock_log.error.assert_any_call("Failed to upload findings to Plextrac")
        
        # Verify sys.exit was not called
        self.mock_exit.assert_not_called()
    
    @patch('json.dump')
    def test_save_processed_findings(self, mock_json_dump):
        """Test saving processed findings."""
        # Sample response data
        response_data = {
            "findings": {
                "123": {"id": "123", "title": "Test Flaw 1"},
                "456": {"id": "456", "title": "Test Flaw 2"}
            }
        }
        
        # Set up the mock open context
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            # Call the method directly
            self.engine._save_processed_findings(response_data)
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with("_processed_findings.json", "w")
        
        # Verify JSON was written
        mock_json_dump.assert_called_once()
    
    @patch('os.makedirs')
    @patch('os.rename')
    def test_cleanup(self, mock_rename, mock_makedirs):
        """Test cleanup functionality."""
        # Enable cleanup
        self.args.cleanup = True
        
        # Set file names
        self.engine.plextrac_format_file = "test_plextrac.csv"
        
        # Use a side_effect function for os.path.exists to return True for the file
        # but False for the _merged directory to trigger makedirs
        def exists_side_effect(path):
            if path == "test_plextrac.csv":
                return True
            elif path == "_merged":
                return False
            return False
        
        with patch('os.path.exists', side_effect=exists_side_effect):
            # Call the cleanup method directly
            self.engine.cleanup()
            
            # Verify makedirs was called for _merged directory
            mock_makedirs.assert_called_once_with("_merged")
            
            # Verify rename was called to move the file
            dest_path = os.path.join("_merged", "test_plextrac.csv")
            mock_rename.assert_called_once_with("test_plextrac.csv", dest_path)


if __name__ == "__main__":
    unittest.main() 