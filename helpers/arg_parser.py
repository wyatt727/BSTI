import argparse

class ArgumentParser:
    def __init__(self):
        self.args = None

    def parse_args(self):
        """ 
        Main function parsing the options/switches and running the right sequence of functions to import and merge 
        findings from Nessus scan file(s)

        :returns: args - the arguments passed to the script
        """
        parser = argparse.ArgumentParser(description="Import Nessus scans files in Plextrac while regrouping findings")

        # Existing arguments
        parser.add_argument("-u", "--username", help="User's plextrac username", type=str, action="store")
        parser.add_argument("-p", "--password", help="User's plextrac password", type=str, action="store")
        parser.add_argument("-c", "--clientID", dest="client_id", help="Client ID in plextrac", action="store")
        parser.add_argument("-r", "--reportID", dest="report_id", help="Report ID in plextrac", action="store")
        parser.add_argument(
            "-s", "--scope", 
            help="Scope/Tag to add to the imported finding. Choose 'internal' for internal findings, 'external' for external findings, 'mobile' for mobile findings, 'webapp' for web application-related findings, or 'surveillance' for surveillance-related findings.",
            choices=["internal", "external", "mobile", "web", "surveillance"],
            type=str,
            action="store"
        )
        parser.add_argument("-d", "--directory", help="Directory/Folder where to find the Nessus file[s]", type=str, action="store")
        parser.add_argument("-t", "--targettedplextrac", dest='target_plextrac', help="Targetted server [report]", choices=["report"], type=str, action="store")
        parser.add_argument('-ss', '--screenshot_dir', help='Path to the directory containing the screenshots')
        parser.add_argument('-nc', '--noncore', dest="non_core", help='Add non-core custom fields to findings', action='store_true')
        parser.add_argument('--create', help='Prompt for client/report creation', action='store_true')
        parser.add_argument('-v', '--verbosity', type=int, choices=[0, 1, 2], default=1, help="increase output verbosity")

        # New argument for TOML client configuration file
        parser.add_argument(
            '-cf', '--client_config',
            help='Path to the TOML configuration file for client settings',
            type=str
        )

        self.args = parser.parse_args()
        
        return self.args
