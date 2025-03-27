"""
Secure Credential Management for BSTI Nessus to Plextrac Converter

This module provides secure storage for credentials using platform-specific backends:
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service

For environments where these services aren't available, it falls back to an encrypted
file-based storage with a master password.
"""
import os
import sys
import base64
import json
import getpass
import platform
from typing import Optional, Dict, Any, Tuple, List
import logging
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from bsti_nessus.utils.logger import Logger


class CredentialManager:
    """Manages secure storage and retrieval of credentials"""
    
    def __init__(self, service_name: str = "bsti_nessus", logger: Optional[Logger] = None):
        """
        Initialize the credential manager
        
        Args:
            service_name: Name of the service (used as a namespace)
            logger: Optional logger instance
        """
        self.service_name = service_name
        self.logger = logger or Logger("credentials")
        self._backend = None
        self._init_backend()
    
    def _init_backend(self) -> None:
        """Initialize the appropriate backend for credential storage"""
        system = platform.system()
        
        # Try to import platform-specific backends
        if system == "Darwin":  # macOS
            try:
                import keyring
                self._backend = KeychainBackend(self.service_name, self.logger)
                self.logger.info("Using macOS Keychain for credential storage")
                return
            except ImportError:
                self.logger.warning("keyring package not available, falling back to file storage")
        
        elif system == "Windows":
            try:
                import keyring
                self._backend = WindowsCredentialBackend(self.service_name, self.logger)
                self.logger.info("Using Windows Credential Manager for credential storage")
                return
            except ImportError:
                self.logger.warning("keyring package not available, falling back to file storage")
        
        elif system == "Linux":
            try:
                import keyring
                self._backend = SecretServiceBackend(self.service_name, self.logger)
                self.logger.info("Using Linux Secret Service for credential storage")
                return
            except ImportError:
                self.logger.warning("keyring package not available, falling back to file storage")
        
        # Fall back to file-based storage
        self._backend = FileBackend(self.service_name, self.logger)
        self.logger.info("Using encrypted file-based credential storage")
    
    def store_credentials(self, username: str, password: str, instance: str) -> bool:
        """
        Store credentials for a Plextrac instance
        
        Args:
            username: Username for authentication
            password: Password for authentication
            instance: Plextrac instance identifier
            
        Returns:
            bool: True if credentials were stored successfully
        """
        return self._backend.store(username, password, instance)
    
    def get_credentials(self, instance: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve credentials for a Plextrac instance
        
        Args:
            instance: Plextrac instance identifier
            
        Returns:
            Tuple of (username, password) or (None, None) if not found
        """
        return self._backend.get(instance)
    
    def delete_credentials(self, instance: str) -> bool:
        """
        Delete credentials for a Plextrac instance
        
        Args:
            instance: Plextrac instance identifier
            
        Returns:
            bool: True if credentials were deleted successfully
        """
        return self._backend.delete(instance)
    
    def list_instances(self) -> List[str]:
        """
        List all Plextrac instances with stored credentials
        
        Returns:
            List of instance identifiers
        """
        return self._backend.list_instances()


class CredentialBackend:
    """Base class for credential storage backends"""
    
    def __init__(self, service_name: str, logger: Logger):
        """
        Initialize the credential backend
        
        Args:
            service_name: Name of the service (used as a namespace)
            logger: Logger instance
        """
        self.service_name = service_name
        self.logger = logger
    
    def store(self, username: str, password: str, instance: str) -> bool:
        """Store credentials"""
        raise NotImplementedError("Subclasses must implement store()")
    
    def get(self, instance: str) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve credentials"""
        raise NotImplementedError("Subclasses must implement get()")
    
    def delete(self, instance: str) -> bool:
        """Delete credentials"""
        raise NotImplementedError("Subclasses must implement delete()")
    
    def list_instances(self) -> List[str]:
        """List instances with credentials"""
        raise NotImplementedError("Subclasses must implement list_instances()")


class KeychainBackend(CredentialBackend):
    """Credential backend using macOS Keychain"""
    
    def __init__(self, service_name: str, logger: Logger):
        """Initialize the keychain backend"""
        super().__init__(service_name, logger)
        import keyring
        self.keyring = keyring
    
    def store(self, username: str, password: str, instance: str) -> bool:
        """Store credentials in macOS Keychain"""
        try:
            # Store username and password
            account_key = f"{instance}:username"
            password_key = f"{instance}:password"
            
            self.keyring.set_password(self.service_name, account_key, username)
            self.keyring.set_password(self.service_name, password_key, password)
            
            # Store the instance in a list of available instances
            instances = self.list_instances()
            if instance not in instances:
                instances.append(instance)
                self.keyring.set_password(self.service_name, "instances", json.dumps(instances))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store credentials: {str(e)}")
            return False
    
    def get(self, instance: str) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve credentials from macOS Keychain"""
        try:
            account_key = f"{instance}:username"
            password_key = f"{instance}:password"
            
            username = self.keyring.get_password(self.service_name, account_key)
            password = self.keyring.get_password(self.service_name, password_key)
            
            return username, password
        except Exception as e:
            self.logger.error(f"Failed to retrieve credentials: {str(e)}")
            return None, None
    
    def delete(self, instance: str) -> bool:
        """Delete credentials from macOS Keychain"""
        try:
            account_key = f"{instance}:username"
            password_key = f"{instance}:password"
            
            # Delete the username and password
            self.keyring.delete_password(self.service_name, account_key)
            self.keyring.delete_password(self.service_name, password_key)
            
            # Update the instances list
            instances = self.list_instances()
            if instance in instances:
                instances.remove(instance)
                self.keyring.set_password(self.service_name, "instances", json.dumps(instances))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete credentials: {str(e)}")
            return False
    
    def list_instances(self) -> List[str]:
        """List instances with credentials in macOS Keychain"""
        try:
            instances_json = self.keyring.get_password(self.service_name, "instances")
            if instances_json:
                return json.loads(instances_json)
            return []
        except Exception as e:
            self.logger.error(f"Failed to list instances: {str(e)}")
            return []


class WindowsCredentialBackend(KeychainBackend):
    """Credential backend using Windows Credential Manager"""
    
    def __init__(self, service_name: str, logger: Logger):
        """Initialize the Windows credential backend"""
        super().__init__(service_name, logger)


class SecretServiceBackend(KeychainBackend):
    """Credential backend using Linux Secret Service"""
    
    def __init__(self, service_name: str, logger: Logger):
        """Initialize the Secret Service backend"""
        super().__init__(service_name, logger)


class FileBackend(CredentialBackend):
    """Encrypted file-based credential storage backend"""
    
    def __init__(self, service_name: str, logger: Logger):
        """Initialize the file backend"""
        super().__init__(service_name, logger)
        self.data_dir = self._get_data_dir()
        self.credentials_file = os.path.join(self.data_dir, f"{service_name}_credentials.enc")
        self.salt_file = os.path.join(self.data_dir, f"{service_name}_salt")
        self._ensure_data_dir()
        self._master_key = None
    
    def _get_data_dir(self) -> str:
        """Get the appropriate data directory for the platform"""
        system = platform.system()
        if system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/BSTI/Nessus")
        elif system == "Windows":
            return os.path.join(os.environ.get("APPDATA", ""), "BSTI", "Nessus")
        else:  # Linux and others
            return os.path.expanduser("~/.config/bsti/nessus")
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _derive_key(self, master_password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive an encryption key from the master password
        
        Args:
            master_password: The master password
            salt: Optional salt (if not provided, a new one will be generated)
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return key, salt
    
    def _get_master_key(self) -> bytes:
        """
        Get the master encryption key, prompting for password if needed
        
        Returns:
            The encryption key
        """
        if self._master_key:
            return self._master_key
        
        # Check if salt exists
        if os.path.exists(self.salt_file):
            with open(self.salt_file, "rb") as f:
                salt = f.read()
        else:
            # First-time setup
            master_password = getpass.getpass("Create a master password for credential encryption: ")
            confirm_password = getpass.getpass("Confirm master password: ")
            
            if master_password != confirm_password:
                raise ValueError("Passwords do not match")
            
            key, salt = self._derive_key(master_password)
            
            # Store the salt
            with open(self.salt_file, "wb") as f:
                f.write(salt)
                
            self._master_key = key
            return key
        
        # Prompt for master password
        master_password = getpass.getpass("Enter master password for credential decryption: ")
        key, _ = self._derive_key(master_password, salt)
        self._master_key = key
        return key
    
    def store(self, username: str, password: str, instance: str) -> bool:
        """Store credentials in encrypted file"""
        try:
            # Load existing credentials if any
            credentials = {}
            if os.path.exists(self.credentials_file):
                existing_credentials = self._load_credentials()
                if existing_credentials:
                    credentials = existing_credentials
            
            # Add or update the instance credentials
            credentials[instance] = {
                "username": username,
                "password": password
            }
            
            # Encrypt and save
            key = self._get_master_key()
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
            
            with open(self.credentials_file, "wb") as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store credentials: {str(e)}")
            return False
    
    def get(self, instance: str) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve credentials from encrypted file"""
        try:
            if not os.path.exists(self.credentials_file):
                return None, None
            
            credentials = self._load_credentials()
            if not credentials or instance not in credentials:
                return None, None
            
            instance_creds = credentials[instance]
            return instance_creds.get("username"), instance_creds.get("password")
        except Exception as e:
            self.logger.error(f"Failed to retrieve credentials: {str(e)}")
            return None, None
    
    def delete(self, instance: str) -> bool:
        """Delete credentials from encrypted file"""
        try:
            if not os.path.exists(self.credentials_file):
                return True
            
            credentials = self._load_credentials()
            if not credentials or instance not in credentials:
                return True
            
            # Remove the instance and save
            del credentials[instance]
            
            # Encrypt and save
            key = self._get_master_key()
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
            
            with open(self.credentials_file, "wb") as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete credentials: {str(e)}")
            return False
    
    def list_instances(self) -> List[str]:
        """List instances with credentials in encrypted file"""
        try:
            if not os.path.exists(self.credentials_file):
                return []
            
            credentials = self._load_credentials()
            return list(credentials.keys()) if credentials else []
        except Exception as e:
            self.logger.error(f"Failed to list instances: {str(e)}")
            return []
    
    def _load_credentials(self) -> Dict[str, Dict[str, str]]:
        """
        Load credentials from encrypted file
        
        Returns:
            Dictionary of credentials or empty dict if there was an error
        """
        try:
            with open(self.credentials_file, "rb") as f:
                encrypted_data = f.read()
            
            key = self._get_master_key()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return json.loads(decrypted_data.decode())
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {str(e)}")
            return {}


def main():
    """Command-line interface for credential management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BSTI Nessus Credential Manager")
    parser.add_argument("--service", "-s", default="bsti_nessus", 
                       help="Service name for credential storage (default: bsti_nessus)")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Store credentials")
    set_parser.add_argument("instance", help="Plextrac instance identifier")
    set_parser.add_argument("--username", "-u", help="Username (if not provided, will prompt)")
    set_parser.add_argument("--password", "-p", help="Password (if not provided, will prompt)")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Retrieve credentials")
    get_parser.add_argument("instance", help="Plextrac instance identifier")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete credentials")
    delete_parser.add_argument("instance", help="Plextrac instance identifier")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List stored instances")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    logger = Logger("credentials", level="INFO")
    
    # Create credential manager
    cred_manager = CredentialManager(args.service, logger)
    
    if args.command == "set":
        username = args.username
        password = args.password
        
        if not username:
            username = input("Username: ")
        
        if not password:
            password = getpass.getpass("Password: ")
        
        if cred_manager.store_credentials(username, password, args.instance):
            print(f"Credentials for {args.instance} stored successfully")
        else:
            print(f"Failed to store credentials for {args.instance}")
            return 1
    
    elif args.command == "get":
        username, password = cred_manager.get_credentials(args.instance)
        
        if username and password:
            print(f"Username: {username}")
            print(f"Password: {'*' * len(password)}")
        else:
            print(f"No credentials found for {args.instance}")
            return 1
    
    elif args.command == "delete":
        if cred_manager.delete_credentials(args.instance):
            print(f"Credentials for {args.instance} deleted successfully")
        else:
            print(f"Failed to delete credentials for {args.instance}")
            return 1
    
    elif args.command == "list":
        instances = cred_manager.list_instances()
        
        if instances:
            print("Stored instances:")
            for instance in instances:
                print(f"  - {instance}")
        else:
            print("No stored instances found")
    
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 