import json
import xml.etree.ElementTree as ET
import py7zr
import os
from scripts.logging_config import log


class GenConfig:
    def __init__(self, **kwargs):
        self.regen = kwargs.get('regen', False)
        nessus_file_path = 'plugins-2023-10-02.xml'
        output_file_path = 'NMB_config.json'
        nessus_7z_file = 'plugins-2023-10-02.7z'

        if not os.path.isfile(nessus_file_path):
            with py7zr.SevenZipFile(nessus_7z_file, mode='r') as archive:
                archive.extractall(path=os.path.dirname(nessus_file_path))
                log.success(f"Extracted {nessus_7z_file} to {nessus_file_path}")

        self._check_regen(output_file_path)

        parsed_results = self.parse_nessus_policy_file(nessus_file_path)
        self.save_results_to_json(parsed_results, output_file_path)
        log.success("Done")
    
    def _check_regen(self, output_file_path):
        """Checks if regen flag is enabled and performs it."""
        if self.regen:
            try:
                os.remove(output_file_path)
                log.info("Config will be regenerated - please wait ...")
            except FileNotFoundError:
                log.warning(f"{output_file_path} not found, nothing to remove.")
            except Exception as e:
                log.error(f"Error removing {output_file_path}: {e}")

    def categorize_plugins(self, results):
        """
        This function categorizes plugins based on their script names and assigns them to specific categories.
        The categorization is determined by predefined keywords and optional exclude words. Each category has
        associated scan type, parameters, and verify words that are used for further analysis.

        The function takes a dictionary of plugin results as input and returns a dictionary of categorized results.

        Parameters:
        - results (dict): A dictionary containing plugin results. The keys are script names, and the values
                        are dictionaries with plugin information including IDs.

        Returns:
        - categorized_results (dict): A dictionary containing categorized results. The keys are category names,
                                    and the values are dictionaries with categorized plugin information including
                                    IDs, scan type, parameters, and verify words.

        Categories and their associated data are defined in the 'categories' dictionary within the function.
        Each category consists of the following elements:
        - primary_keywords (list): A list of keywords used to match the script names for categorization.
        - secondary_keywords (list): A list of secondary keywords used to refine the category results. These keywords
                                    are considered only if the primary keyword is found in the script name.
        - exclude_words (list or None): An optional list of exclude words used to exclude specific scripts from a
                                        category. If set to None, exclude words are ignored.
        - scan_type (str): The type of scan to be performed for plugins in the category.
        - parameters (str): The parameters to be passed to the scan command for plugins in the category.
        - verify_words (list): A list of words used to verify the presence of certain features or vulnerabilities
                            related to the plugins in the category.

        The function iterates through the plugin results and matches each script name against the keywords of each
        category. If a match is found and the script name does not contain any of the exclude words (if provided),
        the plugin is assigned to the corresponding category in the categorized_results dictionary.

        Additionally, the function checks if the secondary keywords are found in the script name after applying the
        primary keyword filter. If both the primary and secondary keywords are present in the script name, the plugin
        is included in the corresponding category.

        Finally, the categorized_results dictionary is returned, containing plugins grouped by their respective categories.
        """
        # Base commands
        nmap = 'nmap -T4 --host-timeout 300s'
        msf = 'sudo msfconsole'
        redis_base = 'redis-cli'
        sudo_nmap = 'sudo nmap -T4 --host-timeout 300s'
        
        # metasploit
        metasploit_ipmi = "-q -x 'use auxiliary/scanner/ipmi/ipmi_dumphashes; set rhosts {host} ; set rport {port} ; run; exit'"
        metasploit_ike = "-q -x 'use auxiliary/scanner/ike/cisco_ike_benigncertain; set rhosts {host} ; set rport {port} ; run; exit'"
        metasploit_nla = "-q -x 'use auxiliary/scanner/rdp/rdp_scanner; set rhosts {host} ; set rport {port} ; run; exit'"
        metasploit_SQL_sa = "-q -x 'use auxiliary/scanner/mssql/mssql_login; set rhosts {host} ; set rport {port} ; run; exit'"
        

        # nmap
        service_version = '-sC -sV {host} -p {port}'
        ssl_cert = '--script ssl-cert {host} -p {port}'
        ssh_enum_ciphers = '--script ssh2-enum-algos {host} -p {port}'
        enum_tls_ciphers = '--script ssl-enum-ciphers {host} -p {port}'
        redis_info = '-h {host} info && sleep 1 && echo -e "quit\n"'
        snmp_public = '-v 2c -c public -w {host}'
        smb_signing = '--script smb2-security-mode {host} -p {port}'
        os_version = '-sC -sV -O {host}'
        nfs_showmount = '--script nfs-showmount {host} -p {port}'
        nfs_ls = '--script nfs-ls {host} -p {port}'
        http_enum = '--script http-enum {host} -p {port}'
        anon_ftp = '--script ftp-anon {host} -p {port}' 
        logjam_test = '--script ssl-dh-params {host} -p {port}'
        apache_cassandra = '--script cassandra-brute {host} -p {port}'
        ip_forwarding = "{host} --script ip-forwarding --script-args='target=google.com'"
        rdp_enum_encryption = '--script rdp-enum-encryption {host} -p {port}'
        test_headers = '--script http-security-headers {host} -p {port}'

        # currently not added
        ampq_info = '--script amqp-info {host} -p {port}'
        mdns_detection = "-sUC {host} -p {port}"
        rompager_cve = "--script http-vuln-cve2013-6786 {host} -p {port}"
        metasploit_openssl_ChangeCipherSpec = "-q -x 'use auxiliary/scanner/ssl/openssl_ccs; set rhosts {host} ; set rport {port} ; run; exit'"
        metasploit_msExchange_info = "-q -x 'use auxiliary/scanner/http/owa_iis_internal_ip; set rhosts {host} ; set rport {port} ; run; exit'"
        oracle_tns_poison = "--script oracle-tns-poison {host} -p {port}"

        # curl
        curl_headers = 'curl --silent -I -L -k https://{host}:{port} || curl --silent -I -L http://{host}:{port}'
        jquery_curl_check = "curl --silent -L -i http://{host}:{port} | grep -i jquery || (echo '_' && curl --silent -k -L -i https://{host}:{port} | grep -i jquery || echo '_')"
        puppet_curl_check = "curl --silent -L -i http://{host}:{port} | grep -i puppet || (echo '_' && curl --silent -k -L -i https://{host}:{port} | grep -i puppet || echo '_')"
        hashicorp_curl_check = "curl --silent -L -i http://{host}:{port} | grep -i Hashicorp || (echo '_' && curl --silent -k -L -i https://{host}:{port} | grep -i Hashicorp || echo '_')"
        web_server_auto_complete = "curl --silent -L -i http://{host}:{port} | grep -i autocomplete || (echo '_' && curl --silent -k -L -i https://{host}:{port} | grep -i autocomplete || echo '_')"
        # dns_server_cache = "-sU --script dns-cache-snoop.nse --script-args 'dns-cache-snoop.mode=timed,dns-cache-snoop.domains=google.com' {host}"

        categorized_results = {}
        categories = {
            "Default_MSSQL_Checks": {
                "primary_keywords": ["Microsoft SQL Server sa Account Default Blank Password"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": msf,
                "parameters": metasploit_SQL_sa,
                "verify_words": ["Login Successful:"], 
            },


            "ArubaOS_OOD_Checks": {
                "primary_keywords": ["ArubaOS-Switch Ripple20 Multiple Vulnerabilities (ARUBA-PSA-2020-006)"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["up"], 
            },

            "Java_RMI_Checks": {
                "primary_keywords": ["Java JMX Agent Insecure Configuration"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["up", "Java RMI"], 
            },


            "OOD_MSSQL_Checks": {
                "primary_keywords": ["Microsoft SQL Server Unsupported Version Detection (remote check)"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["version"], 
            },

            "Web_Server_Auto_Complete_Checks": {
                "primary_keywords": ["Web Server Allows Password Auto-Completion"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": "",
                "parameters": web_server_auto_complete,
                "verify_words": ["autocomplete"], 
            },

            "jQuery_Checks": {
                "primary_keywords": ["JQuery"],
                "secondary_keywords": ["Multiple XSS"],
                "exclude_words": [],
                "scan_type": "",
                "parameters": jquery_curl_check,
                "verify_words": ["jquery"], 
            },

            "Puppet_enterprise_Checks": {
                "primary_keywords": ["Puppet Enterprise"],
                "secondary_keywords": ["<", ">", "/"],
                "exclude_words": [],
                "scan_type": "",
                "parameters": puppet_curl_check,
                "verify_words": ["Puppet"], 
            },

            "Logjam_Checks": {
                "primary_keywords": ["SSL/TLS Diffie-Hellman Modulus <= 1024 Bits (Logjam)"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": logjam_test,
                "verify_words": ["VULNERABLE"], 
            },

            "Hashicorp_API_Checks": {
                "primary_keywords": ["Hashicorp Consul Web UI and API access"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": "",
                "parameters": hashicorp_curl_check,
                "verify_words": ["HashiCorp"], 
            },

            "Insecure_NLA_Checks": {
                "primary_keywords": ["Terminal Services Doesn't Use Network Level Authentication (NLA) Only"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": msf,
                "parameters": metasploit_nla,
                "verify_words": ["Requires NLA: No"], 
            },
            # "HSTS_Missing_Checks": {
            #     "primary_keywords": ["HSTS Missing From HTTPS Server"],
            #     "secondary_keywords": [],
            #     "exclude_words": [],
            #     "scan_type": nmap,
            #     "parameters": test_headers,
            #     "verify_words": ["HSTS not configured", "up"], 
            # },
            "Anon_FTP_Checks": {
                "primary_keywords": ["Anonymous FTP Enabled"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": anon_ftp,
                "verify_words": ["ftp-anon", "allowed"], 
            },
             "Redis_Passwordless_Checks": {
                "primary_keywords": ["Redis Server Unprotected by Password Authentication"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": redis_base,
                "parameters": redis_info,
                "verify_words": ["redis_version"], 
            },
            "NFS_Mount_List_Checks": {
                "primary_keywords": ["NFS Share User Mountable"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": nfs_ls,
                "verify_words": ["nfs-ls:", "up"], 
            },
            "NFS_Mount_Checks": {
                "primary_keywords": ["NFS Exported Share Information Disclosure", "NFS Shares World Readable"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": nfs_showmount,
                "verify_words": ["nfs-showmount:", "up"], 
            },
            "SSL_cert_Checks": {
                "primary_keywords": ["ssl"],
                "secondary_keywords": ["certificate"],
                "exclude_words": ["tomcat"],
                "scan_type": nmap,
                "parameters": ssl_cert,
                "verify_words": ["ssl-cert", "subject", "up"], 
            },
            "Tomcat_Checks": {
                "primary_keywords": ["tomcat"],
                "secondary_keywords": [">", "<", "/"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["tomcat", "up"]
            },
            "Esxi_Checks": {
                "primary_keywords": ["esxi"],
                "secondary_keywords": ["<", ">", "/"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["up"]
            },
            "Nginx_Checks": {
                "primary_keywords": ["nginx"],
                "secondary_keywords": ["<", ">", "/"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["nginx", "up"]
            },
            "vCenter_Checks": {
                "primary_keywords": ["vcenter"],
                "secondary_keywords": ["<", ">"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["vcenter", "up"]
            },
            "PHP_Checks": {
                "primary_keywords": ["php"],
                "secondary_keywords": ["<", ">", "Unsupported"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["php", "up"]
            },
            "SNMP_Public_Checks": {
                "primary_keywords": ["snmp agent"],
                "secondary_keywords": ["public", "community names"],
                "exclude_words": ["Default Password"],
                "scan_type": "snmp-check",
                "parameters": snmp_public,
                "verify_words": ["system information", "hostname"]
            },
            "SMB_Signing_Checks": {
                "primary_keywords": ["SMB", "Microsoft Windows SMB Guest Account Local User Access"],
                "secondary_keywords": ["signing not required"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": smb_signing,
                "verify_words": ["up", "smb", "signing"]
            },
            "TLS_Version_Checks": {
                "primary_keywords": ["TLS", "SSL"],
                "secondary_keywords": ["Protocol", "Strength Cipher Suites", "RC4 Cipher Suites Supported (Bar Mitzvah)"],
                "exclude_words": ["(PCI DSS)", "dos", "overflow", "<", ">"],
                "scan_type": nmap,
                "parameters": enum_tls_ciphers,
                "verify_words": ["ciphers", "up"]
            },
            "SSH_Cipher_Checks": {
                "primary_keywords": ["ssh"],
                "secondary_keywords": ["Key Exchange", "CBC", "mac algorithms", "SSH Protocol Version 1 Session Key Retrieval"],
                "exclude_words": ["(PCI DSS", "<", ">", "overflow", "injection"],
                "scan_type": nmap,
                "parameters": ssh_enum_ciphers,
                "verify_words": ["ssh2-enum-algos", "up"]
            },
            "Dell_iDRAC_Checks": {
                "primary_keywords": ["idrac", "dell"],
                "secondary_keywords": ["<", ">", "multiple vulnerabilities", "DSA", "Vulnerability"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["idrac", "up"]
            },
            "Apache_HTTP_Checks": {
                "primary_keywords": ["apache"],
                "secondary_keywords": ["<", ">", "/"],
                "exclude_words": ["tomcat", "log4j"],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["up"]
            },
            "Python_Unsupported_Checks": {
                "primary_keywords": ["python"],
                "secondary_keywords": ["unsupported"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["python", "up"]
            },
            # "Unsupported_Windows_OS_Checks": {
            #     "primary_keywords": ["Unsupported"],
            #     "secondary_keywords": ["Windows OS"],
            #     "exclude_words": [],
            #     "scan_type": sudo_nmap,
            #     "parameters": os_version,
            #     "verify_words": ["OS details:", "up"]
            # },
            "Unsupported_Unix_OS_Checks": {
                "primary_keywords": ["Unix"],
                "secondary_keywords": ["Operating System Unsupported Version Detection"],
                "exclude_words": [],
                "scan_type": sudo_nmap,
                "parameters": os_version,
                "verify_words": ["OS details", "up"]
            },
            "NTP_Mode6_Checks": {
                "primary_keywords": ["Network Time Protocol (NTP) Mode 6 Scanner"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": "ntpq",
                "parameters": "-c rv {host}",
                "verify_words": ["host", "ntpd", "ntp", "system", "clock="]
            },
            "OpenSSL_Version_Checks": {
                "primary_keywords": ["openssl"],
                "secondary_keywords": ["<", ">", "/"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["openssl", "up"]
            },
            "Splunk_Version_Checks": {
                "primary_keywords": ["splunk"],
                "secondary_keywords": ["<", ">"],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["splunk"]
            },
                        
            # "DNS_Server_Cache_Checks": {
            #     "primary_keywords": ["dns server cache snooping remote information disclosure"],
            #     "secondary_keywords": [],
            #     "exclude_words": [],
            #     "scan_type": sudo_nmap,
            #     "parameters": dns_server_cache,
            #     "verify_words": ["up"]
            # },
            
            "Clickjacking_Checks": {
                "primary_keywords": ["Web Application Potentially Vulnerable to Clickjacking"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": "",
                "parameters": curl_headers,
                "verify_words": ["HTTP/1.1 200 OK"]
            },

            "IPMI_Metasploit_Checks": {
                "primary_keywords": ["ipmi v2.0 password hash disclosure"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": msf,
                "parameters": metasploit_ipmi,
                "verify_words": ["hash found"]
            },
            
            "IKE_Metasploit_Checks": {
                "primary_keywords": ["Internet Key Exchange (IKE) Aggressive Mode with Pre-Shared Key"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": msf,
                "parameters": metasploit_ike,
                "verify_words": ["leak", "ike"]
            },

            "HP_iLO_Version_Checks": {
                "primary_keywords": ["ilo"],
                "secondary_keywords": ["<", ">", "/"],
                "exclude_words": ["dos"],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["ilo", "up"]
            },

            "AMQP_Info_Checks": {
                "primary_keywords": ["AMQP Cleartext Authentication"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": ampq_info,
                "verify_words": ["up", "amqp"]
            },
            
            "Cleartext_Comms_Checks": {
                "primary_keywords": ["Web Server Uses Basic Authentication Without HTTPS", "Web Server Transmits Cleartext Credentials", "Unencrypted Telnet Server", "FTP Supports Cleartext Authentication"],
                "secondary_keywords": [],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": service_version,
                "verify_words": ["version", "up"]
            },

            "Rdp_Encryption_Checks": {
                "primary_keywords": ["Remote Desktop Protocol Server Man-in-the-Middle Weakness", "Unsecured Terminal Services Configuration", "Terminal Services Encryption Level is not FIPS-140 Compliant", "Terminal Services Encryption Level is Medium or Low"],
                "secondary_keywords": [""],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": rdp_enum_encryption,
                "verify_words": ["RDP", "up"]
            },

            "IP_Forwarding_Checks": {
                "primary_keywords": ["IP Forwarding Enabled"],
                "secondary_keywords": [""],
                "exclude_words": [],
                "scan_type": nmap,
                "parameters": ip_forwarding,
                "verify_words": ["enabled", "up"]
            },

            "Apache_Cassandra_Checks": {
                "primary_keywords": ["Apache Cassandra Default Credentials"],
                "secondary_keywords": [""],
                "exclude_words": [],
                "scan_type": sudo_nmap,
                "parameters": apache_cassandra,
                "verify_words": ["cassandra", "up"]
            },
            # Template:
            # "_Checks": {
            #     "primary_keywords": ["", ""],
            #     "secondary_keywords": [""],
            #     "exclude_words": [],
            #     "scan_type": nmap,
            #     "parameters": service_version,
            #     "verify_words": ["", ""]
            # },
        }

        for script_name, plugin_data in results.items():
            plugin_ids = plugin_data["ids"]

            for category, category_data in categories.items():
                primary_keywords = category_data["primary_keywords"]
                secondary_keywords = category_data.get("secondary_keywords", [])
                exclude_words = category_data.get("exclude_words", [])
                scan_type = category_data["scan_type"]
                parameters = category_data["parameters"]
                verify_words = category_data["verify_words"]
                # sudo_required = category_data.get("sudo_required", False)

                for primary_keyword in primary_keywords:
                    if primary_keyword.lower() in script_name.lower() and (exclude_words is None or not any(exclude_word.lower() in script_name.lower() for exclude_word in exclude_words)):
                        if not secondary_keywords or any(secondary_keyword.lower() in script_name.lower() for secondary_keyword in secondary_keywords):
                            if category not in categorized_results:
                                categorized_results[category] = {
                                    "ids": [],
                                    "scan_type": scan_type,
                                    "parameters": parameters,
                                    "verify_words": verify_words
                                }
                                
                            existing_ids = categorized_results[category]["ids"]
                            duplicate_ids = list(set(existing_ids) & set(plugin_ids))
                            if duplicate_ids:
                                print(f"Duplicate ids found: {duplicate_ids}")
                                
                            categorized_results[category]["ids"].extend(plugin_ids)
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
            'CGI abuses : XSS',
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
