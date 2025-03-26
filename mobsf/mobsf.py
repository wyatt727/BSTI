import json
import os
import time
import requests
import re
import csv
from bs4 import BeautifulSoup
from scripts.logging_config import log

class Mobber:
    def __init__(self, mobsf_url, app_path):
        self.mobsf_url = mobsf_url
        self.api_base = "/api/v1"
        self.api_docs_url = f"{mobsf_url}/api_docs"
        self.pdf_url = f"{mobsf_url}{self.api_base}/download_pdf"
        self.upload_url = f"{mobsf_url}{self.api_base}/upload"
        self.scan_url = f"{mobsf_url}{self.api_base}/scan"
        self.scorecard_url = f"{mobsf_url}{self.api_base}/scorecard"
        self.manifest_url = f"{mobsf_url}/manifest_view"
        self.app_path = app_path
        self.api_key = self.get_api_key()
        self.headers = {"Authorization": self.api_key}

        self.app_name = os.path.splitext(os.path.basename(self.app_path))[0]

        _, ext = os.path.splitext(self.app_path)
        self.scan_type = self.get_scan_type(ext)

        report_name = f"{self.app_name}-mobsf-report.pdf"
        self.scorecard_name = f"SCORECARD-{self.app_name}-mobsf.csv"
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)
        self.report_output_path = os.path.join(report_dir, report_name)
        self.scorecard_output_path = os.path.join(report_dir, self.scorecard_name)
        self.file_name, self.hash_value = self.upload_file()

    def get_scan_type(self, extension):
        """Determine the scan type based on the file extension."""
        if extension in ['.apk', '.xapk']:
            return 'apk'
        elif extension in ['.ipa']:
            return 'ipa'
        else:
            log.error(f"Unsupported file extension: {extension}")
            raise ValueError(f"Unsupported file extension: {extension}")

    def get_api_key(self):        
        response = requests.get(self.api_docs_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            api_key_element = soup.select_one("p.lead strong code")
            if api_key_element:
                api_key = api_key_element.get_text(strip=True)
                return api_key
        return None

    def upload_file(self):
        files = {"file": (self.app_path, open(self.app_path, "rb"), "application/octet-stream")}
        response = requests.post(self.upload_url, files=files, headers=self.headers)
        if response.status_code == 200:
            response_json = response.json()
            file_name = response_json["file_name"]
            hash_value = response_json["hash"]
            return file_name, hash_value
        elif response.status_code == 401:
            log.error("Authentication failed. Please check your API key.")
        else:
            log.error(f"Failed to upload file. Status code: {response.status_code}")
            log.error(f"Response: {response.text}")
        return None

    def monitor_scan(self):
        data = {
            "file_name": self.file_name,
            "hash": self.hash_value,
            "scan_type": self.scan_type,
            "re_scan": "0"  # 0 for no rescan, 1 for rescan
        }
        try:
            response = requests.post(self.scan_url, headers=self.headers, data=data)
            return response
        except Exception as e:
            log.error(f'Error during scan: {e}')
            raise

    def scan_file(self):
        response = self.monitor_scan()
        if response.status_code == 200:
            findings = response.json().get('findings', [])
            return {"success": True, "findings": findings}
        else:
            log.error(f"Failed to start scan. Status code: {response.status_code}")
            log.error(f"Response: {response.text}")
            return {"success": False}


    def generate_scorecard(self):
        retry = 0
        data = {"hash": self.hash_value}
        response = requests.post(self.scorecard_url, headers=self.headers, data=data)
        while response.status_code != 200:
            time.sleep(3)
            log.warning(f"Retry number: {retry} - retrying up to 3 times...")
            if retry == 3:
                log.error("Unable to export scorecard")
                return False
            elif response.status_code == 200:
                continue
            else:
                retry += 1

        try:
            json_data = json.loads(response.content)
            high_issues = json_data.get("high", [])
            warning_issues = json_data.get("warning", [])
            info_issues = json_data.get("info", [])
            secure_issues = json_data.get("secure", [])
            hotspot_issues = json_data.get("hotspot", [])

            csv_file_path = self.scorecard_output_path

            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                def write_section_header(title):
                    writer.writerow([title])
                    writer.writerow(["Title", "Description", "Section"])

                for issues, header in [
                    (high_issues, "High Issues"),
                    (warning_issues, "Warning Issues"),
                    (info_issues, "Info Issues"),
                    (secure_issues, "Secure Issues"),
                    (hotspot_issues, "Hotspot Issues")
                ]:
                    write_section_header(header)
                    for issue in issues:
                        writer.writerow([issue.get("title", ""), issue.get("description", ""), issue.get("section", "")])

            return True

        except json.JSONDecodeError as e:
            log.error("Failed to decode JSON response: %s", str(e))
            return False
        except Exception as e:
            log.error("An error occurred: %s", str(e))
            return False

    def generate_report(self):
        retry = 0
        data = {"hash": self.hash_value}
        response = requests.post(self.pdf_url, headers=self.headers, data=data)
        while response.status_code != 200:
            log.info("Waiting for the report to become available...")
            time.sleep(3)
            log.warning(f"Retry number: {retry} - retrying up to 3 times...")
            if retry == 3:
                log.error("Unable to export report")
                return False
            elif response.status_code == 200:
                continue
            else:
                retry += 1

        with open(self.report_output_path, "wb") as file:
            file.write(response.content)
        return True
    
    def download_manifest(self):
        if not self.hash_value:
            log.error("Scan hash is not available.")
            return None

        manifest_url = f"{self.manifest_url}/{self.hash_value}/?type=apk"

        try:
            response = requests.get(manifest_url)
            if response.status_code == 200:
                # Parse the HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                h3_tag = soup.find('h3', text=re.compile(r'AndroidManifest\.xml\s*'))
                pre_tag = h3_tag.find_next('pre', id='code_block') if h3_tag else None

                if pre_tag:
                    # Extract and decode the XML content
                    xml_content = pre_tag.get_text()

                    # Write the XML content to a file
                    manifest_file_path = f"reports/{self.app_name}-AndroidManifest.xml"
                    with open(manifest_file_path, "w", encoding="utf-8") as file:
                        file.write(xml_content)

                    return manifest_file_path
                else:
                    log.error("Failed to find the AndroidManifest.xml content in the page.")
                    return None
            else:
                log.error(f"Failed to download manifest. Status code: {response.status_code}")
                log.error(f"Response: {response.text}")
                return None
        except Exception as e:
            log.error(f"An error occurred while downloading the manifest: {e}")
            return None
        
    def parse_results(self):
        findings = []
        report_dir = 'reports'
        scorecard_csv_path = os.path.join(report_dir, self.scorecard_name)
        
        if not os.path.exists(scorecard_csv_path):
            log.error("Scorecard file does not exist.")
            return findings
        
        with open(scorecard_csv_path, 'r') as file:
            reader = csv.reader(file)
            current_section = None
            
            for row in reader:
                if len(row) == 1 and not row[0].startswith("Title"):
                    current_section = row[0]
                elif len(row) == 3 and current_section:
                    findings.append({
                        "title": row[0],
                        "description": row[1],
                        "section": row[2],
                        "severity": current_section.split(" ")[0]
                    })
        
        return findings
