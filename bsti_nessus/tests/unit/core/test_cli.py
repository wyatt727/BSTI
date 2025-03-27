"""
Unit tests for the CLI module.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import io
from argparse import Namespace
import tempfile
import pytest

from bsti_nessus.core.cli import parse_arguments, validate_arguments, print_banner, run_config_wizard, main
from bsti_nessus.utils.logger import log


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestCLI(unittest.TestCase):
    """Tests for the CLI module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample temporary directory for testing
        self.test_dir = "/tmp/test_dir"
        self.screenshot_dir = "/tmp/test_screenshots"
        
        # Mock os.path.isdir to return True for our test directories
        self.orig_isdir = os.path.isdir
        def mock_isdir(path):
            if path in [self.test_dir, self.screenshot_dir]:
                return True
            return self.orig_isdir(path)
        
        self.isdir_patcher = patch('os.path.isdir', side_effect=mock_isdir)
        self.isdir_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.isdir_patcher.stop()
    
    @patch('sys.argv', ['bsti_nessus', '-u', 'testuser', '-p', 'testpass', 
                        '-d', '/tmp/test_dir', '-t', 'dev'])
    def test_parse_arguments_required_only(self):
        """Test parsing with only required arguments."""
        args = parse_arguments()
        
        self.assertEqual(args.username, 'testuser')
        self.assertEqual(args.password, 'testpass')
        self.assertEqual(args.directory, '/tmp/test_dir')
        self.assertEqual(args.target_plextrac, 'dev')
        self.assertEqual(args.scope, 'internal')  # Default value
        self.assertFalse(args.screenshots)  # Default False
        self.assertFalse(args.cleanup)  # Default False
        self.assertEqual(args.verbosity, 1)  # Default value
    
    @patch('sys.argv', ['bsti_nessus', '-u', 'testuser', '-p', 'testpass', 
                        '-d', '/tmp/test_dir', '-t', 'prod', 
                        '-s', 'external', '--screenshots', '--cleanup',
                        '--screenshot-dir', '/tmp/test_screenshots',
                        '--client', 'Test Client', '--report', 'Test Report',
                        '--non-core', '-v', '2'])
    def test_parse_arguments_all_options(self):
        """Test parsing with all optional arguments."""
        args = parse_arguments()
        
        self.assertEqual(args.username, 'testuser')
        self.assertEqual(args.password, 'testpass')
        self.assertEqual(args.directory, '/tmp/test_dir')
        self.assertEqual(args.target_plextrac, 'prod')
        self.assertEqual(args.scope, 'external')
        self.assertEqual(args.screenshot_dir, '/tmp/test_screenshots')
        self.assertEqual(args.client, 'Test Client')
        self.assertEqual(args.report, 'Test Report')
        self.assertTrue(args.screenshots)
        self.assertTrue(args.cleanup)
        self.assertTrue(args.non_core)
        self.assertEqual(args.verbosity, 2)
    
    @patch('sys.argv', ['bsti_nessus', '-u', 'testuser', '-p', 'testpass', 
                        '-d', '/tmp/test_dir', '-t', 'dev', '-s', 'mobile'])
    def test_parse_arguments_scope_choice(self):
        """Test parsing with a specific scope choice."""
        args = parse_arguments()
        self.assertEqual(args.scope, 'mobile')
    
    @patch('sys.argv', ['bsti_nessus', '-u', 'testuser', '-p', 'testpass', 
                        '-d', '/tmp/test_dir', '-t', 'dev', '-v', '0'])
    def test_parse_arguments_verbosity(self):
        """Test parsing with a specific verbosity level."""
        args = parse_arguments()
        self.assertEqual(args.verbosity, 0)
    
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.argv', ['bsti_nessus', '-u', 'testuser', '-p', 'testpass', 
                        '-d', '/tmp/test_dir', '-t', 'dev', '-s', 'invalid'])
    def test_parse_arguments_invalid_scope(self, mock_stderr):
        """Test parsing with an invalid scope value."""
        with self.assertRaises(SystemExit):
            parse_arguments()
        
        error_output = mock_stderr.getvalue()
        self.assertIn("error: argument -s/--scope", error_output)
        self.assertIn("invalid choice: 'invalid'", error_output)
    
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.argv', ['bsti_nessus', '-u', 'testuser', '-p', 'testpass'])
    def test_parse_arguments_missing_required(self, mock_stderr):
        """Test parsing with missing required arguments."""
        with self.assertRaises(SystemExit):
            parse_arguments()
        
        error_output = mock_stderr.getvalue()
        self.assertIn("error: the following arguments are required", error_output)
    
    def test_validate_arguments_valid(self):
        """Test argument validation with valid arguments."""
        args = Namespace()
        args.directory = self.test_dir
        args.screenshot_dir = self.screenshot_dir
        
        valid = validate_arguments(args)
        self.assertTrue(valid)
    
    @patch('bsti_nessus.core.cli.log')
    def test_validate_arguments_invalid_directory(self, mock_log):
        """Test argument validation with non-existent directory."""
        args = Namespace()
        args.directory = "/non/existent/directory"
        args.screenshot_dir = None
        
        valid = validate_arguments(args)
        self.assertFalse(valid)
        mock_log.error.assert_called_once()
    
    @patch('bsti_nessus.core.cli.log')
    def test_validate_arguments_invalid_screenshot_dir(self, mock_log):
        """Test argument validation with non-existent screenshot directory."""
        args = Namespace()
        args.directory = self.test_dir
        args.screenshot_dir = "/non/existent/screenshot/directory"
        
        valid = validate_arguments(args)
        self.assertFalse(valid)
        mock_log.error.assert_called_once()
    
    @patch('builtins.print')
    def test_print_banner(self, mock_print):
        """Test banner printing."""
        print_banner()
        
        # Verify that print was called at least 3 times (for banner, title, and separator)
        self.assertGreaterEqual(mock_print.call_count, 3)


class TestParseArguments:
    """Test the argument parser"""
    
    def test_config_wizard_only(self):
        """Test parsing with just config wizard flag"""
        test_args = ["--config-wizard"]
        with patch.object(sys, 'argv', ['bsti_nessus'] + test_args):
            args = parse_arguments()
            assert args.config_wizard is True
            assert args.username is None
            assert args.password is None
            
    def test_required_arguments_with_wizard(self):
        """Test that required arguments are optional with config wizard"""
        test_args = ["--config-wizard", "--verbosity", "2"]
        with patch.object(sys, 'argv', ['bsti_nessus'] + test_args):
            args = parse_arguments()
            assert args.config_wizard is True
            assert args.verbosity == 2
            
    def test_required_arguments_without_wizard(self):
        """Test that required arguments are enforced without config wizard"""
        test_args = ["-u", "testuser", "-p", "testpass", "-d", "/tmp", "-t", "dev"]
        with patch.object(sys, 'argv', ['bsti_nessus'] + test_args):
            args = parse_arguments()
            assert args.username == "testuser"
            assert args.password == "testpass"
            assert args.directory == "/tmp"
            assert args.target_plextrac == "dev"
            
    def test_missing_required_arguments(self):
        """Test that missing required arguments raise an error"""
        test_args = ["-u", "testuser"]  # Missing password, directory, target
        with patch.object(sys, 'argv', ['bsti_nessus'] + test_args):
            with pytest.raises(SystemExit):
                parse_arguments()
                
    def test_custom_config_path(self):
        """Test specifying a custom config path"""
        test_args = ["--config-wizard", "--config", "/custom/path/config.json"]
        with patch.object(sys, 'argv', ['bsti_nessus'] + test_args):
            args = parse_arguments()
            assert args.config == "/custom/path/config.json"


class TestValidateArguments:
    """Test argument validation"""
    
    def test_config_wizard_bypass_validation(self):
        """Test that config wizard bypasses other validations"""
        args = MagicMock()
        args.config_wizard = True
        args.directory = "nonexistent_dir"
        
        result = validate_arguments(args)
        assert result is True
        
    def test_invalid_directory(self, temp_dir):
        """Test validation with invalid directory"""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent")
        
        args = MagicMock()
        args.config_wizard = False
        args.directory = nonexistent_dir
        args.screenshot_dir = None
        
        with patch.object(log, 'error'):
            result = validate_arguments(args)
            assert result is False
        
    def test_valid_arguments(self, temp_dir):
        """Test validation with valid arguments"""
        args = MagicMock()
        args.config_wizard = False
        args.directory = temp_dir
        args.screenshot_dir = None
        
        result = validate_arguments(args)
        assert result is True
        
    def test_invalid_screenshot_dir(self, temp_dir):
        """Test validation with invalid screenshot directory"""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent")
        
        args = MagicMock()
        args.config_wizard = False
        args.directory = temp_dir
        args.screenshot_dir = nonexistent_dir
        
        with patch.object(log, 'error'):
            result = validate_arguments(args)
            assert result is False


class TestRunConfigWizard:
    """Test the configuration wizard runner"""
    
    @patch('bsti_nessus.core.cli.setup_logging')
    @patch('bsti_nessus.core.cli.ConfigWizard')
    @patch('bsti_nessus.core.cli.log')
    def test_run_config_wizard(self, mock_log, mock_wizard_class, mock_setup_logging):
        """Test running the configuration wizard"""
        # Set up mocks
        args = MagicMock()
        args.config = "test_config.json"
        args.verbosity = 2
        
        mock_wizard_instance = mock_wizard_class.return_value
        
        # Call the function
        run_config_wizard(args)
        
        # Verify
        mock_setup_logging.assert_called_once_with(2)
        mock_wizard_class.assert_called_once_with("test_config.json")
        mock_wizard_instance.run_wizard.assert_called_once()
        assert mock_log.info.call_count >= 2


class TestMainFunction:
    """Test the main function"""
    
    @patch('bsti_nessus.core.cli.parse_arguments')
    @patch('bsti_nessus.core.cli.setup_logging')
    @patch('bsti_nessus.core.cli.print_banner')
    @patch('bsti_nessus.core.cli.run_config_wizard')
    def test_main_with_config_wizard(self, mock_run_wizard, mock_print_banner, 
                                     mock_setup_logging, mock_parse_args):
        """Test main function with config wizard mode"""
        args = MagicMock()
        args.config_wizard = True
        args.verbosity = 1
        mock_parse_args.return_value = args
        
        main()
        
        mock_parse_args.assert_called_once()
        mock_setup_logging.assert_called_once_with(1)
        mock_print_banner.assert_called_once()
        mock_run_wizard.assert_called_once_with(args)
        
    @patch('bsti_nessus.core.cli.parse_arguments')
    @patch('bsti_nessus.core.cli.setup_logging')
    @patch('bsti_nessus.core.cli.print_banner')
    @patch('bsti_nessus.core.cli.validate_arguments')
    @patch('bsti_nessus.core.cli.NessusEngine')
    def test_main_with_normal_mode(self, mock_engine_class, mock_validate, 
                                  mock_print_banner, mock_setup_logging, mock_parse_args):
        """Test main function with normal conversion mode"""
        args = MagicMock()
        args.config_wizard = False
        args.verbosity = 1
        mock_parse_args.return_value = args
        mock_validate.return_value = True
        
        mock_engine_instance = mock_engine_class.return_value
        
        main()
        
        mock_parse_args.assert_called_once()
        mock_setup_logging.assert_called_once_with(1)
        mock_print_banner.assert_called_once()
        mock_validate.assert_called_once_with(args)
        mock_engine_class.assert_called_once_with(args)
        mock_engine_instance.run.assert_called_once()
        
    @patch('bsti_nessus.core.cli.parse_arguments')
    @patch('bsti_nessus.core.cli.setup_logging')
    @patch('bsti_nessus.core.cli.print_banner')
    @patch('bsti_nessus.core.cli.validate_arguments')
    @patch('bsti_nessus.core.cli.sys.exit')
    def test_main_with_invalid_arguments(self, mock_exit, mock_validate, mock_print_banner, 
                                        mock_setup_logging, mock_parse_args):
        """Test main function with invalid arguments"""
        args = MagicMock()
        args.config_wizard = False
        args.verbosity = 1
        mock_parse_args.return_value = args
        mock_validate.return_value = False
        
        main()
        
        mock_parse_args.assert_called_once()
        mock_setup_logging.assert_called_once_with(1)
        mock_print_banner.assert_called_once()
        mock_validate.assert_called_once_with(args)
        mock_exit.assert_called_once_with(1)
        
    @patch('bsti_nessus.core.cli.parse_arguments')
    @patch('bsti_nessus.core.cli.setup_logging')
    @patch('bsti_nessus.core.cli.log')
    @patch('bsti_nessus.core.cli.sys.exit')
    def test_main_with_keyboard_interrupt(self, mock_exit, mock_log, 
                                         mock_setup_logging, mock_parse_args):
        """Test main function with keyboard interrupt"""
        mock_parse_args.side_effect = KeyboardInterrupt()
        
        main()
        
        mock_log.warning.assert_called_once()
        mock_exit.assert_called_once_with(1)
        
    @patch('bsti_nessus.core.cli.parse_arguments')
    @patch('bsti_nessus.core.cli.setup_logging')
    @patch('bsti_nessus.core.cli.log')
    @patch('bsti_nessus.core.cli.traceback')
    @patch('bsti_nessus.core.cli.sys.exit')
    def test_main_with_unexpected_error(self, mock_exit, mock_traceback, 
                                       mock_log, mock_setup_logging, mock_parse_args):
        """Test main function with unexpected error"""
        mock_parse_args.side_effect = Exception("Test error")
        
        main()
        
        mock_log.error.assert_called()
        mock_traceback.format_exc.assert_called_once()
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main() 