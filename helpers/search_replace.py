from typing import Any, Dict, List, Union
from helpers.custom_logger import log
from helpers.flaw_lister import FlawLister


class SearchReplacer:

    def __init__(self, url_manager: Any, request_handler: Any, args: Any):
        """
        Initialize the SearchReplacer class with a URL manager, request handler, and additional arguments.

        :param url_manager: Object responsible for managing URLs.
        :param request_handler: Object responsible for handling HTTP requests.
        :param args: Additional command-line arguments or other configurations.
        """
        self.url_manager = url_manager
        self.request_handler = request_handler
        self.args = args
        self.flaw_lister = FlawLister(self.url_manager, self.request_handler)

    def build_payload(self, flaw: Dict[str, Any], software_name: str) -> Dict[str, Any]:
        """
        Build the payload for updating the flaw with the software name.

        :param flaw: The flaw data to be updated.
        :param software_name: The software name to replace in the placeholders.
        :return: The payload for the update request.
        """
        return {
            "description": flaw["description"].replace("{{software_name}}", software_name),
            "recommendations": flaw["recommendations"].replace("{{software_name}}", software_name),
        }

    
    def get_flaw_ids(self) -> List[int]:
        """
        Get a list of flaw IDs from the FlawLister.
        :return: List of flaw IDs.
        """
        flaws = self.flaw_lister.list_flaws()
        return [flaw['flaw_id'] for flaw in flaws]
        

    def replace_engine(self):
        """
        Replace placeholders in flaws and update them via the API.
        """
        flaw_ids = self.get_flaw_ids()
        for flaw_id in flaw_ids:
            flaw = self.flaw_lister.get_flaw_by_id(flaw_id)
            if flaw:
                title = flaw.get("title", "")
                software_name = title.split(" - ")[0] if " - " in title else title
                
                url = self.url_manager.get_update_finding_url(flaw_id)
                payload = self.build_payload(flaw, software_name)
                
                response = self.request_handler.put(url, json=payload)
                
                if response.status_code == 200:
                    log.info(f"Successfully updated flaw {flaw_id}")
                else:
                    log.error(f"Failed to update flaw {flaw_id}: {response.text}")