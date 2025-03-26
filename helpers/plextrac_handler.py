from typing import Any, Optional
from helpers.custom_logger import log
class PlextracHandler:
    def __init__(self, access_token: str, request_handler: Any, url_manager: Any):
        """Initializes the PlextracHandler with a given access token."""
        self.access_token = access_token
        self.request_handler = request_handler
        self.url_manager = url_manager

    def authenticate(self) -> bool:
        """Authenticates using the given access token.
        
        :return: True if authenticated, False otherwise.
        """
        return bool(self.request_handler.access_token)

    def upload_nessus_file(self, merged_nessus_file_path: str) -> Optional[Any]:
        """Uploads a Nessus file to Plextrac.

        :param merged_nessus_file_path: Path to the Nessus file to upload.
        :return: Server response if upload is successful, None otherwise.
        """
        url = self.url_manager.get_upload_nessus_url()

        try:
            with open(merged_nessus_file_path, 'rb') as f:
                files = [('file', ('file', f, 'application/octet-stream'))]
                response = self.request_handler.post(url, files=files)
        except FileNotFoundError:
            log.error(f"File {merged_nessus_file_path} not found.")
            return None
        except IOError:
            log.error(f"Failed to read {merged_nessus_file_path}.")
            return None

        if response.status_code == 200:
            log.debug("Nessus file successfully uploaded!")
        else:
            log.error(f"Failed to upload Nessus file. Server responded with status code: {response.status_code}")
            log.error(response.text)
            return None

        return response