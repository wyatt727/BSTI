import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from bsti_nessus.core.engine import MainEngine
from bsti_nessus.utils.config_manager import ConfigManager


@pytest.fixture
def mock_config():
    """Fixture for providing test configuration"""
    config = {
        "plextrac": {
            "instances": {
                "test": {
                    "url": "https://test-instance.plextrac.com",
                    "verify_ssl": False
                }
            }
        },
        "nessus": {
            "csv_format": {
                "required_fields": ["Plugin ID", "Name", "Risk", "Description"],
                "optional_fields": ["Solution", "See Also"]
            }
        }
    }
    return config


@pytest.fixture
def mock_http_client():
    """Fixture for mocking HTTP client responses"""
    with patch("bsti_nessus.integrations.plextrac.api.HttpClient") as mock_client:
        # Mock authentication response
        mock_auth_response = MagicMock()
        mock_auth_response.json.return_value = {"token": "fake-token"}
        mock_auth_response.status_code = 200

        # Mock upload response 
        mock_upload_response = MagicMock()
        mock_upload_response.json.return_value = {"id": "123", "status": "success"}
        mock_upload_response.status_code = 200

        # Configure the mock client
        mock_instance = mock_client.return_value
        mock_instance.post.side_effect = [mock_auth_response, mock_upload_response]
        mock_instance.get.return_value.status_code = 200
        mock_instance.get.return_value.json.return_value = {
            "clients": [{"id": "client1", "name": "Test Client"}]
        }

        yield mock_instance


@pytest.fixture
def sample_nessus_file():
    """Create a temporary sample Nessus CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
        temp_file.write("Plugin ID,Name,Risk,Description,Solution,See Also\n")
        temp_file.write("12345,Test Vulnerability,High,This is a test vulnerability description,Patch the system,https://example.com\n")
        temp_file.write("67890,Another Vulnerability,Medium,Another description,Update firmware,https://example.com/update\n")
        file_path = temp_file.name

    yield file_path
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.mark.integration
def test_nessus_conversion_workflow(mock_config, mock_http_client, sample_nessus_file):
    """Test the full Nessus to Plextrac conversion workflow"""
    with patch("bsti_nessus.utils.config_manager.ConfigManager.load") as mock_load:
        mock_load.return_value = mock_config
        config_manager = ConfigManager("test-config.json")
        
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("tempfile.mkdtemp", return_value=temp_dir):
                # Initialize the engine with our mocks
                engine = MainEngine(
                    username="test_user",
                    password="test_pass",
                    plextrac_instance="test",
                    config_manager=config_manager,
                    nessus_dir=os.path.dirname(sample_nessus_file),
                    verbose=True
                )
                
                # Run the conversion process
                with patch("glob.glob", return_value=[sample_nessus_file]):
                    with patch("bsti_nessus.integrations.nessus.parser.NessusParser.parse") as mock_parse:
                        mock_parse.return_value = {
                            "findings": [
                                {
                                    "plugin_id": "12345",
                                    "name": "Test Vulnerability",
                                    "risk": "High",
                                    "description": "This is a test vulnerability description",
                                    "solution": "Patch the system",
                                    "references": "https://example.com"
                                }
                            ]
                        }
                        
                        result = engine.run()
                        
                        # Assertions
                        assert result["status"] == "success"
                        assert mock_http_client.post.call_count >= 1  # Authentication call
                        
                        # Verify the parser was called
                        mock_parse.assert_called_once()


@pytest.mark.integration
def test_conversion_with_error_handling(mock_config, mock_http_client, sample_nessus_file):
    """Test error handling in the conversion workflow"""
    with patch("bsti_nessus.utils.config_manager.ConfigManager.load") as mock_load:
        mock_load.return_value = mock_config
        config_manager = ConfigManager("test-config.json")
        
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("tempfile.mkdtemp", return_value=temp_dir):
                # Initialize the engine with our mocks
                engine = MainEngine(
                    username="test_user",
                    password="test_pass",
                    plextrac_instance="test",
                    config_manager=config_manager,
                    nessus_dir=os.path.dirname(sample_nessus_file),
                    verbose=True
                )
                
                # Simulate an authentication error
                with patch.object(mock_http_client, "post") as mock_post:
                    mock_post.return_value.status_code = 401
                    mock_post.return_value.json.return_value = {"error": "Invalid credentials"}
                    
                    with patch("glob.glob", return_value=[sample_nessus_file]):
                        with pytest.raises(Exception) as exc_info:
                            engine.run()
                            
                        assert "Authentication failed" in str(exc_info.value) 