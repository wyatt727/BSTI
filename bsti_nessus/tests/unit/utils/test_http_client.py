"""
Unit tests for the HTTP client module.
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
import requests
import pytest
from requests.exceptions import RequestException, Timeout, ConnectionError

from bsti_nessus.utils.http_client import HTTPClient


class TestHTTPClient(unittest.TestCase):
    """Tests for the HTTPClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = HTTPClient(
            base_url="https://api.example.com",
            timeout=5,
            max_retries=2,
            retry_delay=0.1,  # Use small delay for faster tests
            verify_ssl=False
        )

    def test_initialization(self):
        """Test client initialization with parameters."""
        self.assertEqual(self.client.base_url, "https://api.example.com")
        self.assertEqual(self.client.timeout, 5)
        self.assertEqual(self.client.max_retries, 2)
        self.assertEqual(self.client.retry_delay, 0.1)
        self.assertEqual(self.client.verify_ssl, False)
        self.assertEqual(self.client.default_headers, {})
        self.assertIsNone(self.client.access_token)

    def test_set_base_url(self):
        """Test setting the base URL."""
        self.client.set_base_url("https://new-api.example.com")
        self.assertEqual(self.client.base_url, "https://new-api.example.com")

    def test_set_token(self):
        """Test setting the access token."""
        self.client.set_token("test-token")
        self.assertEqual(self.client.access_token, "test-token")
        self.assertEqual(self.client.default_headers["Authorization"], "Bearer test-token")

    def test_set_headers(self):
        """Test setting default headers."""
        headers = {"Content-Type": "application/json", "User-Agent": "Test-Client"}
        self.client.set_headers(headers)
        self.assertEqual(self.client.default_headers, headers)

    def test_build_url_with_relative_endpoint(self):
        """Test building URL with a relative endpoint."""
        url = self.client._build_url("users")
        self.assertEqual(url, "https://api.example.com/users")

    def test_build_url_with_slash_in_base_and_endpoint(self):
        """Test building URL when both base URL and endpoint have slashes."""
        self.client.set_base_url("https://api.example.com/")
        url = self.client._build_url("/users")
        self.assertEqual(url, "https://api.example.com/users")

    def test_build_url_with_absolute_endpoint(self):
        """Test building URL with an absolute endpoint."""
        url = self.client._build_url("https://other-api.example.com/users")
        self.assertEqual(url, "https://other-api.example.com/users")

    @patch("requests.Session.request")
    def test_get_request(self, mock_request):
        """Test making a GET request."""
        # Configure the mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "test"}'
        mock_request.return_value = mock_response

        # Make the request
        response = self.client.get("users", 
                                    headers={"Custom": "Header"}, 
                                    params={"page": 1})
        
        # Verify the mock was called with expected arguments
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/users",
            headers={"Custom": "Header"},
            params={"page": 1},
            data=None,
            json=None,
            files=None,
            timeout=5,
            verify=False
        )
        
        # Verify we got the expected response
        self.assertEqual(response, mock_response)

    @patch("requests.Session.request")
    def test_post_request(self, mock_request):
        """Test making a POST request."""
        # Configure the mock
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 1}'
        mock_request.return_value = mock_response

        # Make the request
        response = self.client.post(
            "users",
            headers={"Content-Type": "application/json"},
            json={"name": "Test User"}
        )
        
        # Verify the mock was called with expected arguments
        mock_request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            params=None,
            data=None,
            json={"name": "Test User"},
            files=None,
            timeout=5,
            verify=False
        )
        
        # Verify we got the expected response
        self.assertEqual(response, mock_response)

    @patch("requests.Session.request")
    def test_put_request(self, mock_request):
        """Test making a PUT request."""
        # Configure the mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 1, "name": "Updated User"}'
        mock_request.return_value = mock_response

        # Make the request
        response = self.client.put(
            "users/1",
            json={"name": "Updated User"}
        )
        
        # Verify the mock was called with expected arguments
        mock_request.assert_called_once_with(
            method="PUT",
            url="https://api.example.com/users/1",
            headers={},
            params=None,
            data=None,
            json={"name": "Updated User"},
            files=None,
            timeout=5,
            verify=False
        )
        
        # Verify we got the expected response
        self.assertEqual(response, mock_response)

    @patch("requests.Session.request")
    def test_delete_request(self, mock_request):
        """Test making a DELETE request."""
        # Configure the mock
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.text = ''
        mock_request.return_value = mock_response

        # Make the request
        response = self.client.delete("users/1")
        
        # Verify the mock was called with expected arguments
        mock_request.assert_called_once_with(
            method="DELETE",
            url="https://api.example.com/users/1",
            headers={},
            params=None,
            data=None,
            json=None,
            files=None,
            timeout=5,
            verify=False
        )
        
        # Verify we got the expected response
        self.assertEqual(response, mock_response)

    @patch("requests.Session.request")
    def test_retry_on_request_exception(self, mock_request):
        """Test retry logic on RequestException."""
        # Configure the mock to raise an exception on first call, then return a response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.side_effect = [
            RequestException("Connection failed"),
            mock_response
        ]

        # Make the request
        response = self.client.get("users")
        
        # Verify the mock was called twice
        self.assertEqual(mock_request.call_count, 2)
        
        # Verify we got the expected response
        self.assertEqual(response, mock_response)

    @patch("requests.Session.request")
    def test_max_retries_exceeded(self, mock_request):
        """Test behavior when max retries are exceeded."""
        # Configure the mock to always raise an exception
        mock_request.side_effect = ConnectionError("Connection failed")

        # Make the request
        response = self.client.get("users")
        
        # Verify the mock was called the expected number of times (initial + 2 retries)
        self.assertEqual(mock_request.call_count, 3)
        
        # Verify we got a 500 response
        self.assertEqual(response.status_code, 500)
        self.assertIn("Connection failed", response._content.decode('utf-8'))

    @patch("requests.Session.request")
    def test_authentication_header(self, mock_request):
        """Test that authentication header is included when token is set."""
        # Configure the mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Set token and make request
        self.client.set_token("test-token")
        self.client.get("users")
        
        # Verify the auth header was included
        kwargs = mock_request.call_args[1]
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-token")

    @patch("requests.Session.request")
    def test_handle_non_2xx_response(self, mock_request):
        """Test handling of non-2xx responses."""
        # Configure the mock
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "Not found"}'
        mock_request.return_value = mock_response

        # Make the request
        response = self.client.get("users/999")
        
        # Verify we got the error response
        self.assertEqual(response.status_code, 404)
        
        # Verify we only tried once (no retries for 4xx status codes)
        self.assertEqual(mock_request.call_count, 1)

    @patch("requests.Session.request")
    def test_timeout_handling(self, mock_request):
        """Test handling of request timeouts."""
        # Configure the mock to raise a timeout
        mock_request.side_effect = Timeout("Request timed out")

        # Make the request
        response = self.client.get("slow-endpoint")
        
        # Verify we got a 500 response after all retries
        self.assertEqual(response.status_code, 500)
        self.assertIn("timed out", response._content.decode('utf-8'))
        
        # Verify we tried the expected number of times
        self.assertEqual(mock_request.call_count, 3)  # initial + 2 retries

if __name__ == "__main__":
    unittest.main() 