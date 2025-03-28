"""
Plextrac API client for authentication and interaction with the Plextrac API.
"""
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import json

from ...utils.http_client import HTTPClient
from ...utils.logger import log


class PlextracAPI:
    """
    Plextrac API client for authentication and interaction with the Plextrac API.
    """
    def __init__(self, instance: str, http_client: Optional[HTTPClient] = None):
        """
        Initialize the Plextrac API client.
        
        Args:
            instance (str): Plextrac instance name (e.g. 'dev', 'prod', etc.).
            http_client (HTTPClient, optional): HTTP client to use for API requests.
                If not provided, a new client will be created.
        """
        base_url = f'https://{instance}.kevlar.bulletproofsi.net/'
        
        self.http_client = http_client or HTTPClient(base_url=base_url, verify_ssl=False)
        
        if http_client:
            self.http_client.set_base_url(base_url)
        
        # Define API endpoints
        self.auth_endpoint = 'api/v1/authenticate'
        self.upload_findings_endpoint = 'api/v1/findings/import'
        
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate with the Plextrac API.
        
        Args:
            username (str): Username for authentication.
            password (str): Password for authentication.
            
        Returns:
            tuple: (success, token)
        """
        headers = {'Content-Type': 'application/json'}
        payload = {
            'username': username,
            'password': password
        }
        
        response = self.http_client.post(
            endpoint=self.auth_endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            
            if token:
                self.http_client.set_token(token)
                log.success("Successfully authenticated with Plextrac API")
                return True, token
            else:
                log.error("Authentication successful but no token received")
                return False, None
        else:
            log.error(f"Failed to authenticate with Plextrac API: {response.status_code} - {response.text}")
            return False, None
    
    def upload_nessus_file(self, file_path: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Upload a Nessus file to Plextrac.
        
        Args:
            file_path (str): Path to the Nessus file to upload.
            
        Returns:
            tuple: (success, response_data)
        """
        try:
            if not self.http_client.access_token:
                log.error("Authentication token not set. Please authenticate first.")
                return False, None
            
            with open(file_path, 'rb') as f:
                files = [('file', ('file', f, 'application/octet-stream'))]
                
                response = self.http_client.post(
                    endpoint=self.upload_findings_endpoint,
                    files=files
                )
        except FileNotFoundError:
            log.error(f"File {file_path} not found.")
            return False, None
        except IOError as e:
            log.error(f"Failed to read {file_path}: {str(e)}")
            return False, None
            
        if response.status_code == 200:
            log.success("Nessus file successfully uploaded!")
            try:
                return True, response.json()
            except json.JSONDecodeError:
                return True, {"message": "File uploaded successfully"}
        else:
            log.error(f"Failed to upload Nessus file. Server responded with status code: {response.status_code}")
            log.error(response.text)
            return False, None
    
    def upload_screenshot(self, flaw_id: str, screenshot_path: str) -> bool:
        """
        Upload a screenshot for a specific flaw.
        
        Args:
            flaw_id (str): ID of the flaw.
            screenshot_path (str): Path to the screenshot file.
            
        Returns:
            bool: Success status.
        """
        endpoint = f'api/v1/finding/{flaw_id}/attachment'
        
        try:
            if not os.path.exists(screenshot_path):
                log.error(f"Screenshot file not found: {screenshot_path}")
                return False
            
            with open(screenshot_path, 'rb') as f:
                files = [('file', (os.path.basename(screenshot_path), f, 'image/png'))]
                
                response = self.http_client.post(
                    endpoint=endpoint,
                    files=files
                )
        except Exception as e:
            log.error(f"Failed to upload screenshot: {str(e)}")
            return False
        
        if response.status_code == 200:
            log.success(f"Screenshot successfully uploaded for flaw ID: {flaw_id}")
            return True
        else:
            log.error(f"Failed to upload screenshot for flaw ID: {flaw_id}. Server responded with status code: {response.status_code}")
            log.error(response.text)
            return False
    
    def get_flaws(self, client_id: str = None, report_id: str = None) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
        """
        Get a list of flaws from Plextrac.
        
        Args:
            client_id (str, optional): Client ID to filter flaws.
            report_id (str, optional): Report ID to filter flaws.
            
        Returns:
            tuple: (success, flaws)
        """
        endpoint = 'api/v1/findings'
        params = {}
        
        if client_id:
            params['client_id'] = client_id
        
        if report_id:
            params['report_id'] = report_id
        
        response = self.http_client.get(
            endpoint=endpoint,
            params=params
        )
        
        if response.status_code == 200:
            try:
                flaws = response.json()
                return True, flaws
            except json.JSONDecodeError:
                log.error("Failed to parse flaws response as JSON")
                return False, None
        else:
            log.error(f"Failed to get flaws. Server responded with status code: {response.status_code}")
            log.error(response.text)
            return False, None
    
    def update_flaw_description(self, flaw_id: str, description: str) -> bool:
        """
        Update the description of a flaw.
        
        Args:
            flaw_id (str): ID of the flaw.
            description (str): New description.
            
        Returns:
            bool: Success status.
        """
        endpoint = f'api/v1/finding/{flaw_id}'
        
        response = self.http_client.get(endpoint)
        
        if response.status_code != 200:
            log.error(f"Failed to get flaw {flaw_id} for updating. Server responded with status code: {response.status_code}")
            return False
        
        try:
            flaw_data = response.json()
            flaw_data['description'] = description
            
            update_response = self.http_client.put(
                endpoint=endpoint,
                json=flaw_data
            )
            
            if update_response.status_code == 200:
                log.success(f"Successfully updated description for flaw ID: {flaw_id}")
                return True
            else:
                log.error(f"Failed to update description for flaw ID: {flaw_id}. Server responded with status code: {update_response.status_code}")
                log.error(update_response.text)
                return False
                
        except json.JSONDecodeError:
            log.error(f"Failed to parse flaw data as JSON for flaw ID: {flaw_id}")
            return False
    
    def update_flaw_fields(self, flaw_id: str, fields: Dict[str, Any]) -> bool:
        """
        Update fields of a flaw.
        
        Args:
            flaw_id (str): ID of the flaw.
            fields (dict): Fields to update.
            
        Returns:
            bool: Success status.
        """
        endpoint = f'api/v1/finding/{flaw_id}'
        
        response = self.http_client.get(endpoint)
        
        if response.status_code != 200:
            log.error(f"Failed to get flaw {flaw_id} for updating. Server responded with status code: {response.status_code}")
            return False
        
        try:
            flaw_data = response.json()
            
            # Update flaw data with provided fields
            for key, value in fields.items():
                flaw_data[key] = value
            
            update_response = self.http_client.put(
                endpoint=endpoint,
                json=flaw_data
            )
            
            if update_response.status_code == 200:
                log.success(f"Successfully updated fields for flaw ID: {flaw_id}")
                return True
            else:
                log.error(f"Failed to update fields for flaw ID: {flaw_id}. Server responded with status code: {update_response.status_code}")
                log.error(update_response.text)
                return False
                
        except json.JSONDecodeError:
            log.error(f"Failed to parse flaw data as JSON for flaw ID: {flaw_id}")
            return False
    
    def update_non_core_fields(self, flaw_id: str, non_core_data: Dict[str, Any]) -> bool:
        """
        Update non-core fields for a finding in Plextrac.
        
        Args:
            flaw_id (str): ID of the flaw to update.
            non_core_data (Dict[str, Any]): Dictionary of non-core field data to update.
            
        Returns:
            bool: Success status of the update.
        """
        if not self.http_client.access_token:
            log.error("Authentication token not set. Please authenticate first.")
            return False
        
        endpoint = f'api/v1/findings/{flaw_id}/non-core'
        
        response = self.http_client.put(
            endpoint=endpoint,
            json=non_core_data
        )
        
        if response.status_code in [200, 201, 204]:
            log.success(f"Successfully updated non-core fields for flaw {flaw_id}")
            return True
        else:
            log.error(f"Failed to update non-core fields for flaw {flaw_id}")
            log.error(f"Server responded with status code: {response.status_code}")
            log.error(response.text)
            return False 