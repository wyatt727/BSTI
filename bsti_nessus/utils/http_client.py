"""
HTTP client for making API requests with retry logic and error handling.
"""
import requests
import time
from typing import Any, Dict, Optional, Union, Tuple
from requests.exceptions import RequestException

from .logger import log

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

class HTTPClient:
    """
    HTTP client for making API requests with retry logic and error handling.
    """
    def __init__(self, 
                 base_url: str = "", 
                 timeout: int = 30, 
                 max_retries: int = 3, 
                 retry_delay: int = 2,
                 verify_ssl: bool = False):
        """
        Initialize the HTTP client.
        
        Args:
            base_url (str, optional): Base URL for API requests.
            timeout (int, optional): Request timeout in seconds.
            max_retries (int, optional): Maximum number of retries for failed requests.
            retry_delay (int, optional): Delay between retries in seconds.
            verify_ssl (bool, optional): Whether to verify SSL certificates.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.default_headers: Dict[str, str] = {}
        self.access_token: Optional[str] = None
        
    def set_base_url(self, base_url: str):
        """Set the base URL for API requests."""
        self.base_url = base_url
    
    def set_token(self, token: str):
        """Set the access token for API requests."""
        self.access_token = token
        self.default_headers['Authorization'] = f'Bearer {token}'
    
    def set_headers(self, headers: Dict[str, str]):
        """Set default headers for API requests."""
        self.default_headers = headers
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build a full URL from an endpoint.
        
        Args:
            endpoint (str): API endpoint.
            
        Returns:
            str: Full URL.
        """
        # If endpoint already starts with http:// or https://, return it as is
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        
        # Ensure base_url ends with a slash and endpoint doesn't start with one
        base = self.base_url
        if not base.endswith('/'):
            base += '/'
        
        endpoint = endpoint.lstrip('/')
        
        return f"{base}{endpoint}"
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str,
                     headers: Optional[Dict[str, str]] = None,
                     params: Optional[Dict[str, Any]] = None,
                     data: Optional[Any] = None,
                     json: Optional[Dict[str, Any]] = None,
                     files: Optional[Any] = None) -> Tuple[requests.Response, bool]:
        """
        Make an HTTP request with retry logic.
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE).
            endpoint (str): API endpoint.
            headers (dict, optional): Request headers.
            params (dict, optional): Query parameters.
            data (any, optional): Request body as form data.
            json (dict, optional): Request body as JSON.
            files (any, optional): Files to upload.
            
        Returns:
            tuple: (Response object, bool indicating success)
        """
        url = self._build_url(endpoint)
        
        # Merge default headers with provided headers
        merged_headers = self.default_headers.copy()
        if headers:
            merged_headers.update(headers)
        
        # Add authorization header if access token is set
        if self.access_token and 'Authorization' not in merged_headers:
            merged_headers['Authorization'] = f'Bearer {self.access_token}'
        
        # Make the request with retries
        retries = 0
        while retries <= self.max_retries:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                # Log if not 2xx response
                if response.status_code < 200 or response.status_code >= 300:
                    log.warning(f"{method} request to {url} failed with status {response.status_code}: {response.text}")
                    
                    # If we get a 401, token might have expired
                    if response.status_code == 401 and self.access_token:
                        log.warning("Authentication failed, token might have expired")
                        # We'll let the caller handle reauthentication
                
                # Return response even if it's an error
                return response, response.status_code >= 200 and response.status_code < 300
                
            except RequestException as e:
                retries += 1
                if retries <= self.max_retries:
                    log.warning(f"Request to {url} failed, retrying ({retries}/{self.max_retries}): {str(e)}")
                    time.sleep(self.retry_delay)
                else:
                    log.error(f"Request to {url} failed after {self.max_retries} retries: {str(e)}")
                    # Create a dummy response object
                    response = requests.Response()
                    response.status_code = 500
                    response._content = str(e).encode('utf-8')
                    return response, False
    
    def get(self, 
            endpoint: str,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a GET request.
        
        Args:
            endpoint (str): API endpoint.
            headers (dict, optional): Request headers.
            params (dict, optional): Query parameters.
            
        Returns:
            Response object.
        """
        response, _ = self._make_request('GET', endpoint, headers, params)
        return response
    
    def post(self,
             endpoint: str,
             headers: Optional[Dict[str, str]] = None,
             params: Optional[Dict[str, Any]] = None,
             data: Optional[Any] = None,
             json: Optional[Dict[str, Any]] = None,
             files: Optional[Any] = None) -> requests.Response:
        """
        Make a POST request.
        
        Args:
            endpoint (str): API endpoint.
            headers (dict, optional): Request headers.
            params (dict, optional): Query parameters.
            data (any, optional): Request body as form data.
            json (dict, optional): Request body as JSON.
            files (any, optional): Files to upload.
            
        Returns:
            Response object.
        """
        response, _ = self._make_request('POST', endpoint, headers, params, data, json, files)
        return response
    
    def put(self,
            endpoint: str,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Any] = None,
            json: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a PUT request.
        
        Args:
            endpoint (str): API endpoint.
            headers (dict, optional): Request headers.
            params (dict, optional): Query parameters.
            data (any, optional): Request body as form data.
            json (dict, optional): Request body as JSON.
            
        Returns:
            Response object.
        """
        response, _ = self._make_request('PUT', endpoint, headers, params, data, json)
        return response
    
    def delete(self,
               endpoint: str,
               headers: Optional[Dict[str, str]] = None,
               params: Optional[Dict[str, Any]] = None,
               json: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a DELETE request.
        
        Args:
            endpoint (str): API endpoint.
            headers (dict, optional): Request headers.
            params (dict, optional): Query parameters.
            json (dict, optional): Request body as JSON.
            
        Returns:
            Response object.
        """
        response, _ = self._make_request('DELETE', endpoint, headers, params, json=json)
        return response 