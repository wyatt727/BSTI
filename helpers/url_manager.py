from typing import Any, Union
class URLManager:
    def __init__(self, args: Any, base_url: str):
        """
        Initializes the URLManager with the given arguments and base URL.
        
        :param args: Parsed arguments containing API parameters like client_id, report_id, etc.
        :param base_url: The base URL for the API.
        :param v2_base_url: The base URL for the v2 API. (Built off of base_url)
        """
        self.args = args
        self.base_url = base_url + "api/v1"
        self.v2_base_url = base_url + "api/v2"
        self.authenticate_url = f'{self.base_url}/authenticate'

    def _construct_url(self, *segments: Union[str, int]) -> str:
        """
        Constructs a URL by joining the base URL with the given segments.
        
        :param segments: URL segments to append to the base URL.
        :return: Constructed URL.
        """
        str_segments = [str(segment) for segment in segments]
        return f"{self.base_url}/{'/'.join(str_segments)}"
    
    def _construct_v2_url(self, *segments: Union[str, int]) -> str:
        """
        Constructs a URL by joining the base URL with the given segments.
        
        :param segments: URL segments to append to the base URL.
        :return: Constructed URL.
        """
        str_segments = [str(segment) for segment in segments]
        return f"{self.v2_base_url}/{'/'.join(str_segments)}"
    
    def get_writeup_db_url(self, writeup_id: str) -> str:
        """Returns the URL for a specific write-up database."""
        return self._construct_url('template', writeup_id)
    
    def get_update_finding_url(self, flaw_id: str) -> str:
        """Returns the URL for updating a specific finding."""
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id, 'flaw', flaw_id)

    def get_finding_url(self, flaw_id: str) -> str:
        """Returns the URL for getting a specific finding."""
        # This is essentially the same as get_update_finding_url
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id, 'flaw', flaw_id)

    def get_delete_finding_url(self, flaw_id: int) -> str:
        """Returns the URL for deleting a specific finding."""
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id, 'flaw', flaw_id)

    def get_graphql_url(self) -> str:
        """Returns the GraphQL URL."""
        return f'https://{self.args.target_plextrac}.kevlar.bulletproofsi.net/graphql'
    
    def get_copy_report_url(self, writeup_id: str) -> str:
        """Returns the URL for copying a report."""
        return self._construct_url('copy', writeup_id)
    
    def get_client_info_url(self) -> str:
        """Returns the URL for client information."""
        return self._construct_url('client', self.args.client_id)
    
    def get_report_info_url(self) -> str:
        """Returns the URL for report information."""
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id)
    
    def get_delete_flaw_url(self) -> str:
        """Returns the URL for deleting flaws."""
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id, 'flaws', 'delete')
    
    def get_flaws_url(self) -> str:
        """Returns the URL for flaws."""
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id, 'flaws')
    
    def get_upload_nessus_url(self) -> str:
        """Returns the URL for uploading Nessus files."""
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id, 'import', 'offlinecsv')
        ##### This will change in v1.61 to: 
        # return self._construct_v2_url('client', self.args.client_id, 'report', self.args.report_id, 'importAsync', 'offlinecsv')
    
    def get_client_create_url(self) -> str:
        """Returns the URL for creating a new client."""
        return self._construct_url('client', 'create')
    
    def get_report_create_url(self, client_id: str) -> str:
        """Returns the URL for creating a new report."""
        return self._construct_url('client', client_id, 'report', 'create')
    
    def get_report_template_url(self) -> str:
        """Returns the URL for report templates."""
        return self._construct_url('tenant', '0', 'report-templates')
    
    def get_field_template_url(self) -> str:
        """Returns the URL for field templates."""
        return self._construct_url('field-templates')
    
    def get_upload_screenshot_url(self) -> str:
        """Returns the URL for uploading screenshots."""
        return self._construct_url('client', self.args.client_id, 'report', self.args.report_id, 'upload2')