import csv
import json
import re
import os
import requests
from collections import defaultdict

class Interpreter:
    UNWANTED_STRINGS = {".org", "localhost", "ipaddress", ".io", ".js", ".com", ",", "\"", "\'", ":*", ".png", "css", ".net", ".ico"}
    SERVICE_DETECT_KEYWORDS = {'Service Detect', 'SQL Server', 'Server Detect'}
    FQDN_PATTERN = re.compile(r'(?:FQDN\s+:\s+|Common name:|CN[:=])(?![^|/\n]*\*)([^|/\n]+)')
    HTTP_PATTERN = re.compile(r'https?://\S+')
    CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/csv/known_exploited_vulnerabilities.csv"

    def __init__(self, csv_file, client_dir):
        self.csv_file = csv_file
        self.client_dir = client_dir
        self.output_file = 'Interpreter_output.html'
        self.output_path = os.path.join(self.client_dir, self.output_file)
        self.mindmap_data = self.read_mindmap_json()
        self.cisa_kev_file = os.path.join(self.client_dir, "known_exploited_vulnerabilities.csv")
        self.cisa_kev_data = self.download_and_parse_cisa_kev()
        self.generate_html_output()
        self.cleanup_files()

    @staticmethod
    def read_mindmap_json():
        with open("mindmap.json", 'r', encoding='utf-8') as file:
            return json.load(file)

    def download_and_parse_cisa_kev(self):
        # Download the CISA KEV CSV file
        response = requests.get(self.CISA_KEV_URL)
        with open(self.cisa_kev_file, 'wb') as file:
            file.write(response.content)

        # Parse the CISA KEV CSV file
        cisa_kev_data = {}
        with open(self.cisa_kev_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cve_id = row['cveID']
                cisa_kev_data[cve_id] = {
                    "vulnerabilityName": row.get('vulnerabilityName', 'NA'),
                    "vendorProject": row.get('vendorProject', 'NA'),
                    "product": row.get('product', 'NA'),
                    "shortDescription": row.get('shortDescription', 'NA'),
                    "notes": row.get('notes', 'NA'),
                }
        return cisa_kev_data

    def collect_nessus_data(self, row, nessus_data):
        name = row['Name']
        plugin_output = row['Plugin Output']
        host = row['Host']
        port = row['Port']
        if any(keyword in name for keyword in self.SERVICE_DETECT_KEYWORDS):
            output_to_use = name if not plugin_output or len(plugin_output) > 110 else plugin_output
            if port.isdigit():
                nessus_data[output_to_use][int(port)].append(host)

    def read_csv_and_collect_info(self):
        nessus_data = defaultdict(lambda: defaultdict(list))
        os_info = {}
        basic_host_info = defaultdict(list)
        dns_hostnames = {}
        vulnerability_info = defaultdict(list)
        http_info = defaultdict(list)
        known_exploitable_vulns = defaultdict(list)

        with open(self.csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.collect_nessus_data(row, nessus_data)
                self.collect_os_info(row, os_info)
                self.collect_basic_host_info(row, basic_host_info)
                self.collect_dns_hostnames(row, dns_hostnames)
                self.collect_vulnerability_info(row, vulnerability_info)
                self.collect_http_info(row, http_info)
                self.collect_known_exploitable_vulns(row, known_exploitable_vulns)

        # Filter HTTP info
        self.filter_http_info(http_info)

        return nessus_data, os_info, basic_host_info, dns_hostnames, vulnerability_info, http_info, known_exploitable_vulns

    def collect_os_info(self, row, os_info):
        if row['Name'] == 'OS Identification':
            plugin_output = row['Plugin Output']
            os_description = plugin_output.split('\n')[1] if '\n' in plugin_output else 'Unknown OS'
            os_info[row['Host']] = os_description.replace('Remote operating system :', '').strip()

    def collect_basic_host_info(self, row, basic_host_info):
        if 'Nessus SYN scanner' in row['Name'] and row['Port'].isdigit():
            basic_host_info[row['Host']].append(int(row['Port']))

    def collect_dns_hostnames(self, row, dns_hostnames):
        plugin_output = row['Plugin Output']
        matches = self.FQDN_PATTERN.findall(plugin_output)
        for match in matches:
            if '.' in match and not match.startswith("ip-"):
                dns_hostnames[row['Host']] = match
                break

    def collect_vulnerability_info(self, row, vulnerability_info):
        if row['Risk'] != 'None':
            cve = row.get('CVE', 'N/A')
            cvss = row.get('CVSS v2.0 Base Score', 'N/A')
            name = row.get('Name', 'N/A')
            description = row.get('Description', 'N/A')
            ports = row.get('Port', 'N/A')
            risk = row.get('Risk', 'N/A')
            vulnerability_info[name].append((description, cve, cvss, row['Host'], ports, risk))

    def collect_http_info(self, row, http_info):
        plugin_output = row['Plugin Output']
        if 'http://' in plugin_output or 'https://' in plugin_output:
            http_info[row['Host']].extend(self.HTTP_PATTERN.findall(plugin_output))

    def collect_known_exploitable_vulns(self, row, known_exploitable_vulns):
        cve = row.get('CVE', 'N/A')
        if cve in self.cisa_kev_data:
            vuln_info = self.cisa_kev_data[cve]
            host = row['Host']
            known_exploitable_vulns[cve].append((vuln_info, host))

    @classmethod
    def filter_http_info(cls, http_info):
        for host, urls in list(http_info.items()):
            filtered_urls = {url for url in urls if not any(unwanted in url for unwanted in cls.UNWANTED_STRINGS)}
            http_info[host] = list(filtered_urls)

    def generate_bash_script(self, http_info):
        bash_script = """
        #!/bin/bash

        # List of URLs to check
        declare -a URL_LIST=({urls})

        # Loop through each URL
        for url in "${{URL_LIST[@]}}"; do
            # Get HTTP status code using curl
            STATUS_CODE=$(curl -o /dev/null -s -w "%{{http_code}}" "$url")

            # Check if the status code is 200
            if [ "$STATUS_CODE" == "200" ]; then
                echo "$url returned 200 OK. Taking screenshot..."
                
                # Use EyeWitness.py to grab a screenshot
                ./EyeWitness.py -f <(echo "$url") --web

            else
                echo "$url returned $STATUS_CODE"
            fi
        done
        """

        urls = ' '.join(f'"{url}"' for hosts in http_info.values() for url in hosts)
        bash_script = bash_script.replace("{urls}", urls)
        return bash_script

    def generate_html_output(self):
        nessus_data, os_info, basic_host_info, dns_hostnames, vulnerability_info, http_info, known_exploitable_vulns = self.read_csv_and_collect_info()
        mindmap_data = self.read_mindmap_json()

        # Start collecting HTML content
        html_content = []

        # Initial HTML structure
        html_content.append("""
        <html>
        <head>
            <title>Interpreter</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css">
            <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.3/dist/umd/popper.min.js"></script>
            <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
            <style>
                body {
                    background-color: #121212;
                    color: #ffffff;
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    width: 90%;
                    max-width: 100%;
                    margin: 0 auto;
                    padding: 20px;
                }
                .collapsible, .vulnerability {
                    background-color: #333;
                    color: #fff;
                    cursor: pointer;
                    padding: 10px;
                    width: 100%;
                    border: none;
                    outline: none;
                    font-size: 18px;
                    text-align: left;
                    margin-bottom: 5px;
                }
                .collapsible .icons, .vulnerability .icons {
                    float: right;
                }
                .content, .content-service, .content-vulnerability {
                    padding: 10px;
                    display: none;
                    overflow: hidden;
                    background-color: #444;
                    text-align: left;
                }
                .collapsible-service, .collapsible-vulnerability {
                    background-color: #555;
                    color: #fff;
                    cursor: pointer;
                    padding: 10px;
                    width: 100%;
                    border: none;
                    outline: none;
                    font-size: 16px;
                    text-align: left;
                    margin-bottom: 5px;
                }
                .content-service, .content-vulnerability {
                    padding: 0 10px;
                    display: none;
                    overflow: hidden;
                    background-color: #666;
                    text-align: left;
                }
                .ip-address {
                    padding-left: 20px;
                    list-style-type: square;
                }
                textarea {
                    width: 100%;
                    min-height: 100px;
                }
                .hidden {
                    display: none;
                }
                .links {
                    margin-top: 10px;
                }
                .links a {
                    color: #0078d4;
                    text-decoration: underline;
                    margin-right: 10px;
                }
                .host-info-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .host-entry {
                    display: flex;
                    justify-content: space-between;
                    padding: 0px 0;
                }
                .host-entry .host-ip, .host-entry .host-os, .host-entry .host-dns {
                    padding: 0 10px;
                }
                .host-entry .host-ip {
                    text-align: left;
                    flex-basis: 20%;
                }
                .host-entry .host-os {
                    text-align: left;
                    flex-basis: 40%;
                }
                .host-entry .host-dns {
                    text-align: right;
                    flex-basis: 40%;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Interpreter</h1>
                <button id='expandAll' onclick='expandAllSections()'>Expand All</button>
                <button id='collapseAll' onclick='collapseAllSections()'>Collapse All</button>
        """)

        # Group hosts by OS
        hosts_by_os = defaultdict(list)
        for host, ports in basic_host_info.items():
            os_description = os_info.get(host, 'Unknown OS')
            dns_hostname = dns_hostnames.get(host, '')
            hosts_by_os[os_description].append({
                "host": host,
                "ports": ports,
                "dns_hostname": dns_hostname
            })

        # Sort the OS descriptions alphabetically
        sorted_os_descriptions = sorted(hosts_by_os.keys())

        # Include grouped host information by OS
        html_content.append("<div class='collapsible-container'>")
        html_content.append("<div class='collapsible' onclick='toggleContent(this)'><span class='service'><strong>Host Info</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>")
        html_content.append("<div class='content'>")

        for os_description in sorted_os_descriptions:
            hosts = hosts_by_os[os_description]
            html_content.append(f"<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='service'><strong>{os_description}</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>")
            html_content.append("<div class='content-service'>")

            for host_info in hosts:
                host = host_info['host']
                ports = host_info['ports']
                dns_hostname = host_info['dns_hostname']

                html_content.append("<div class='collapsible-container-service'>")
                html_content.append("<div class='collapsible-service' onclick='toggleContentService(this)'>")
                html_content.append("<div class='host-entry'>")
                html_content.append(f"<span class='host-ip'>{host}</span>")
                html_content.append(f"<span class='host-dns'>{dns_hostname}</span>")
                html_content.append("</div>")
                html_content.append("<span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>")
                html_content.append("<div class='content-service'>")
                html_content.append(f"<p><strong class='service'>Ports: {','.join(map(str, ports))}</strong></p>")

                for port in ports:
                    port_data = mindmap_data.get(str(port))
                    if port_data:
                        link = port_data.get('Link')
                        # notes = port_data.get('Notes')
                        if link:
                            links = link.split('\n')
                            for link_item in links:
                                html_content.append(f"<p><strong>Port {port}:</strong> <a href='{link_item.strip()}' target='_blank'>{link_item.strip()}</a></p>")
                        # if notes:
                        #    html_content.append(f"<p><strong>Notes:</strong> {notes}</p>")

                html_content.append("</div></div>")

            html_content.append("</div></div>")

        html_content.append("</div></div>")

        # Sort the nessus_data based on the character count of Plugin Output
        nessus_data_sorted = sorted(nessus_data.items(), key=lambda item: len(item[0]))

        # List of keywords or phrases to filter out
        filter_out_keywords = ["SSL certificate", "seems to be", "SSLv", "Service URL", "TCP wrapper", "TLSv", "Nessus detected", "Version", "Server Status", "banner", "http://", "https://", "ping"]

        # Include Service Info
        html_content += "<div class='collapsible-container'>"
        html_content += "<div class='collapsible' onclick='toggleContent(this)'><span class='service'><strong>Service Info</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
        html_content += "<div class='content'>"
        for plugin_output, ports_data in nessus_data_sorted:
            # Check if the plugin_output contains any of the keywords to filter out
            if any(keyword in plugin_output for keyword in filter_out_keywords):
                continue  # Skip this entry

            html_content += f"<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='service'><strong>Service: {plugin_output}</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
            html_content += "<div class='content-service'>"
            for port, hosts in ports_data.items():
                html_content += "<p><strong>Port:</strong> {}\n".format(port)
                html_content += "<textarea readonly='' rows='4' cols='50'>\n"
                html_content += "\n".join(hosts)
                html_content += "</textarea></p>"

                # Include mindmap data for this port, if available
                mindmap_port_data = mindmap_data.get(str(port))
                if mindmap_port_data:
                    link = mindmap_port_data.get('Link')
                    notes = mindmap_port_data.get('Notes')
                    if link:
                        html_content += f"<p>{link}</p>"
                    #if notes:
                    #    html_content += f"<p><strong>Notes:</strong> {notes}</p>"

            html_content += "</div></div>"
        html_content += "</div></div>"

        # Include Known Exploitable Vulns
        html_content += "<div class='collapsible-container'>"
        html_content += "<div class='collapsible' onclick='toggleContent(this)'><span class='vulnerability'><strong>CISA KEV Info</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
        html_content += "<div class='content'>"

        for cve, details in known_exploitable_vulns.items():
            vuln_info = details[0][0]
            hosts = [host for _, host in details]

            html_content += f"<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='vulnerability'><strong>{vuln_info['vulnerabilityName']} ({cve})</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
            html_content += "<div class='content-service'>"
            html_content += f"<p><strong>Vendor/Project:</strong> {vuln_info['vendorProject']}</p>"
            html_content += f"<p><strong>Product:</strong> {vuln_info['product']}</p>"
            html_content += f"<p><strong>Description:</strong> {vuln_info['shortDescription']}</p>"
            html_content += f"<p><strong>Notes:</strong> {vuln_info['notes']}</p>"
            html_content += "<p><strong>Associated IPs</strong>: <textarea readonly='' rows='4' cols='50'>"
            html_content += "\n".join(hosts)
            html_content += "</textarea></p>"
            html_content += "</div></div>"

        html_content += "</div></div>"

        # Group vulnerabilities by criticality
        vulnerabilities_by_criticality = {
            "Critical": [],
            "High": [],
            "Medium": [],
            "Low": []
        }

        risk_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        risk_colors = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "green"}

        for vulnerability_name, vulnerability_data in vulnerability_info.items():
            description, cve, cvss, host, ports, risk = vulnerability_data[0]
            vulnerabilities_by_criticality[risk].append({
                "name": vulnerability_name,
                "description": description,
                "cve": cve,
                "cvss": cvss,
                "host": host,
                "ports": ports
            })

        # Include Vulnerability Info grouped by criticality
        html_content.append("<div class='collapsible-container'>")
        html_content.append("<div class='collapsible' onclick='toggleContent(this)'><span class='vulnerability'><strong>Nessus Vulnerability Info</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>")
        html_content.append("<div class='content'>")

        for criticality in ["Critical", "High", "Medium", "Low"]:
            vulnerabilities = vulnerabilities_by_criticality[criticality]
            if vulnerabilities:
                html_content.append(f"<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='vulnerability'><strong>{criticality}: ({len(vulnerabilities)})</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>")
                html_content.append("<div class='content-service'>")

                for vuln in vulnerabilities:
                    html_content.append(f"<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='vulnerability'><strong style='color: {risk_colors[criticality]}'>{vuln['name']}</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>")
                    html_content.append("<div class='content-service'>")
                    html_content.append(f"<p><strong>Description:</strong> {vuln['description']}</p>")
                    html_content.append(f"<p><strong>CVE:</strong> {vuln['cve']}</p>")
                    html_content.append(f"<p><strong>CVSS:</strong> {vuln['cvss']}</p>")
                    html_content.append(f"<p><strong>Associated Ports:</strong> {vuln['ports']}</p>")
                    html_content.append("<p><strong>Hosts:</strong> <textarea readonly='' rows='4' cols='50'>")
                    html_content.append(f"{vuln['host']}")
                    html_content.append("</textarea></p>")
                    html_content.append("</div></div>")

                html_content.append("</div></div>")

        html_content.append("</div></div>")  # Close Vulnerability Info section

        
        # Include HTTP(S) Info
        html_content += "<div class='collapsible-container'>"
        html_content += "<div class='collapsible' onclick='toggleContent(this)'><span class='service'><strong>HTTP(S) Info</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
        html_content += "<div class='content'>"

        # Include the "All URLs" section
        all_urls = [url for urls in http_info.values() for url in urls]
        html_content += "<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='service'><strong>All URLs</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
        html_content += "<div class='content-service'>"
        html_content += "<textarea readonly='' rows='20' cols='100'>\n"
        html_content += "\n".join(all_urls)
        html_content += "</textarea>"
        html_content += "<p><code>cat urls.txt | aquatone -out ./aquatone-data</code></p>"
        html_content += "</div></div>"

        # Include HTTP(S) Info
        html_content += "<div class='collapsible-container'>"
        html_content += "<div class='collapsible' onclick='toggleContent(this)'><span class='service'><strong>Directories Per Host</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
        html_content += "<div class='content'>"
        
        for host, urls in http_info.items():
            html_content += f"<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='service'><strong>Host: {host}</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
            html_content += "<div class='content-service'>"
            html_content += "<ul class='ip-address'>"
            html_content += "<p><strong>URLs:</strong></p>"
            for url in urls:
                html_content += f"<li>{url}</li>"
            html_content += "</ul>"

            html_content += "</div></div>"
        html_content += "</div></div>"

        # Include the EyeWitness Bash Script. Need to test/update this, currently just works in theory. Probably use aquatone instead.
        bash_script_content = self.generate_bash_script(http_info)
        html_content += "<div class='collapsible-container-service'><div class='collapsible-service' onclick='toggleContentService(this)'><span class='service'><strong>Bash Script for EyeWitness.py</strong></span><span class='icons'><span class='expand-button'></span><span class='collapse-button'></span></span></div>"
        html_content += "<div class='content-service'>"
        html_content += "<p>Checks each URL to see if it returns 200 code, and if it does, it uses eyewitness to capture screenshot of the page."
        html_content += f"<textarea readonly='' rows='20' cols='100'>{bash_script_content}</textarea>"
        html_content += "</div></div>"
        
        # JavaScript for toggling content
        html_content.append("""
        <script>
            function toggleContent(element) {
                var content = element.nextElementSibling;
                if (content.style.display === 'block') {
                    content.style.display = 'none';
                } else {
                    content.style.display = 'block';
                }
            }

            function toggleContentService(element) {
                var content = element.nextElementSibling;
                if (content.style.display === 'block') {
                    content.style.display = 'none';
                } else {
                    content.style.display = 'block';
                }
            }

            function expandAllSections() {
                var contents = document.getElementsByClassName('content');
                for (var i = 0; i < contents.length; i++) {
                    contents[i].style.display = 'block';
                }
            }

            function collapseAllSections() {
                var contents = document.getElementsByClassName('content');
                for (var i = 0; i < contents.length; i++) {
                    contents[i].style.display = 'none';
                }
            }
        </script>
        </div></body></html>
        """)

        # Join and write the final HTML content
        final_html_content = ''.join(html_content)
        with open(self.output_path, 'w', encoding='utf-8') as file:
            file.write(final_html_content)
    
    def cleanup_files(self):
        # Delete the CISA KEV CSV file after processing
        if os.path.exists(self.cisa_kev_file):
            os.remove(self.cisa_kev_file)
