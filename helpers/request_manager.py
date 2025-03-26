from typing import Any, Dict, Optional
import requests
class RequestHandler:
    def __init__(self, access_token: str):
        self.session = requests.Session()
        self.session.verify = False # Consider enabling SSL verification for production
        self.access_token = access_token
        self.headers: Dict[str, str] = {}

    def _set_headers(self, headers: Optional[Dict[str, str]] = None):
        self.headers.update(headers or {})
        self.headers['Authorization'] = self.access_token

    def _validate_response(self, response: requests.Response) -> requests.Response:
        if response is None:
            raise ValueError("Invalid response received.")
        if not hasattr(response, "status_code"):
            raise ValueError("Response does not have a status_code attribute.")
        if not hasattr(response, "content"):
            raise ValueError("Response does not have a content attribute.")
        return response

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        self._set_headers(headers)
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=300)
            return self._validate_response(response)
        except requests.Timeout:
            raise ValueError("The request timed out after 5 minutes.")
        except requests.RequestException as e:
            raise ValueError(f"An error occurred: {e}")

    def post(self, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None, proxies: Optional[Dict[str, str]] = None) -> requests.Response:
        self._set_headers(headers)
        if 'Content-Type' in self.headers and self.headers['Content-Type'] == 'application/json':
            del self.headers['Content-Type']
        try:
            response = self.session.post(url, headers=self.headers, data=data, json=json, files=files, proxies=proxies, timeout=300)
            return self._validate_response(response)
        except requests.Timeout:
            raise ValueError("The request timed out after 5 minutes.")
        except requests.RequestException as e:
            raise ValueError(f"An error occurred: {e}")

    def patch(self, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        self._set_headers(headers)
        try:
            response = self.session.patch(url, headers=self.headers, data=data, json=json, timeout=300)
            return self._validate_response(response)
        except requests.Timeout:
            raise ValueError("The request timed out after 5 minutes.")
        except requests.RequestException as e:
            raise ValueError(f"An error occurred: {e}")

    def put(self, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        self._set_headers(headers)
        try:
            response = self.session.put(url, headers=self.headers, data=data, json=json, timeout=300)
            return self._validate_response(response)
        except requests.Timeout:
            raise ValueError("The request timed out after 5 minutes.")
        except requests.RequestException as e:
            raise ValueError(f"An error occurred: {e}")
        
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        self._set_headers(headers)
        try:
            response = self.session.delete(url, headers=self.headers, timeout=300)
            return self._validate_response(response)
        except requests.Timeout:
            raise ValueError("The request timed out after 5 minutes.")
        except requests.RequestException as e:
            raise ValueError(f"An error occurred: {e}")