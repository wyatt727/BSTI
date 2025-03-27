"""
Unit tests for the credential manager
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from bsti_nessus.utils.credentials import (
    CredentialManager, 
    CredentialBackend, 
    FileBackend, 
    KeychainBackend,
    WindowsCredentialBackend,
    SecretServiceBackend
)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing"""
    return MagicMock()


@pytest.fixture
def mock_keyring():
    """Create a mock keyring for testing"""
    mock = MagicMock()
    mock.get_password.return_value = None  # Default return value
    return mock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestCredentialBackend:
    """Test the base credential backend class"""
    
    def test_abstract_methods(self, mock_logger):
        """Test that abstract methods raise NotImplementedError"""
        backend = CredentialBackend("test_service", mock_logger)
        
        with pytest.raises(NotImplementedError):
            backend.store("user", "pass", "instance")
            
        with pytest.raises(NotImplementedError):
            backend.get("instance")
            
        with pytest.raises(NotImplementedError):
            backend.delete("instance")
            
        with pytest.raises(NotImplementedError):
            backend.list_instances()


class TestKeychainBackend:
    """Test the keychain backend"""
    
    @patch("bsti_nessus.utils.credentials.KeychainBackend.keyring", new_callable=MagicMock)
    def test_store_credentials(self, mock_keyring, mock_logger):
        """Test storing credentials in keychain"""
        # Setup
        backend = KeychainBackend("test_service", mock_logger)
        backend.keyring = mock_keyring
        mock_keyring.get_password.return_value = "[]"
        
        # Execute
        result = backend.store("testuser", "testpass", "testinstance")
        
        # Verify
        assert result is True
        mock_keyring.set_password.assert_any_call("test_service", "testinstance:username", "testuser")
        mock_keyring.set_password.assert_any_call("test_service", "testinstance:password", "testpass")
        mock_keyring.set_password.assert_any_call("test_service", "instances", '["testinstance"]')
    
    @patch("bsti_nessus.utils.credentials.KeychainBackend.keyring", new_callable=MagicMock)
    def test_get_credentials(self, mock_keyring, mock_logger):
        """Test retrieving credentials from keychain"""
        # Setup
        backend = KeychainBackend("test_service", mock_logger)
        backend.keyring = mock_keyring
        mock_keyring.get_password.side_effect = lambda service, key: {
            "testinstance:username": "testuser",
            "testinstance:password": "testpass"
        }.get(key)
        
        # Execute
        username, password = backend.get("testinstance")
        
        # Verify
        assert username == "testuser"
        assert password == "testpass"
        mock_keyring.get_password.assert_any_call("test_service", "testinstance:username")
        mock_keyring.get_password.assert_any_call("test_service", "testinstance:password")
    
    @patch("bsti_nessus.utils.credentials.KeychainBackend.keyring", new_callable=MagicMock)
    def test_delete_credentials(self, mock_keyring, mock_logger):
        """Test deleting credentials from keychain"""
        # Setup
        backend = KeychainBackend("test_service", mock_logger)
        backend.keyring = mock_keyring
        mock_keyring.get_password.return_value = '["testinstance", "other"]'
        
        # Execute
        result = backend.delete("testinstance")
        
        # Verify
        assert result is True
        mock_keyring.delete_password.assert_any_call("test_service", "testinstance:username")
        mock_keyring.delete_password.assert_any_call("test_service", "testinstance:password")
        mock_keyring.set_password.assert_called_with("test_service", "instances", '["other"]')
    
    @patch("bsti_nessus.utils.credentials.KeychainBackend.keyring", new_callable=MagicMock)
    def test_list_instances(self, mock_keyring, mock_logger):
        """Test listing instances from keychain"""
        # Setup
        backend = KeychainBackend("test_service", mock_logger)
        backend.keyring = mock_keyring
        mock_keyring.get_password.return_value = '["instance1", "instance2"]'
        
        # Execute
        instances = backend.list_instances()
        
        # Verify
        assert instances == ["instance1", "instance2"]
        mock_keyring.get_password.assert_called_with("test_service", "instances")


class TestFileBackend:
    """Test the file-based backend"""
    
    @patch("bsti_nessus.utils.credentials.os.path.expanduser")
    def test_get_data_dir(self, mock_expanduser, mock_logger, temp_dir):
        """Test data directory resolution for different platforms"""
        mock_expanduser.side_effect = lambda p: p.replace("~", temp_dir)
        
        # Test macOS
        with patch("bsti_nessus.utils.credentials.platform.system", return_value="Darwin"):
            backend = FileBackend("test_service", mock_logger)
            assert backend.data_dir == os.path.join(temp_dir, "Library/Application Support/BSTI/Nessus")
        
        # Test Windows
        with patch("bsti_nessus.utils.credentials.platform.system", return_value="Windows"):
            with patch.dict("os.environ", {"APPDATA": temp_dir}):
                backend = FileBackend("test_service", mock_logger)
                assert backend.data_dir == os.path.join(temp_dir, "BSTI", "Nessus")
        
        # Test Linux
        with patch("bsti_nessus.utils.credentials.platform.system", return_value="Linux"):
            backend = FileBackend("test_service", mock_logger)
            assert backend.data_dir == os.path.join(temp_dir, ".config/bsti/nessus")
    
    @patch("bsti_nessus.utils.credentials.os.makedirs")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_data_dir")
    def test_ensure_data_dir(self, mock_get_data_dir, mock_makedirs, mock_logger):
        """Test data directory creation"""
        # Setup
        mock_get_data_dir.return_value = "/test/data/dir"
        
        # Execute
        backend = FileBackend("test_service", mock_logger)
        
        # Verify
        mock_makedirs.assert_called_once_with("/test/data/dir", exist_ok=True)
    
    @patch("bsti_nessus.utils.credentials.getpass.getpass")
    @patch("bsti_nessus.utils.credentials.os.path.exists")
    @patch("bsti_nessus.utils.credentials.open", new_callable=MagicMock)
    @patch("bsti_nessus.utils.credentials.FileBackend._ensure_data_dir")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_data_dir")
    def test_get_master_key_new(self, mock_get_data_dir, mock_ensure_dir, 
                               mock_open, mock_exists, mock_getpass, mock_logger):
        """Test getting master key for first-time setup"""
        # Setup
        mock_get_data_dir.return_value = "/test/data"
        mock_exists.return_value = False
        mock_getpass.side_effect = ["testpass", "testpass"]  # First-time setup prompts twice
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Execute
        backend = FileBackend("test_service", mock_logger)
        key = backend._get_master_key()
        
        # Verify
        assert key is not None
        mock_getpass.assert_any_call("Create a master password for credential encryption: ")
        mock_getpass.assert_any_call("Confirm master password: ")
        mock_file.write.assert_called_once()
    
    @patch("bsti_nessus.utils.credentials.getpass.getpass")
    @patch("bsti_nessus.utils.credentials.os.path.exists")
    @patch("bsti_nessus.utils.credentials.open", new_callable=MagicMock)
    @patch("bsti_nessus.utils.credentials.FileBackend._ensure_data_dir")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_data_dir")
    def test_get_master_key_existing(self, mock_get_data_dir, mock_ensure_dir, 
                                    mock_open, mock_exists, mock_getpass, mock_logger):
        """Test getting master key with existing salt file"""
        # Setup
        mock_get_data_dir.return_value = "/test/data"
        mock_exists.return_value = True
        mock_getpass.return_value = "testpass"  # Existing setup prompts once
        mock_file = MagicMock()
        mock_file.read.return_value = b"testsalt"
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Execute
        backend = FileBackend("test_service", mock_logger)
        key = backend._get_master_key()
        
        # Verify
        assert key is not None
        mock_getpass.assert_called_once_with("Enter master password for credential decryption: ")
        mock_file.read.assert_called_once()
    
    @patch("bsti_nessus.utils.credentials.FileBackend._load_credentials")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_master_key")
    @patch("bsti_nessus.utils.credentials.os.path.exists")
    @patch("bsti_nessus.utils.credentials.open", new_callable=MagicMock)
    @patch("bsti_nessus.utils.credentials.Fernet")
    @patch("bsti_nessus.utils.credentials.FileBackend._ensure_data_dir")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_data_dir")
    def test_store_credentials(self, mock_get_data_dir, mock_ensure_dir, mock_fernet, 
                             mock_open, mock_exists, mock_get_key, mock_load, mock_logger):
        """Test storing credentials in file"""
        # Setup
        mock_get_data_dir.return_value = "/test/data"
        mock_exists.return_value = True
        mock_get_key.return_value = b"testkey"
        mock_load.return_value = {"existing": {"username": "user", "password": "pass"}}
        mock_fernet_instance = MagicMock()
        mock_fernet.return_value = mock_fernet_instance
        mock_fernet_instance.encrypt.return_value = b"encrypted-data"
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Execute
        backend = FileBackend("test_service", mock_logger)
        result = backend.store("testuser", "testpass", "testinstance")
        
        # Verify
        assert result is True
        mock_get_key.assert_called_once()
        mock_fernet.assert_called_once_with(b"testkey")
        expected_data = {
            "existing": {"username": "user", "password": "pass"},
            "testinstance": {"username": "testuser", "password": "testpass"}
        }
        mock_fernet_instance.encrypt.assert_called_once()
        mock_file.write.assert_called_once_with(b"encrypted-data")
    
    @patch("bsti_nessus.utils.credentials.FileBackend._load_credentials")
    @patch("bsti_nessus.utils.credentials.os.path.exists")
    @patch("bsti_nessus.utils.credentials.FileBackend._ensure_data_dir")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_data_dir")
    def test_get_credentials(self, mock_get_data_dir, mock_ensure_dir, 
                           mock_exists, mock_load, mock_logger):
        """Test retrieving credentials from file"""
        # Setup
        mock_get_data_dir.return_value = "/test/data"
        mock_exists.return_value = True
        mock_load.return_value = {
            "testinstance": {"username": "testuser", "password": "testpass"}
        }
        
        # Execute
        backend = FileBackend("test_service", mock_logger)
        username, password = backend.get("testinstance")
        
        # Verify
        assert username == "testuser"
        assert password == "testpass"
        mock_load.assert_called_once()
    
    @patch("bsti_nessus.utils.credentials.FileBackend._load_credentials")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_master_key")
    @patch("bsti_nessus.utils.credentials.os.path.exists")
    @patch("bsti_nessus.utils.credentials.open", new_callable=MagicMock)
    @patch("bsti_nessus.utils.credentials.Fernet")
    @patch("bsti_nessus.utils.credentials.FileBackend._ensure_data_dir")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_data_dir")
    def test_delete_credentials(self, mock_get_data_dir, mock_ensure_dir, mock_fernet, 
                              mock_open, mock_exists, mock_get_key, mock_load, mock_logger):
        """Test deleting credentials from file"""
        # Setup
        mock_get_data_dir.return_value = "/test/data"
        mock_exists.return_value = True
        mock_get_key.return_value = b"testkey"
        mock_load.return_value = {
            "testinstance": {"username": "testuser", "password": "testpass"},
            "other": {"username": "user", "password": "pass"}
        }
        mock_fernet_instance = MagicMock()
        mock_fernet.return_value = mock_fernet_instance
        mock_fernet_instance.encrypt.return_value = b"encrypted-data"
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Execute
        backend = FileBackend("test_service", mock_logger)
        result = backend.delete("testinstance")
        
        # Verify
        assert result is True
        mock_get_key.assert_called_once()
        mock_fernet.assert_called_once_with(b"testkey")
        expected_data = {"other": {"username": "user", "password": "pass"}}
        mock_fernet_instance.encrypt.assert_called_once()
        mock_file.write.assert_called_once_with(b"encrypted-data")
    
    @patch("bsti_nessus.utils.credentials.FileBackend._load_credentials")
    @patch("bsti_nessus.utils.credentials.os.path.exists")
    @patch("bsti_nessus.utils.credentials.FileBackend._ensure_data_dir")
    @patch("bsti_nessus.utils.credentials.FileBackend._get_data_dir")
    def test_list_instances(self, mock_get_data_dir, mock_ensure_dir, 
                          mock_exists, mock_load, mock_logger):
        """Test listing instances from file"""
        # Setup
        mock_get_data_dir.return_value = "/test/data"
        mock_exists.return_value = True
        mock_load.return_value = {
            "instance1": {"username": "user1", "password": "pass1"},
            "instance2": {"username": "user2", "password": "pass2"}
        }
        
        # Execute
        backend = FileBackend("test_service", mock_logger)
        instances = backend.list_instances()
        
        # Verify
        assert set(instances) == {"instance1", "instance2"}
        mock_load.assert_called_once()


class TestCredentialManager:
    """Test the credential manager class"""
    
    @patch("bsti_nessus.utils.credentials.platform.system")
    def test_init_backend_macos(self, mock_system, mock_logger):
        """Test backend initialization on macOS"""
        # Setup
        mock_system.return_value = "Darwin"
        
        # Test with keyring available
        with patch.dict("sys.modules", {"keyring": MagicMock()}):
            with patch("bsti_nessus.utils.credentials.KeychainBackend") as mock_backend:
                # Execute
                manager = CredentialManager("test_service", mock_logger)
                
                # Verify
                mock_backend.assert_called_once_with("test_service", mock_logger)
                assert manager._backend == mock_backend.return_value
        
        # Test with keyring not available
        with patch.dict("sys.modules", {"keyring": None}):
            with patch("bsti_nessus.utils.credentials.KeychainBackend", side_effect=ImportError):
                with patch("bsti_nessus.utils.credentials.FileBackend") as mock_file_backend:
                    # Execute
                    manager = CredentialManager("test_service", mock_logger)
                    
                    # Verify
                    mock_file_backend.assert_called_once_with("test_service", mock_logger)
                    assert manager._backend == mock_file_backend.return_value
    
    @patch("bsti_nessus.utils.credentials.platform.system")
    def test_init_backend_windows(self, mock_system, mock_logger):
        """Test backend initialization on Windows"""
        # Setup
        mock_system.return_value = "Windows"
        
        # Test with keyring available
        with patch.dict("sys.modules", {"keyring": MagicMock()}):
            with patch("bsti_nessus.utils.credentials.WindowsCredentialBackend") as mock_backend:
                # Execute
                manager = CredentialManager("test_service", mock_logger)
                
                # Verify
                mock_backend.assert_called_once_with("test_service", mock_logger)
                assert manager._backend == mock_backend.return_value
        
        # Test with keyring not available
        with patch.dict("sys.modules", {"keyring": None}):
            with patch("bsti_nessus.utils.credentials.WindowsCredentialBackend", side_effect=ImportError):
                with patch("bsti_nessus.utils.credentials.FileBackend") as mock_file_backend:
                    # Execute
                    manager = CredentialManager("test_service", mock_logger)
                    
                    # Verify
                    mock_file_backend.assert_called_once_with("test_service", mock_logger)
                    assert manager._backend == mock_file_backend.return_value
    
    @patch("bsti_nessus.utils.credentials.platform.system")
    def test_init_backend_linux(self, mock_system, mock_logger):
        """Test backend initialization on Linux"""
        # Setup
        mock_system.return_value = "Linux"
        
        # Test with keyring available
        with patch.dict("sys.modules", {"keyring": MagicMock()}):
            with patch("bsti_nessus.utils.credentials.SecretServiceBackend") as mock_backend:
                # Execute
                manager = CredentialManager("test_service", mock_logger)
                
                # Verify
                mock_backend.assert_called_once_with("test_service", mock_logger)
                assert manager._backend == mock_backend.return_value
        
        # Test with keyring not available
        with patch.dict("sys.modules", {"keyring": None}):
            with patch("bsti_nessus.utils.credentials.SecretServiceBackend", side_effect=ImportError):
                with patch("bsti_nessus.utils.credentials.FileBackend") as mock_file_backend:
                    # Execute
                    manager = CredentialManager("test_service", mock_logger)
                    
                    # Verify
                    mock_file_backend.assert_called_once_with("test_service", mock_logger)
                    assert manager._backend == mock_file_backend.return_value
    
    def test_delegate_methods(self, mock_logger):
        """Test that methods delegate to the backend"""
        # Setup
        mock_backend = MagicMock()
        
        with patch("bsti_nessus.utils.credentials.CredentialManager._init_backend"):
            manager = CredentialManager("test_service", mock_logger)
            manager._backend = mock_backend
            
            # Test store_credentials
            mock_backend.store.return_value = True
            result = manager.store_credentials("user", "pass", "instance")
            assert result is True
            mock_backend.store.assert_called_once_with("user", "pass", "instance")
            
            # Test get_credentials
            mock_backend.get.return_value = ("user", "pass")
            username, password = manager.get_credentials("instance")
            assert username == "user"
            assert password == "pass"
            mock_backend.get.assert_called_once_with("instance")
            
            # Test delete_credentials
            mock_backend.delete.return_value = True
            result = manager.delete_credentials("instance")
            assert result is True
            mock_backend.delete.assert_called_once_with("instance")
            
            # Test list_instances
            mock_backend.list_instances.return_value = ["instance1", "instance2"]
            instances = manager.list_instances()
            assert instances == ["instance1", "instance2"]
            mock_backend.list_instances.assert_called_once() 