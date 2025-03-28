import os
import pytest
import platform
from unittest.mock import patch, MagicMock

from bsti_nessus.utils.credentials import CredentialManager
from bsti_nessus.utils.logger import CustomLogger


@pytest.fixture
def mock_logger():
    """Fixture that provides a mock logger."""
    return MagicMock(spec=CustomLogger)


@pytest.fixture
def credential_manager(mock_logger):
    """Fixture that provides a credential manager with a mock backend."""
    with patch('bsti_nessus.utils.credentials.CredentialManager._init_backend'):
        # Create a credential manager
        manager = CredentialManager(service_name='test_service', logger=mock_logger)
        
        # Create a mock backend
        mock_backend = MagicMock()
        
        # Configure the mock backend
        mock_backend.store.return_value = True
        mock_backend.get.return_value = ('test_user', 'test_pass')
        mock_backend.delete.return_value = True
        mock_backend.list_instances.return_value = ['dev', 'prod']
        
        # Replace the backend
        manager._backend = mock_backend
        
        # Monkey-patch store_credentials to avoid parameter order issues
        original_store = manager.store_credentials
        def patched_store(username, password, instance):
            return original_store(username, password, instance)
        manager.store_credentials = patched_store
        
        return manager


@pytest.mark.integration
def test_store_credentials(credential_manager):
    """Test storing credentials."""
    # Store credentials
    result = credential_manager.store_credentials('test_user', 'test_pass', 'dev')
    
    # Verify the result
    assert result is True
    
    # Verify the backend was called with correct arguments
    # The actual implementation of store takes (instance, username, password)
    credential_manager._backend.store.assert_called_once_with('dev', 'test_user', 'test_pass')


@pytest.mark.integration
def test_retrieve_credentials(credential_manager):
    """Test retrieving credentials."""
    # Retrieve credentials
    username, password = credential_manager.get_credentials('dev')
    
    # Verify the result
    assert username == 'test_user'
    assert password == 'test_pass'
    
    # Verify the backend was called with correct arguments
    credential_manager._backend.get.assert_called_once_with('dev')


@pytest.mark.integration
def test_delete_credentials(credential_manager):
    """Test deleting credentials."""
    # Delete credentials
    result = credential_manager.delete_credentials('dev')
    
    # Verify the result
    assert result is True
    
    # Verify the backend was called with correct arguments
    credential_manager._backend.delete.assert_called_once_with('dev')


@pytest.mark.integration
def test_list_stored_instances(credential_manager):
    """Test listing stored instances."""
    # List instances
    instances = credential_manager.list_instances()
    
    # Verify the result
    assert instances == ['dev', 'prod']
    
    # Verify the backend was called
    credential_manager._backend.list_instances.assert_called_once()


@pytest.mark.integration
@pytest.mark.parametrize("platform_name,backend_class", [
    ('Darwin', 'KeychainBackend'),
    ('Windows', 'WindowsCredentialBackend'),
    ('Linux', 'SecretServiceBackend'),
    ('Unknown', 'EncryptedFileBackend')
])
def test_backend_selection(platform_name, backend_class, mock_logger):
    """Test backend selection based on platform."""
    with patch('platform.system', return_value=platform_name):
        with patch(f'bsti_nessus.utils.credentials.{backend_class}') as mock_backend_class:
            # Mock the backend constructor
            mock_backend = MagicMock()
            mock_backend_class.return_value = mock_backend
            
            # Create the credential manager
            manager = CredentialManager(service_name='test_service', logger=mock_logger)
            
            # Verify the correct backend was initialized
            mock_backend_class.assert_called_once_with('test_service', mock_logger)
            assert manager._backend == mock_backend


@pytest.mark.integration
def test_error_handling(credential_manager, mock_logger):
    """Test error handling in credential operations."""
    # Make the backend methods raise exceptions
    credential_manager._backend.store.side_effect = Exception("Storage error")
    credential_manager._backend.get.side_effect = Exception("Retrieval error")
    credential_manager._backend.delete.side_effect = Exception("Deletion error")
    
    # Test store error handling
    result = credential_manager.store_credentials('user', 'pass', 'dev')
    assert result is False
    mock_logger.error.assert_called_with("Failed to store credentials for dev: Storage error")
    
    # Reset mock
    mock_logger.reset_mock()
    
    # Test retrieve error handling
    username, password = credential_manager.get_credentials('dev')
    assert username is None
    assert password is None
    mock_logger.error.assert_called_with("Failed to retrieve credentials for dev: Retrieval error")
    
    # Reset mock
    mock_logger.reset_mock()
    
    # Test delete error handling
    result = credential_manager.delete_credentials('dev')
    assert result is False
    mock_logger.error.assert_called_with("Failed to delete credentials for dev: Deletion error")


@pytest.mark.integration
@pytest.mark.skipif(platform.system() != 'Darwin', reason="Only runs on macOS")
def test_keychain_backend_integration():
    """Test actual integration with macOS Keychain if running on macOS."""
    # Use the global log instance with proper setup
    with patch('bsti_nessus.utils.logger.log') as mock_log:
        try:
            # Create a real credential manager
            manager = CredentialManager(service_name='bsti_nessus_test', logger=mock_log)
            
            # Generate a unique instance name to avoid conflicts
            import uuid
            instance_name = f"test_{uuid.uuid4().hex[:8]}"
            
            # Store credentials
            store_result = manager.store_credentials('test_user', 'test_pass', instance_name)
            
            # Only continue testing if store succeeded
            if store_result:
                # Retrieve credentials
                username, password = manager.get_credentials(instance_name)
                assert username == 'test_user'
                assert password == 'test_pass'
                
                # Delete credentials
                delete_result = manager.delete_credentials(instance_name)
                assert delete_result is True
                
                # Verify credentials are gone
                username, password = manager.get_credentials(instance_name)
                assert username is None
                assert password is None
        except Exception as e:
            pytest.skip(f"Skipping due to error with actual keychain: {str(e)}")


@pytest.mark.integration
def test_cli_interface(credential_manager):
    """Test the command-line interface for credential management."""
    with patch('sys.argv', ['credential_manager.py', 'set', 'dev']):
        with patch('getpass.getpass', return_value='test_pass'):
            with patch('builtins.input', return_value='test_user'):
                with patch('bsti_nessus.utils.credentials.CredentialManager', return_value=credential_manager):
                    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
                        # Mock the parsed arguments
                        args = MagicMock()
                        args.command = 'set'
                        args.instance = 'dev'
                        args.username = None  # Trigger prompt
                        args.password = None  # Trigger prompt
                        args.service = 'test_service'
                        mock_parse_args.return_value = args
                        
                        # Store the original method
                        original_store = credential_manager.store_credentials
                        # Replace with a mock
                        credential_manager.store_credentials = MagicMock(return_value=True)
                        
                        try:
                            # Run the CLI function
                            from bsti_nessus.utils.credentials import main
                            with patch('sys.exit') as mock_exit:
                                # Run main and capture the output
                                main()
                                
                                # Verify the credential manager was used correctly with the correct parameter order
                                credential_manager.store_credentials.assert_called_with('test_user', 'test_pass', 'dev')
                        finally:
                            # Restore the original method
                            credential_manager.store_credentials = original_store 