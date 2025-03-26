from typing import Any, Dict, Optional
from helpers.custom_logger import log
from helpers.flaw_lister import FlawLister
import requests

class DescriptionProcessor:
    def __init__(self, config: Dict[str, Any], url_manager: Any, request_handler: Any, mode: str, args: Any):
        """
        Initialize the DescriptionProcessor class with configurations, a URL manager, and a request handler.

        :param config: Configuration dictionary.
        :param url_manager: Object responsible for managing URLs.
        :param request_handler: Object responsible for handling HTTP requests.
        :param mode: Mode of operation ("external" or other values).
        :param args: Command-line arguments or other configurations.
        """
        self.config = config
        self.url_manager = url_manager
        self.request_handler = request_handler
        self.mode = mode
        self.args = args
        self.flaw_lister = FlawLister(self.url_manager, self.request_handler)

    def retrieve_writeup_details(self, writeup_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the details of a writeup based on the given writeup_id.

        :param writeup_id: ID of the writeup.
        :return: Dictionary containing details of the writeup, or None if the request fails.
        """
        url = self.url_manager.get_writeup_db_url(writeup_id)
        response = self.request_handler.get(url)
        
        if response.status_code == 200:
            return response.json()
            
        else:
            return None

    def update_flaw_description(self, flaw_id: str, description: str, recommendation: str, references: str) -> bool:
        """
        Update the description and recommendation of a flaw based on the given flaw_id.

        :param flaw_id: ID of the flaw.
        :param description: New description to set.
        :param recommendation: New recommendation to set.
        :return: True if update is successful, False otherwise.
        """
        url = self.url_manager.get_graphql_url()

        payload = {
            'operationName': 'FindingUpdate',
            'variables': {
                'clientId': int(self.args.client_id),
                'data': {
                    'description': description,
                    'recommendations': recommendation,
                    'references' : references
                },
                'findingId': float(flaw_id),
                'reportId': int(self.args.report_id),
            },
            "query": "mutation FindingUpdate($clientId: Int!, $data: FindingUpdateInput!, $findingId: Float!, $reportId: Int!) {\n  findingUpdate(\n    clientId: $clientId\n    data: $data\n    findingId: $findingId\n    reportId: $reportId\n  ) {\n    ... on FindingUpdateSuccess {\n      finding {\n        ...FindingFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment FindingFragment on Finding {\n  assignedTo\n  closedAt\n  createdAt\n  code_samples {\n    caption\n    code\n    id\n    __typename\n  }\n  common_identifiers {\n    CVE {\n      name\n      id\n      year\n      link\n      __typename\n    }\n    CWE {\n      name\n      id\n      link\n      __typename\n    }\n    __typename\n  }\n  description\n  exhibits {\n    assets {\n      asset\n      id\n      __typename\n    }\n    caption\n    exhibitID\n    index\n    type\n    __typename\n  }\n  fields {\n    key\n    label\n    value\n    __typename\n  }\n  flaw_id\n  includeEvidence\n  recommendations\n  references\n  scores\n  selectedScore\n  severity\n  source\n  status\n  subStatus\n  tags\n  title\n  visibility\n  calculated_severity\n  risk_score {\n    CVSS3_1 {\n      overall\n      vector\n      subScore {\n        base\n        temporal\n        environmental\n        __typename\n      }\n      __typename\n    }\n    CVSS3 {\n      overall\n      vector\n      subScore {\n        base\n        temporal\n        environmental\n        __typename\n      }\n      __typename\n    }\n    CVSS2 {\n      overall\n      vector\n      subScore {\n        base\n        temporal\n        __typename\n      }\n      __typename\n    }\n    CWSS {\n      overall\n      vector\n      subScore {\n        base\n        environmental\n        attackSurface\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  hackerOneData {\n    bountyAmount\n    programId\n    programName\n    remoteId\n    __typename\n  }\n  snykData {\n    issueType\n    pkgName\n    issueUrl\n    identifiers {\n      CVE\n      CWE\n      __typename\n    }\n    exploitMaturity\n    patches\n    nearestFixedInVersion\n    isMaliciousPackage\n    violatedPolicyPublicId\n    introducedThrough\n    fixInfo {\n      isUpgradable\n      isPinnable\n      isPatchable\n      isFixable\n      isPartiallyFixable\n      nearestFixedInVersion\n      __typename\n    }\n    __typename\n  }\n  edgescanData {\n    id\n    portal_url\n    details {\n      html\n      id\n      orginal_detail_hash\n      parameter_name\n      parameter_type\n      port\n      protocol\n      screenshot_urls {\n        file\n        id\n        medium_thumb\n        small_thumb\n        __typename\n      }\n      src\n      type\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
        }

        try:
            response = self.request_handler.post(url, json=payload)
            if response.status_code == 200:
                log.debug(f'Update complete {flaw_id}')
                # print("DEBUG UPDATE DISC:", response.content)
                return True
            else:
                log.error(f'Update failed for flaw: {flaw_id}')
                print(response.content)
                return False
        except requests.RequestException as e:
            log.error(f"Error occurred while trying to update the description for flaw ID {flaw_id}: {str(e)}")
            print(response.content)
            return False
        
    def _get_title_prefix(self) -> str:
        """
        Get the appropriate title prefix based on the mode to ensure uniqueness and context clarity.

        Modes and their prefixes:
        - "external": Prefixes with "(External)"
        - "web": Prefixes with "(WebApp)"
        - "surveillance": Prefixes with "(Surveillance)"
        - "mobile": Prefixes with "(Mobile)"
        - Other/internal: No prefix

        :return: Title prefix as a string.
        """
        prefix_map = {
            "external": "(External) ",
            "web": "(Web) ",
            "surveillance": "(Surveillance) ",
            "mobile": "(Mobile) ",
            "internal": ""
        }
        return prefix_map.get(self.mode, "")


    def process(self) -> None:
        """
        Process each flaw, update its description and recommendation if it matches a writeup_db entry.
        """
        flaws = self.flaw_lister.list_flaws()
        title_prefix = self._get_title_prefix()
        
        for flaw in flaws:
            flaw_name = flaw["title"]
            
            for category, details in self.config["plugins"].items():
                adjusted_writeup_name = title_prefix + details["writeup_name"]
                
                if flaw_name == adjusted_writeup_name:
                    writeup_id = details["writeup_db_id"]
                    writeup_details = self.retrieve_writeup_details(writeup_id)
                    
                    if writeup_details:
                        description = writeup_details.get("description", "")
                        recommendation = writeup_details.get("recommendations", "")
                        references = writeup_details.get("references", "")
                        self.update_flaw_description(flaw["id"], description, recommendation, references)
