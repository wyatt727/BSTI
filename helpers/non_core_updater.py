from typing import Any, Dict, List, Union
from helpers.custom_logger import log
from helpers.flaw_lister import FlawLister
import requests

class NonCoreUpdater:

    def __init__(self, url_manager: Any, request_handler: Any, args: Any):
        """
        Initialize the NonCoreUpdater class with a URL manager, request handler, and additional arguments.

        :param url_manager: Object responsible for managing URLs.
        :param request_handler: Object responsible for handling HTTP requests.
        :param args: Additional command-line arguments or other configurations.
        """
        self.url_manager = url_manager
        self.request_handler = request_handler
        self.args = args
        self.flaw_lister = FlawLister(self.url_manager, self.request_handler)

    def get_new_fields(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": "recommendation_title",
                "label": "Title of the recommendation - Short Recommendation",
                "value": "FIXME"
            },
            {
                "key": "owner",
                "label": "Recommendation owner (who will fix the finding)",
                "value": "Systems Administrator"
            }
        ]
    
    def prepare_fields(self, current_fields: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if isinstance(current_fields, dict):
            current_field_dict = current_fields
        elif isinstance(current_fields, list):
            current_field_dict = {field["key"]: field for field in current_fields}
        else:
            log.error(f"Unexpected format for current_fields: {current_fields}")
            return []

        # Remove any existing 'merged_assets' field and ensure no extra fields are included
        if "merged_assets" in current_field_dict:
            merged_assets_value = current_field_dict["merged_assets"]
            merged_assets_value["key"] = "merged_assets"
            if "sort_order" in merged_assets_value:
                del merged_assets_value["sort_order"]

        new_fields = self.get_new_fields()
        for field in new_fields:
            current_field_dict[field["key"]] = field

        return [
            {
                "key": field.get("key"),
                "label": field.get("label"),
                "value": field.get("value")
            }
            for field in current_field_dict.values()
            if all(k in field for k in ("key", "label", "value"))
        ]

    

    def send_graphql_request(self, flaw_id: str, final_fields: List[Dict[str, Any]]) -> bool:
        url = self.url_manager.get_graphql_url()
        payload = {
            'operationName': 'FindingUpdate',
            'variables': {
                'clientId': int(self.args.client_id),
                'data': {
                    "fields": final_fields
                },
                'findingId': int(flaw_id),
                'reportId': int(self.args.report_id),
            },
            "query": """
            mutation FindingUpdate($clientId: Int!, $data: FindingUpdateInput!, $findingId: Float!, $reportId: Int!) {
            findingUpdate(
                clientId: $clientId
                data: $data
                findingId: $findingId
                reportId: $reportId
            ) {
                ... on FindingUpdateSuccess {
                finding {
                    ...FindingFragment
                    __typename
                }
                __typename
                }
                __typename
            }
            }

            fragment FindingFragment on Finding {
            assignedTo
            closedAt
            createdAt
            code_samples {
                caption
                code
                id
                __typename
            }
            common_identifiers {
                CVE {
                name
                id
                year
                link
                __typename
                }
                CWE {
                name
                id
                link
                __typename
                }
                __typename
            }
            description
            exhibits {
                assets {
                asset
                id
                __typename
                }
                caption
                exhibitID
                index
                type
                __typename
            }
            fields {
                key
                label
                value
                __typename
            }
            flaw_id
            includeEvidence
            recommendations
            references
            scores
            selectedScore
            severity
            source
            status
            subStatus
            tags
            title
            visibility
            calculated_severity
            risk_score {
                CVSS3_1 {
                overall
                vector
                subScore {
                    base
                    temporal
                    environmental
                    __typename
                }
                __typename
                }
                CVSS3 {
                overall
                vector
                subScore {
                    base
                    temporal
                    environmental
                    __typename
                }
                __typename
                }
                CVSS2 {
                overall
                vector
                subScore {
                    base
                    temporal
                    __typename
                }
                __typename
                }
                CWSS {
                overall
                vector
                subScore {
                    base
                    environmental
                    attackSurface
                    __typename
                }
                __typename
                }
                __typename
            }
            hackerOneData {
                bountyAmount
                programId
                programName
                remoteId
                __typename
            }
            snykData {
                issueType
                pkgName
                issueUrl
                identifiers {
                CVE
                CWE
                __typename
                }
                exploitMaturity
                patches
                nearestFixedInVersion
                isMaliciousPackage
                violatedPolicyPublicId
                introducedThrough
                fixInfo {
                isUpgradable
                isPinnable
                isPatchable
                isFixable
                isPartiallyFixable
                nearestFixedInVersion
                __typename
                }
                __typename
            }
            edgescanData {
                id
                portal_url
                details {
                html
                id
                orginal_detail_hash
                parameter_name
                parameter_type
                port
                protocol
                screenshot_urls {
                    file
                    id
                    medium_thumb
                    small_thumb
                    __typename
                }
                src
                type
                __typename
                }
                __typename
            }
            __typename
            }
            """
        }
        try:
            response = self.request_handler.post(url, json=payload)
            if response.status_code == 200:
                log.debug(f'Update complete for flaw {flaw_id}')
                return True
            else:
                response_json = response.json()
                errors = response_json.get('errors', [])
                for error in errors:
                    message = error.get('message', '').lower()
                    if "owasp testing category" in message:
                        log.debug(f'Skipped OWASP Testing Category for flaw ID {flaw_id}')
                    else:
                        log.error(f'Update failed for flaw: {flaw_id}')
                        log.debug(response.content)

                return False
        except requests.RequestException as e:
            log.error(f"Error occurred while updating fields for flaw ID {flaw_id}: {str(e)}")
            return False


    def update_flaw_fields(self, flaw_id: str, current_fields: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        final_fields = self.prepare_fields(current_fields)
        return self.send_graphql_request(flaw_id, final_fields)

    def process(self) -> None:
        flaws = self.flaw_lister.list_flaws()
        for flaw in flaws:
            existing_fields = flaw.get("fields", [])
            self.update_flaw_fields(flaw["id"], existing_fields)
