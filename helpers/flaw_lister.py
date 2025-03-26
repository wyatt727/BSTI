from typing import Any, Dict, List, Optional, Set
from functools import lru_cache
from helpers.custom_logger import log
class FlawLister:
    def __init__(self, url_manager: Any, request_handler: Any):
        self.url_manager = url_manager
        self.request_handler = request_handler

    @lru_cache(maxsize=128)
    def get_detailed_flaw(self, flaw_id: str) -> Optional[Dict[str, Any]]:
        detail_url = self.url_manager.get_update_finding_url(flaw_id)
        detail_response = self.request_handler.get(detail_url)
        if detail_response.status_code == 200:
            return detail_response.json()
        else:
            log.error(f'Failed to get detailed data for flaw ID: {flaw_id}')
            return None

    def get_existing_flaws(self):
        """Fetch and record all existing flaws to a file."""
        url = self.url_manager.get_flaws_url()
        log.debug(f"Fetching existing flaws from URL: {url}")
        response = self.request_handler.get(url)
        existing_flaws = []

        if response.status_code == 200:
            content = response.json()
            log.debug(f"Got response with content type: {type(content)}")
            
            if isinstance(content, list):
                log.debug(f"Found {len(content)} existing flaws in the response")
                
                with open('existing_flaws.txt', 'w') as f:
                    for i, item in enumerate(content):
                        if i < 5:  # Just log a few for debugging
                            log.debug(f"Existing flaw item {i}: {item}")
                            
                        flaw_id = str(item['data'][0])
                        f.write(f"{flaw_id}\n")
                        
                        detailed_flaw = self.get_detailed_flaw(flaw_id)
                        if detailed_flaw:
                            log.debug(f"Got detailed data for existing flaw ID: {flaw_id}")
                            # Only add to existing_flaws if we got data
                            existing_flaws.append(detailed_flaw)
                        else:
                            log.debug(f"Failed to get detailed data for existing flaw ID: {flaw_id}")
            else:
                log.error(f'No existing flaw data found - Content: {content}')
        else:
            log.error(f'Failed to list existing flaws. Status code: {response.status_code}, Response: {response.text}')
            
        log.debug(f"Returning {len(existing_flaws)} detailed existing flaws")
        return existing_flaws

    def list_flaws(self) -> List[Dict[str, Any]]:
        """
        List all new flaws by comparing against existing ones.
        """
        existing_ids = self._load_excluded_flaw_ids()
        log.debug(f"Loaded {len(existing_ids)} existing flaw IDs to exclude")
        
        url = self.url_manager.get_flaws_url()
        log.debug(f"Fetching flaws from URL: {url}")
        response = self.request_handler.get(url)
        detailed_flaws = []

        if response.status_code == 200:
            content = response.json()
            log.debug(f"Got response with content type: {type(content)}")
            
            if isinstance(content, list):
                log.debug(f"Found {len(content)} flaws in the response")
                for i, item in enumerate(content):
                    if i < 5:  # Just log a few for debugging
                        log.debug(f"Flaw item {i}: {item}")
                    
                    flaw_id = str(item['data'][0])
                    log.debug(f"Processing flaw ID: {flaw_id}, excluded: {flaw_id in existing_ids}")
                    
                    if flaw_id in existing_ids:
                        log.debug(f"Skipping flaw ID {flaw_id} as it's in the exclude list")
                        continue
                        
                    detailed_flaw = self.get_detailed_flaw(flaw_id)
                    if detailed_flaw:
                        log.debug(f"Adding detailed flaw ID: {flaw_id} to results")
                        detailed_flaws.append(detailed_flaw)
                    else:
                        log.debug(f"Failed to get detailed data for flaw ID: {flaw_id}")
            else:
                log.error(f'No flaw data found - Content: {content}')
        else:
            log.error(f'Failed to list flaws. Status code: {response.status_code}, Response: {response.text}')
            
        log.debug(f"Returning {len(detailed_flaws)} detailed flaws")
        return detailed_flaws

    def _load_excluded_flaw_ids(self) -> Set[str]:
        try:
            with open('existing_flaws.txt', 'r') as f:
                return {str(line.strip()) for line in f}
        except FileNotFoundError:
            log.error("existing_flaws.txt not found. No flaws will be excluded.")
            return set()
