import json
import xml.etree.ElementTree as ET
import py7zr
import os
from helpers import log
import sys
class GenConfig:
    def __init__(self):
        nessus_file_path = 'plugins-2023-10-02.xml'
        output_file_path = 'N2P_config.json'
        nessus_7z_file = 'plugins-2023-10-02.7z'

        if not os.path.isfile(nessus_file_path):
            if not os.path.isfile(nessus_7z_file):
                log.error(f"Could not find {nessus_7z_file} You must have deleted it or moved it :( - do a fresh git clone and try again.")
                sys.exit(1)
            with py7zr.SevenZipFile(nessus_7z_file, mode='r') as archive:
                archive.extractall(path=os.path.dirname(nessus_file_path))
                log.info(f"Extracted {nessus_7z_file} to {nessus_file_path}")
        if not os.path.isfile(output_file_path):
            log.info(f"Creating {output_file_path} - this will take awhile ...")
            parsed_results = self.parse_nessus_policy_file(nessus_file_path)
            self.save_results_to_json(parsed_results, output_file_path)
            log.success("Done!")

    def categorize_plugins(self, results):
        categorized_results = {}
        categories = {
            "Invalid X.509 (SSL/TLS) Certificate": {
                "writeup_name": "Invalid X.509 (SSL/TLS) Certificate",
                "primary_keywords": ["ssl"],
                "secondary_keywords": ["certificate"],
                "exclude_words": ["tomcat", "apache", "DOS"],
                "writeup_db_id": "147020",
                "guaranteed_ids": ["35291", "45411", "51192", "57582", "15901", "69551", "124410", "60108"]
            },
            "Potentially Unnecessary or Insecure Services" : {
            "writeup_name": "Potentially Unnecessary or Insecure Services",
                "primary_keywords": [],
                "secondary_keywords": [],
                "exclude_words": [],
                "writeup_db_id": "214661",
                "guaranteed_ids": ["10061", "12218"]
            },
            "Default Credentials" : {
            "writeup_name": "Default Credentials",
                "primary_keywords": [],
                "secondary_keywords": [],
                "exclude_words": [],
                "writeup_db_id": "255978",
                "guaranteed_ids": ["106462"]
            },
            "Software Components Out of Date and Vulnerable": {
                "writeup_name": "Software Components Out of Date and Vulnerable",
                "primary_keywords": [">", "<", "Multiple vulnerabilities"],
                "secondary_keywords": [],
                "exclude_words": ["ssl", "tls", "ssh"],
                "writeup_db_id": "12430",
                "guaranteed_ids": ["100681", "168828", "102587", "180192", "102588", "102589", "103329", "103697", "103698", "103782", "104358", "106975", "106976", "106977", "111066", "111067", "111068", "118035", "118036", "121113", "121119", "121120", "121121", "121124", "126125", "132413", "132418", "132419", "133719", "133845", "134862", "136770", "136806", "136807", "138097", "138098", "138574", "138591", "138851", "139584", "141446", "144050", "144054", "145033", "147019", "147163", "147164", "148405", "151502", "152182", "152183", "154147", "157360", "159462", "160891", "160893", "160894", "161181", "162498", "162499", "162502", "166806", "166807", "169458", "171342", "171349", "171656", "173256", "39447", "39479", "44314", "46753", "47577", "48255", "51526", "51975", "51987", "56008", "57080", "62987", "64784", "66426", "70414", "72690", "73756", "74245", "77162", "81579", "81649", "83490", "84738", "88935", "94578", "94637", "95438", "96003", "99361", "99367", "99368"]
            },
            "Unsecured Protocol Version and Ciphers of Administration Services (SSH)": {
                "writeup_name": "Unsecured Protocol Version and Ciphers of Administration Services (SSH)",
                "primary_keywords": ["ssh"],
                "secondary_keywords": ["Key Exchange", "CBC", "mac algorithms"],
                "exclude_words": ["(PCI DSS", "<", ">", "overflow", "injection"],
                "writeup_db_id": "155308",
                "guaranteed_ids": ["90317", "153953", "70658", "71049", "10882", "57620"]
            },
            "Cleartext Communication In Use Or Allowed": {
                "writeup_name": "Cleartext Communication In Use Or Allowed",
                "primary_keywords": ["Web Server Uses Basic Authentication Without HTTPS", "Web Server Transmits Cleartext Credentials", "Unencrypted Telnet Server", "FTP Supports Cleartext Authentication"],
                "secondary_keywords": [""],
                "exclude_words": [],
                "writeup_db_id": "386385",
                "guaranteed_ids": ["42263", "26194", "54582", "34850", "34324", "15855", "87733", "87736"]
            },
            "SNMP Default Community Strings": {
                "writeup_name": "SNMP Default Community Strings",
                "primary_keywords": ["snmp agent"],
                "secondary_keywords": ["public", "community names"],
                "exclude_words": [],
                "writeup_db_id": "444851",
                "guaranteed_ids": ["10264", "41028", "76474"]
            },
            "Unsecured SSL/TLS Configuration": {
                "writeup_name": "Unsecured SSL/TLS Configuration",
                "primary_keywords": ["TLS", "SSL"],
                "secondary_keywords": ["Protocol", "Strength Cipher Suites"],
                "exclude_words": ["(PCI DSS)", "dos", "overflow", "<", ">"],
                "writeup_db_id": "325607",
                "guaranteed_ids": ["104743", "42873", "20007", "132676", "26928", "81606", "83875", "83738", "78479", "65821", "31705", "142960", "42880", "89058", "132675", "157288", "62565"]
            },
            "Unsecured Terminal Services Configuration": {
                "writeup_name": "Unsecured Terminal Services Configuration",
                "primary_keywords": ["Remote Desktop Protocol Server Man-in-the-Middle Weakness", "Unsecured Terminal Services Configuration", "Terminal Services Encryption Level is not FIPS-140 Compliant", "Terminal Services Encryption Level is Medium or Low"],
                "secondary_keywords": [""],
                "exclude_words": [],
                "writeup_db_id": "419174",
                "guaranteed_ids": ["30218", "57690", "58453"]
            },
            
            # Template:
            # "_Checks": {
            #     "writeup_name": ""
            #     "primary_keywords": ["", ""],
            #     "secondary_keywords": [""],
            #     "exclude_words": [],
            #     "writeup_db_id": ""
            # },
        }

        for script_name, plugin_data in results.items():
            plugin_ids = plugin_data["ids"]
            
            for category, category_data in categories.items():
                primary_keywords = category_data["primary_keywords"]
                secondary_keywords = category_data.get("secondary_keywords", [])
                exclude_words = category_data.get("exclude_words", [])
                writeup_name = category_data.get("writeup_name")
                writeup_db_id = category_data.get("writeup_db_id")
                guaranteed_ids = category_data.get("guaranteed_ids", [])
                
                if category not in categorized_results:
                    categorized_results[category] = {
                        "ids": [],
                        "writeup_db_id": writeup_db_id,
                        "writeup_name": writeup_name,
                    }

                # Add the guaranteed IDs if any
                if guaranteed_ids:
                    categorized_results[category]["ids"].extend(gid for gid in guaranteed_ids if gid not in categorized_results[category]["ids"])
                
                for primary_keyword in primary_keywords:
                    if primary_keyword.lower() in script_name.lower():
                        if exclude_words is None or not any(exclude_word.lower() in script_name.lower() for exclude_word in exclude_words):
                            if not secondary_keywords or any(secondary_keyword.lower() in script_name.lower() for secondary_keyword in secondary_keywords):
                                
                                # Avoid adding duplicates
                                unique_ids = [pid for pid in plugin_ids if pid not in categorized_results[category]["ids"]]
                                categorized_results[category]["ids"].extend(unique_ids)
                                
                                break

        return categorized_results


    def parse_nessus_policy_file(self, file_path):
        """
        This function parses a Nessus policy file and extracts relevant information from it to create a dictionary of categorized results.

        The function takes a file path as input, reads the Nessus policy file, and extracts information such as script names,
        script IDs, risk factors, and script families. It filters out scripts with a risk factor of 'None' and includes only
        scripts belonging to specific allowed script families.

        Parameters:
        - file_path (str): The path to the Nessus policy file.

        Returns:
        - categorized_results (dict): A dictionary containing categorized results. The keys are category names,
                                    and the values are dictionaries with categorized plugin information including IDs.

        The function begins by parsing the Nessus policy file using the ElementTree module. It extracts the root element
        of the XML tree structure.

        It initializes an empty dictionary called 'results' to store the extracted plugin information.

        Next, a list of allowed script families is defined. Only scripts belonging to these families will be considered
        for further processing.

        The function then iterates through each 'nasl' element in the XML tree structure. It retrieves the script name,
        script ID, risk factor, and script family for each 'nasl' element.

        If the risk factor is 'None', the script is considered informational and not included in the results.

        If the script family belongs to one of the allowed script families, the script is added to the 'results' dictionary.
        If the script name already exists in 'results', the script ID is appended to the existing list of IDs. Otherwise,
        a new entry is created with the script name and an empty list of IDs.

        Once the parsing and filtering are complete, the 'results' dictionary is passed to the 'categorize_plugins' function,
        which categorizes the plugins based on their script names and returns a categorized dictionary of results.

        Finally, the categorized results are returned from the function.
        """
        tree = ET.parse(file_path)
        root = tree.getroot()

        results = {}

        allowed_script_families = [
            'Backdoors',
            'Brute force attacks',
            'CGI abuses',
            'CISCO',
            'Databases',
            'Default Unix Accounts',
            'DNS',
            'Firewalls',
            'FTP',
            'Gain a shell remotely',
            'General',
            'Misc.',
            'Netware',
            'Peer-To-Peer File Sharing',
            'RPC',
            'SCADA',
            'Service detection',
            'Settings',
            'SMTP problems',
            'SNMP',
            'Tenable.ot',
            'Web Servers',
            'Windows'
        ]

        for nasl_element in root.findall('nasl'):
            script_name_element = nasl_element.find('script_name')
            if script_name_element is not None:
                script_name = script_name_element.text.strip()

                script_id_element = nasl_element.find('script_id')
                if script_id_element is not None:
                    script_id = script_id_element.text.strip()

                    risk_factor_element = nasl_element.find(".//attribute[name='risk_factor']/value")
                    if risk_factor_element is not None and risk_factor_element.text.strip().lower() == 'none':
                        continue

                    script_family_element = nasl_element.find('script_family')
                    if script_family_element is not None:
                        script_family = script_family_element.text.strip()
                        if script_family in allowed_script_families:
                            if script_name not in results:
                                results[script_name] = {
                                    "ids": [],
                                }

                            if script_id not in results[script_name]['ids']:
                                results[script_name]['ids'].append(script_id)

        categorized_results = self.categorize_plugins(results)
        return categorized_results


    def save_results_to_json(self, results, output_file):
        json_data = {"plugins": results}

        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=4)
            f.write('\n')