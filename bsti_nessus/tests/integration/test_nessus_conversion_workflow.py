import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from bsti_nessus.core.engine import NessusEngine
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
    with patch("bsti_nessus.utils.http_client.HTTPClient") as mock_client:
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
    with patch("bsti_nessus.utils.config_manager.ConfigManager.load_config"):
        with patch("bsti_nessus.integrations.plextrac.api.HTTPClient", return_value=mock_http_client):
            with patch("sys.exit") as mock_exit:  # Prevent actual system exit
                # Setup mock response for authentication
                auth_response = MagicMock()
                auth_response.status_code = 200
                auth_response.json.return_value = {"token": "fake-token"}
                mock_http_client.post.return_value = auth_response
                
                # Create mock args
                args = MagicMock()
                args.username = "test_user"
                args.password = "test_pass"
                args.target_plextrac = "test"
                args.directory = os.path.dirname(sample_nessus_file)
                args.scope = "internal"
                args.screenshots = False
                args.client = None
                
                # Create a temporary output directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    with patch("tempfile.mkdtemp", return_value=temp_dir):
                        # Initialize the engine with our mocks
                        with patch.object(ConfigManager, "get_plugin_categories", return_value={}):
                            with patch.object(ConfigManager, "get_plugin_details", return_value={}):
                                engine = NessusEngine(args)
                                
                                # Make the authentication succeed
                                with patch.object(engine.plextrac_api, "authenticate", return_value=(True, "fake-token")):
                                    # Run the conversion process
                                    with patch("glob.glob", return_value=[sample_nessus_file]):
                                        with patch("bsti_nessus.integrations.nessus.parser.NessusParser.process_directory"):
                                            with patch("bsti_nessus.integrations.nessus.parser.NessusParser.generate_plextrac_csv"):
                                                with patch.object(engine, "_load_existing_flaws"):
                                                    with patch.object(engine, "upload_nessus_file") as mock_upload:
                                                        mock_upload.return_value = {"status": "success"}
                                                        
                                                        # Run the engine
                                                        engine.run()
                                                        
                                                        # Assertions
                                                        mock_upload.assert_called_once()


@pytest.mark.integration
def test_conversion_with_error_handling(mock_config, mock_http_client, sample_nessus_file):
    """Test error handling in the conversion workflow"""
    with patch("bsti_nessus.utils.config_manager.ConfigManager.load_config"):
        with patch("bsti_nessus.integrations.plextrac.api.HTTPClient", return_value=mock_http_client):
            with patch("sys.exit") as mock_exit:  # Prevent actual system exit
                # Create mock args
                args = MagicMock()
                args.username = "test_user"
                args.password = "test_pass"
                args.target_plextrac = "test"
                args.directory = os.path.dirname(sample_nessus_file)
                args.scope = "internal"
                args.screenshots = False
                args.client = None
                
                # Initialize a mock engine and plextrac API for focused testing
                engine = MagicMock()
                engine.args = args
                engine.plextrac_api = MagicMock()
                engine.plextrac_api.authenticate.return_value = (False, None)
                
                # Extract the authenticate method from NessusEngine
                from bsti_nessus.core.engine import NessusEngine
                authenticate_method = NessusEngine.authenticate
                
                # Call the authenticate method directly with our mock engine
                with patch("bsti_nessus.core.engine.log"):
                    authenticate_method(engine)
                    
                    # Assert that sys.exit was called once with error code 1
                    mock_exit.assert_called_once_with(1) 