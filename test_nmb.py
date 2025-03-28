#!/usr/bin/env python3
# Test script for BSTI Nessus Management Buddy (NMB)
# This script validates the functionality of the enhanced NMB implementation

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# Add the parent directory to sys.path to import the nmb module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import modules from nmb.py to test
from nmb import (
    CredentialsCache,
    find_policy_file,
    read_burp_targets,
    read_credentials,
    determine_execution_mode,
    run_config_wizard,
    handle_mode,
    main,
    parse_arguments
)

class TestNMB(unittest.TestCase):
    """Test cases for the NMB implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.policy_dir = os.path.join(self.temp_dir, "Nessus-policy")
        os.makedirs(self.policy_dir, exist_ok=True)
        
        # Create mock policy files
        with open(os.path.join(self.policy_dir, "Default Good Model Nessus Vulnerability Policy.nessus"), "w") as f:
            f.write("<policy>test</policy>")
        
        with open(os.path.join(self.policy_dir, "Custom_Nessus_Policy-Pn_pAll_AllSSLTLS-Web-NoLocalCheck-NoDOS.nessus"), "w") as f:
            f.write("<policy>test</policy>")
        
        # Create mock targets files
        self.targets_file = os.path.join(self.temp_dir, "targets.txt")
        with open(self.targets_file, "w") as f:
            f.write("192.168.1.1\n192.168.1.2\n192.168.1.3\n")
        
        # Create mock credentials files
        self.username_file = os.path.join(self.temp_dir, "usernames.txt")
        self.password_file = os.path.join(self.temp_dir, "passwords.txt")
        with open(self.username_file, "w") as f:
            f.write("admin\nuser1\n")
        with open(self.password_file, "w") as f:
            f.write("password1\npassword2\n")
        
        # Store original directory to restore it after the test
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def test_credentials_cache(self):
        """Test the CredentialsCache class."""
        # Test initialization with username and password
        cache = CredentialsCache(username="user", password="pass")
        self.assertEqual(cache.get_creds(), ("user", "pass"))
        
        # Test initialization without credentials should trigger credential manager
        with patch('nmb.CredentialManager') as mock_cred_manager:
            mock_instance = Mock()
            mock_instance.get_credentials.return_value = ("stored_user", "stored_pass")
            mock_cred_manager.return_value = mock_instance
            
            # Create a new cache with the patch in place
            # This will call CredentialManager in __init__
            cache = CredentialsCache()
            
            # Verify CredentialManager was called with the correct service name
            mock_cred_manager.assert_called_with(service_name="bsti-nessus")
            mock_instance.get_credentials.assert_called_with("nessus-drone")
            self.assertEqual(cache.get_creds(), ("stored_user", "stored_pass"))
    
    def test_find_policy_file_core(self):
        """Test finding the core policy file."""
        policy_file = find_policy_file("core")
        self.assertTrue(policy_file.endswith("Default Good Model Nessus Vulnerability Policy.nessus"))
    
    def test_find_policy_file_nc(self):
        """Test finding the non-core policy file."""
        policy_file = find_policy_file("nc")
        self.assertTrue(policy_file.endswith("Custom_Nessus_Policy-Pn_pAll_AllSSLTLS-Web-NoLocalCheck-NoDOS.nessus"))
    
    @patch('builtins.input', return_value="/custom/path/policy.nessus")
    def test_find_policy_file_custom(self, mock_input):
        """Test finding a custom policy file."""
        policy_file = find_policy_file("custom")
        self.assertEqual(policy_file, os.path.normpath("/custom/path/policy.nessus"))
    
    def test_read_burp_targets(self):
        """Test reading targets from a file."""
        targets = read_burp_targets(self.targets_file)
        self.assertEqual(targets, ["192.168.1.1", "192.168.1.2", "192.168.1.3"])
    
    def test_read_credentials(self):
        """Test reading credentials from files."""
        usernames, passwords = read_credentials(self.username_file, self.password_file)
        self.assertEqual(usernames, ["admin", "user1"])
        self.assertEqual(passwords, ["password1", "password2"])
    
    def test_determine_execution_mode_local(self):
        """Test determining execution mode with local flag."""
        args = MagicMock()
        args.local = True
        
        mode = determine_execution_mode(args)
        self.assertTrue(mode)
    
    def test_determine_execution_mode_drone(self):
        """Test determining execution mode without local flag."""
        args = MagicMock()
        args.local = False
        
        mode = determine_execution_mode(args)
        self.assertFalse(mode)
    
    @patch('nmb.ConfigWizard')
    def test_run_config_wizard_success(self, mock_config_wizard):
        """Test running the configuration wizard successfully."""
        mock_instance = Mock()
        mock_instance.run_wizard.return_value = {
            "username": "wizard_user",
            "password": "wizard_pass",
            "drone": "wizard_drone"
        }
        mock_config_wizard.return_value = mock_instance
        
        args = MagicMock()
        args.username = None
        args.password = None
        args.drone = None
        
        creds_cache = MagicMock()
        creds_cache.store_creds.return_value = True
        
        result = run_config_wizard(args, creds_cache)
        
        mock_config_wizard.assert_called_once()
        mock_instance.run_wizard.assert_called_once()
        creds_cache.store_creds.assert_called_once_with("wizard_user", "wizard_pass")
        self.assertEqual(args.username, "wizard_user")
        self.assertEqual(args.password, "wizard_pass")
        self.assertEqual(args.drone, "wizard_drone")
        self.assertTrue(result)
    
    @patch('nmb.ConfigWizard')
    def test_run_config_wizard_canceled(self, mock_config_wizard):
        """Test running the configuration wizard when canceled."""
        mock_instance = Mock()
        mock_instance.run_wizard.return_value = None
        mock_config_wizard.return_value = mock_instance
        
        args = MagicMock()
        creds_cache = MagicMock()
        
        result = run_config_wizard(args, creds_cache)
        
        mock_config_wizard.assert_called_once()
        mock_instance.run_wizard.assert_called_once()
        creds_cache.store_creds.assert_not_called()
        self.assertFalse(result)
    
    @patch('nmb.ProgressTracker')
    def test_handle_mode(self, mock_progress_tracker):
        """Test handling a mode with progress tracking."""
        mock_instance = Mock()
        mock_progress_tracker.return_value = mock_instance
        
        args = MagicMock()
        mock_handler_class = MagicMock()
        mock_handler_class.__name__ = "MockHandlerClass"
        mock_handler_args_provider = lambda _: "arg1"
        
        handler_info = {
            "handler_class": mock_handler_class,
            "handler_args_providers": [mock_handler_args_provider]
        }
        
        with patch('nmb.log') as mock_log:
            handle_mode(args, "test_mode", ["arg_name"], handler_info)
        
        mock_progress_tracker.assert_called_once()
        mock_instance.start.assert_called_once()
        mock_instance.update.assert_called()
        mock_instance.finish.assert_called_once()
        mock_handler_class.assert_called_once_with("arg1")
    
    def test_parse_arguments(self):
        """Test parsing command line arguments."""
        with patch('sys.argv', ['nmb.py', '-m', 'deploy', '-d', 'test_drone', '-c', 'test_client', 
                              '-s', 'core', '-u', 'test_user', '-p', 'test_pass']):
            args = parse_arguments()
            
            self.assertEqual(args.mode, 'deploy')
            self.assertEqual(args.drone, 'test_drone')
            self.assertEqual(args.client, 'test_client')
            self.assertEqual(args.project_type, 'core')
            self.assertEqual(args.username, 'test_user')
            self.assertEqual(args.password, 'test_pass')
            self.assertFalse(args.config_wizard)
            self.assertFalse(args.parallel)

    @patch('nmb.run_config_wizard')
    @patch('nmb.handle_mode')
    def test_main_with_config_wizard(self, mock_handle_mode, mock_run_config_wizard):
        """Test main function with config wizard enabled."""
        with patch('nmb.parse_arguments') as mock_parse_args:
            args = MagicMock()
            args.config_wizard = True
            args.mode = 'deploy'
            args.username = 'test_user'
            args.password = 'test_pass'
            mock_parse_args.return_value = args
            
            # Simulate successful config wizard
            mock_run_config_wizard.return_value = True
            
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_not_called()
                
            mock_run_config_wizard.assert_called_once()
            mock_handle_mode.assert_called_once()
    
    @patch('nmb.run_config_wizard')
    @patch('nmb.handle_mode')
    def test_main_with_failed_config_wizard(self, mock_handle_mode, mock_run_config_wizard):
        """Test main function with failed config wizard."""
        # Define a custom exception to stop execution
        class TestExitException(Exception):
            pass
            
        with patch('nmb.parse_arguments') as mock_parse_args:
            args = MagicMock()
            args.config_wizard = True
            args.mode = 'deploy'
            mock_parse_args.return_value = args
            
            # Simulate failed config wizard
            mock_run_config_wizard.return_value = False
            
            # Make sys.exit raise our custom exception
            with patch('sys.exit', side_effect=TestExitException) as mock_exit:
                try:
                    main()
                except TestExitException:
                    # Expected to raise our custom exception
                    pass
                
                mock_exit.assert_called_once_with(1)
            
            mock_run_config_wizard.assert_called_once()
            # Since execution should stop at sys.exit, handle_mode should not be called
            mock_handle_mode.assert_not_called()


# Run the tests
if __name__ == '__main__':
    unittest.main() 