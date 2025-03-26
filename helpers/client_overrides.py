from typing import Any, Dict, List
from helpers.custom_logger import log
from helpers.flaw_lister import FlawLister
import requests
import toml

class ClientOverrides:

    def __init__(self, url_manager: Any, request_handler: Any, args: Any):
        """
        Initialize the ClientOverrides class with a URL manager, request handler, and additional arguments.

        :param url_manager: Object responsible for managing URLs.
        :param request_handler: Object responsible for handling HTTP requests.
        :param args: Additional command-line arguments or other configurations.
        """
        self.url_manager = url_manager
        self.request_handler = request_handler
        self.args = args
        self.flaw_lister = FlawLister(self.url_manager, self.request_handler)
        self.severity_map = self.load_severity_map(args.client_config)

    def load_severity_map(self, toml_file: str) -> Dict[str, str]:
        """
        Load the severity mapping from a TOML file.

        :param toml_file: Path to the TOML configuration file.
        :return: A dictionary mapping finding titles to severities.
        """
        try:
            config = toml.load(toml_file)
            severity_map = {}
            for finding in config.get('finding', []):
                title = finding.get('title')
                severity = finding.get('severity')
                if title and severity:
                    severity_map[title] = severity
            return severity_map
        except Exception as e:
            log.error(f"Failed to load TOML file: {e}")
            return {}

    def build_payload(self, severity: str, flaw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the payload for updating the flaw with the new severity.

        :param severity: The new severity to set.
        :param flaw: The existing flaw details.
        :return: The payload for the update request.
        """
        return {
            "status": flaw.get("status", "Open"),
            "title": flaw.get("title", ""),
            "severity": severity,
            "subStatus": flaw.get("sub_status", "Pass"),
            "assignedTo": flaw.get("assigned_to", ""),
            "description": flaw.get("description", ""),
            "recommendations": flaw.get("recommendations", ""),
            "references": flaw.get("references", ""),
            "tags": flaw.get("tags", []),
            "risk_score": flaw.get("risk_score", {}),
            "calculated_severity": flaw.get("calculated_severity", False),
            "affected_assets": flaw.get("affected_assets", {}),
            "common_identifiers": flaw.get("common_identifiers", {}),
            "exhibits": flaw.get("exhibits", []),
            "client_id": self.args.client_id,
            "report_id": self.args.report_id,
            "source": flaw.get("source", "plextrac"),
            "last_update": flaw.get("last_update", 0),
            "doc_version": flaw.get("doc_version", ""),
            "createdAt": flaw.get("createdAt", 0),
            "report_name": flaw.get("report_name", ""),
            "visibility": flaw.get("visibility", "published"),
            "operators": flaw.get("operators", []),
            "reportedBy": flaw.get("reportedBy", []),
            "cuid": flaw.get("cuid", ""),
            "doc_type": flaw.get("doc_type", "flaw"),
            "fields": flaw.get("fields", {}),
            "tenant_id": flaw.get("tenant_id", "0"),
            "id": flaw.get("id", 0)
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
        Replace or delete flaws based on the TOML configuration and update them via the API.
        """
        flaw_ids = self.get_flaw_ids()
        for flaw_id in flaw_ids:
            flaw = self.flaw_lister.get_detailed_flaw(flaw_id)
            if flaw:
                title = flaw.get("title", "")
                new_severity = self.severity_map.get(title, None)
                url = self.url_manager.get_update_finding_url(flaw_id)

                if new_severity:
                    if new_severity == "DELETE":
                        # Perform a DELETE request to remove the finding
                        delete_url = self.url_manager.get_delete_finding_url(flaw_id)
                        response = self.request_handler.delete(delete_url)
                        
                        if response.status_code == 200:
                            log.info(f"Successfully deleted flaw {flaw_id}")
                        else:
                            log.error(f"Failed to delete flaw {flaw_id}: {response.text}")
                    else:
                        # Update the finding's severity
                        payload = self.build_payload(new_severity, flaw)
                        response = self.request_handler.put(url, json=payload)
                        
                        if response.status_code == 200:
                            log.info(f"Successfully updated flaw {flaw_id} severity to {new_severity}")
                        else:
                            log.error(f"Failed to update flaw {flaw_id}: {response.text}")
                else:
                    log.debug(f"No severity update found for flaw {flaw_id} with title '{title}'")
