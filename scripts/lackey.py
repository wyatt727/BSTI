import re
import subprocess
import platform
import sys
import hashlib
from filelock import FileLock
import html
import os
import pickle
from htmlwebshot import WebShot, Config
from scripts.drone import Drone
from scripts.parser import ConfigParser
from scripts.logging_config import log
from scripts.interpreter import Interpreter
from scripts.analyzer import Analyzer
import shutil
import signal

class Lackey:
    def __init__(self, csv_file, ext_scope, local_checks, username, password, drone):
        self.csv_file = csv_file
        self.ext_scope = ext_scope
        self.client_dir = os.path.splitext(self.csv_file)[0]
        self.nessus_file = os.path.splitext(self.csv_file)[0] + ".nessus"
        self.local_checks = local_checks
        self.drone = None if local_checks else Drone(drone, username, password)
        self.operating_system = platform.system()
        self.checked_plugins = set()
        self.unchecked_scripts = []
        self.failed_checks = []
        self.verified_checks = []
        self.unknown_checks = []
        self.state_pattern = re.compile(r"\d+\/\w+\s+(open|closed|filtered)\s+\w+")
        exec = ConfigParser(csv_file)
        self.nessus_data, self.json_config, self.supported_plugins, self.missing_plugins = exec.gather_data()
        self.current_host_index = 0
        self.current_csv_file_hash = self.compute_file_hash(self.csv_file)
        self.setup_signal_handlers()
        self.engine()
        self.generate_summary()
        self.gather_screenshots()
        self.generate_interpreter_data()
        # if run_eyewitness:
        #     log.info("Eyewitness enabled ...")
            # self.analyze_data()
        self.move_evidence()
        log.info("----------Execution Ended-----------")


    def move_evidence(self):
        # Get the base name without the extension
        base_name = os.path.splitext(self.csv_file)[0]
        # Define the extensions you want to move along with the csv file
        extensions_to_move = ['.csv', '.html', '.nessus']

        for ext in extensions_to_move:
            # Construct the full file name for each extension
            file_name = f"{base_name}{ext}"
            try:
                # Check if the file exists before attempting to move it
                if os.path.exists(file_name):
                    shutil.move(file_name, os.path.join(self.client_dir, os.path.basename(file_name)))
                    log.info(f"Moved {file_name} to {self.client_dir}")
                else:
                    log.warning(f"File {file_name} does not exist and cannot be moved.")
            except Exception as e:
                log.error(f"Error moving file {file_name}: {e}")

    def generate_interpreter_data(self):
        log.info("Generating interpreter data ...")
        Interpreter(self.csv_file, self.client_dir)
        log.success("Interpreter data generated successfully.")

    def analyze_data(self):
        log.info("Analyzing data with Eyewittness ...")
        analyzer = Analyzer(self.nessus_file, self.client_dir, self.drone)
        output_zip = analyzer.analyze_results()
        log.success(f"Data analyzed successfully and saved to: {output_zip}")

        
    def gather_screenshots(self):
        log.info("Gathering screenshots ...")

        for item in self.verified_checks:
            plugin_name = item[0]
            scan_type = item[8]
            parameters = item[9] 
            output = item[3]

            # Escape special characters in the cleaned output
            cleaned_output = html.escape(output)

            # Create the command string
            command_used = f"# Command used: {scan_type} {parameters}"

            # Escape special characters in the command string
            cleaned_command = html.escape(command_used)

            css = """
            body {
                background-color: #000000; /* Black background color */
                padding: 10px;
                font-family: 'Courier New', monospace;
                color: #ffffff;  /* Set the text color to white */
            }
            pre {
                white-space: pre-wrap;       /* Since CSS 2.1 */
                white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
                white-space: -pre-wrap;      /* Opera 4-6 */
                white-space: -o-pre-wrap;    /* Opera 7 */
                word-wrap: break-word;       /* Internet Explorer 5.5+ */
            }
            """

            # Create a temporary HTML file containing only the cleaned output
            html_content = f"""
            <html>
            <head>
            <style>
            {css}
            </style>
            </head>
            <body>
            <pre>{cleaned_command}</pre>
            <pre>{cleaned_output}</pre>
            </body>
            </html>
            """
            try:
                # Create an instance of WebShot
                if self.operating_system == "Windows":
                    shot = WebShot(
                        quality=100,
                        config=Config(
                            wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
                            wkhtmltoimage=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe",
                        ),
                    )
                elif self.operating_system == "Darwin":  # MacOS specific handling
                    # Check common MacOS installation paths for wkhtmltopdf
                    mac_paths = [
                        "/usr/local/bin/wkhtmltopdf",
                        "/usr/local/bin/wkhtmltoimage",
                        "/opt/homebrew/bin/wkhtmltopdf", 
                        "/opt/homebrew/bin/wkhtmltoimage"
                    ]
                    
                    # Use first path that exists
                    wkhtmltopdf_path = next((path for path in mac_paths if os.path.exists(path)), None)
                    wkhtmltoimage_path = next((path for path in mac_paths if os.path.exists(path) and "image" in path), None)
                    
                    if wkhtmltopdf_path and wkhtmltoimage_path:
                        log.info(f"Found wkhtmltopdf at {wkhtmltopdf_path}")
                        log.info(f"Found wkhtmltoimage at {wkhtmltoimage_path}")
                        shot = WebShot(
                            quality=100,
                            config=Config(
                                wkhtmltopdf=wkhtmltopdf_path,
                                wkhtmltoimage=wkhtmltoimage_path,
                            ),
                        )
                    else:
                        log.warning("Could not find wkhtmltopdf/wkhtmltoimage in common MacOS locations.")
                        log.warning("Using default configuration which may not work correctly.")
                        shot = WebShot(quality=100)
                else:
                    shot = WebShot()

                screenshot_dir = self.client_dir
                
                # The below will be used when nessus2plextrac is absorbed into this script.
                # # Generate the MD5 hash of the plugin name
                hashed_filename = hashlib.md5(plugin_name.lower().encode()).hexdigest()


                # Specify the output file path
                output_path = os.path.join(screenshot_dir, f"{hashed_filename}.png")

                # # Generate the cleaned filename
                # windows_illegal_chars = r'[<>:"/\\|?*]'
                # cleaned_filename = re.sub(windows_illegal_chars, '', f"{plugin_name}.png")

                # # Specify the output file path
                # output_path = os.path.join(screenshot_dir, cleaned_filename)

                # Save the screenshot
                shot.create_pic(html=html_content, css=css, output=output_path)

                log.success(f"Screenshots saved to: {output_path}")

            except Exception as e:
                log.error(f"An error occurred during execution: {e}")

        
    def run_scan(self, host, port, plugin_id, scan_type, parameters, drone, local_checks=False):
        """
        Run a scan on the specified host using the given scan type, parameters, and drone.

        Args:
            host (str): The target host IP address or hostname.
            port (int): The target port number.
            plugin_id (str): The ID of the plugin to run the scan.
            scan_type (str): The type of scan to perform.
            parameters (str): The parameters for the scan command.
            drone (Drone): The Drone object representing the SSH connection.
            local_checks (bool, optional): Flag indicating whether to perform local checks instead of remote execution.
                                        Defaults to False.

        Returns:
            str: The output of the scan command.

        The function constructs the scan command based on the provided parameters, host, and port.
        If the parameters do not contain '{port}', it formats the command with the host only.
        Otherwise, it formats the command with both the host and port.
        If local_checks is True, it executes the command using subprocess.check_output locally.
        Otherwise, it executes the command remotely using the Drone object's execute method.
        The function returns the output of the scan command if successful.
        If an exception occurs during the scan execution, it prints an error message and returns an empty string.
        """
        
        command = f"{scan_type} {parameters.format(host=host, port=port)}"
        
        try:
            if local_checks:
                return subprocess.check_output(command, shell=True, universal_newlines=True)
            else:
                return drone.execute(command)
        except subprocess.CalledProcessError as e:  # Replace with specific exceptions
            log.error(f"Error running scan for host {host}:{port}: {str(e)}")
            return

    

    def check_scan(self, output, verify_words):
        """
        Check the state of a scan based on the output and a list of verify words.

        Args:
            output (str): The output of the scan.
            verify_words (list): A list of words to verify in the output.

        Returns:
            str: The state of the scan: "up" if all verify words are found in the output,
                "down" if at least one verify word is missing, "unknown" if the state cannot be determined.
        """
        if not output:
            return "unknown"

        state = self.state_pattern.search(output).group(1) if self.state_pattern.search(output) else ''
        output_lower = output.lower()

        if "host timeout" in output_lower or any(word.lower() not in output_lower for word in verify_words):
            return "unknown" if state in ("filtered", "") else "down"

        return "up"
    
    def process_item(self, item, plugin_to_category, verified_findings, failed_hosts, retried_scans):
        host, port, name, plugin_id, risk, description, remedy = item

        # Skip processing if the host has failed or the finding is already verified
        if host in failed_hosts or name in verified_findings:
            return

        # Get category data for the plugin
        category_data = plugin_to_category.get(plugin_id)
        if not category_data:
            return

        category, category_data = category_data
        scan_type = category_data['scan_type']
        parameters = category_data['parameters']
        log.info(f"Testing {host}:{port} for {name}")

        output = self.run_scan(host, port, plugin_id, scan_type, parameters, self.drone, self.local_checks)
        if not output:
            return

        verify_words = category_data.get('verify_words', [])
        result = self.check_scan(output, verify_words)

        if result == "up":
            verified_findings.add(name)
            self.verified_checks.append((name, host, port, output, False, risk, description, remedy, scan_type, parameters))
            log.success(f"Verified {name}")
            return

        if result == "down":
            failed_hosts.add(host)
            self.failed_checks.append((name, host, port, output, False, scan_type, parameters))
            log.error(f"Host: {host}:{port} is down - script: {name} failed")
            return

        # If the result is unknown and the scan has not been retried yet
        retry_key = (host, plugin_id)
        if result == "unknown" and "nmap -T4 --host-timeout 300s" in scan_type and retry_key not in retried_scans:
            log.warning('Host appears down - Rerunning scan with -Pn')
            updated_output = self.run_scan(host, port, plugin_id, scan_type, f"{parameters} -Pn", self.drone, self.local_checks)

            # Mark this scan as retried
            retried_scans.add(retry_key)

            if not updated_output:
                return

            updated_result = self.check_scan(updated_output, verify_words)
            if updated_result == "up":
                verified_findings.add(name)
                self.verified_checks.append((name, host, port, updated_output, True, risk, description, remedy, scan_type, parameters))
                log.success(f"Verified {name} after re-running with -Pn")
            else:
                log.error(f"Rerunning the scan with -Pn failed for {name}")
                self.failed_checks.append((name, host, port, updated_output, True, scan_type, parameters))

        # Handling for when the scan type does not include specific parameters and result is unknown
        elif result == "unknown":
            verified_findings.add(name)
            self.unknown_checks.append((name, host, port, output, False, scan_type, parameters))
            log.warning(f"Status unknown for {name}")

    def engine(self):
        try:
            self.current_host_index, _ = self.load_initial_state()

            plugin_to_category = {
                plugin_id: (category, category_data) 
                for category, category_data in self.json_config['plugins'].items() 
                for plugin_id in category_data['ids']
            }

            verified_findings, failed_hosts, retried_scans = set(), set(), set()
            for index, item in enumerate(self.nessus_data[self.current_host_index:]):
                # Pass retried_scans to process_item
                self.process_item(item, plugin_to_category, verified_findings, failed_hosts, retried_scans)
                self.current_host_index = index + 1

            saved_state = self.get_state_filename()
            if os.path.exists(saved_state):
                os.remove(saved_state)
                log.warning("State file removed.")

        except Exception as e: 
            log.error(e) # Catch all exceptions to ensure the state is saved before exiting
            self.save_state_and_exit()

    def compute_file_hash(self, filename):
        """Compute a SHA256 hash of a file."""
        with open(filename, 'rb') as f:
            file_data = f.read()
        return hashlib.sha256(file_data).hexdigest()


    def get_state_filename(self):
        """Generate a state filename based on the hash of the csv_file."""
        hash_value = self.compute_file_hash(self.csv_file)[:10]  # Take the first 10 chars for brevity
        filename = f'state_{hash_value}.pkl'
        return 'local_' + filename if self.local_checks else filename

    def save_state(self, state):
        """Save the current state with file locking to avoid race conditions."""
        state_file = self.get_state_filename()
        lock = FileLock(f"{state_file}.lock")
        with lock:
            with open(state_file, 'wb') as f:
                pickle.dump(state, f)
        return state_file

    def load_state(self):
        """Load the saved state with file locking."""
        state_file = self.get_state_filename()
        lock = FileLock(f"{state_file}.lock")
        with lock:
            if os.path.exists(state_file):
                try:
                    with open(state_file, 'rb') as f:
                        state = pickle.load(f)
                    return state
                except FileNotFoundError:
                    return None
            else:
                return None

    def setup_signal_handlers(self):
        if sys.platform == 'win32':
            signal.signal(signal.SIGBREAK, self.signal_handler)
        else:
            signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        log.warning(f"Received signal: {signum}. Saving state and exiting...")
        self.save_state_and_exit()

    def load_initial_state(self):
        saved_state_data = self.load_state()
        current_csv_file_hash = self.compute_file_hash(self.csv_file)
        self.current_host_index = 0

        if saved_state_data:
            log.success("Previous state loaded.")
            saved_csv_file_hash = saved_state_data.get('csv_file_hash')
            if saved_csv_file_hash != current_csv_file_hash:
                log.warning("CSV file has changed since the last run. Starting from the beginning.")
            else:
                self.current_host_index = saved_state_data.get('current_host_index', 0)
                self.verified_checks = saved_state_data.get('verified_checks', [])  # Load verified checks

        return self.current_host_index, current_csv_file_hash

    def save_state_and_exit(self):
        log.warning("Saving current state...")
        state = {
            'current_host_index': self.current_host_index,
            'csv_file_hash': self.current_csv_file_hash,
            'verified_checks': self.verified_checks 
        }
        self.save_state(state)
        log.success("Current state saved. Exiting gracefully.")
        sys.exit(0)


    def generate_summary(self):
        log.info('Generating a summary ...')
        report_dir = self.client_dir
        os.makedirs(report_dir, exist_ok=True)
        if self.ext_scope:
            title = "External Report"
            html_summary = "external_summary.html"
        else:
            title = "Internal Report"
            html_summary = 'internal_summary.html'
        output_path = os.path.join(report_dir, html_summary)
        
        
        try:
            
            with open(output_path, 'w') as f:
                f.write('<html>\n')
                f.write('<head>\n')
                f.write(f'<title>{title}</title>\n')
                f.write('<style>\n')
                f.write('body {font-family: "Roboto", Arial, sans-serif; background: linear-gradient(to right, #2b5876, #4e4376); color: #ffffff; margin: 0; padding: 20px;}\n')
                f.write('h1 {font-size: 2em; margin-top: 20px; border-bottom: 2px solid #ffffff; padding-bottom: 10px;}\n')
                f.write('p, li {font-size: 1em;}\n')

                f.write('table {border-collapse: collapse; width: 100%; margin: 20px 0; box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.2);}\n')
                f.write('th, td {text-align: left; padding: 10px; border: 1px solid #666666; transition: background 0.2s;}\n')
                f.write('th {background-color: #333333; color: #ffffff; font-weight: bold;}\n')
                f.write('tr:nth-child(even) {background-color: rgba(255,255,255,0.05);}\n')
                f.write('tr:hover {background-color: rgba(255,255,255,0.1);}\n')

                f.write('.details {display: none;}\n')
                f.write('.code-block {background-color: rgba(0, 0, 0, 0.8); padding: 10px; border: 1px solid #555555; font-family: "Courier New", monospace; box-shadow: inset 0px 0px 10px rgba(0, 0, 0, 0.5);}\n')
                f.write('.output-description {display: flex; align-items: center;}\n')
                f.write('.output {flex: 1; padding-right: 10px; border-right: 1px solid #666666;}\n')
                f.write('.description {flex: 1; padding-left: 10px; align-self: flex-start;}\n')

                f.write('.vertical-line {width: 1px; background-color: #666666; height: 100%; margin-left: 10px;}\n')

                f.write('.heading {text-align: center;}\n')
                f.write('.arrow {cursor: pointer; transition: transform 0.2s;}\n')
                f.write('</style>\n')

                f.write('<script>\n')
                f.write('function toggleDetails(row) {\n')
                f.write('  var details = row.nextElementSibling;\n')
                f.write('  var arrow = row.querySelector(".arrow");\n')
                f.write('  if (details.style.display === "none") {\n')
                f.write('    details.style.display = "table-row";\n')
                f.write('    arrow.innerHTML = "&#9660;";\n')
                f.write('  } else {\n')
                f.write('    details.style.display = "none";\n')
                f.write('    arrow.innerHTML = "&#9658;";\n')
                f.write('  }\n')
                f.write('}\n')
                f.write('</script>\n')

                f.write('</head>\n')
                f.write('<body>\n')
                
                summary_descriptions = []
                for item in self.verified_checks:
                    remedy = item[7]
                    summary_descriptions.append(remedy)
                
                f.write('<h1>Executive Summary</h1>\n')
                
                f.write('<p>Summary:</p>\n')
                f.write('<ul>\n')
                for summary in summary_descriptions:
                    f.write(f'<li>{summary}</li>\n')
                f.write('</ul>\n')
                
                
                f.write('<h1>Verified Checks</h1>\n')
                f.write('<table>\n')
                f.write('<tr><th>Plugin Name</th><th>Severity Rating</th><th>Host:Port</th><th>Retry</th><th>Scan Details</th></tr>\n')
                
                for item in self.verified_checks:
                    plugin_name = item[0]
                    ip = item[1]
                    port = item[2]
                    output = item[3]
                    retry = item[4]
                    risk = item[5]
                    description = item[6]
                    scan_type = item[8]
                    parameters = item[9]
                    scan_details = f"{scan_type} {parameters}"  
                    
                    # Include scan_details in the row
                    f.write(f'<tr onclick="toggleDetails(this)"><td><span class="arrow">&#9658;</span>{html.escape(plugin_name)}</td><td>{risk}</td><td>{html.escape(ip)}:{html.escape(port)}</td><td>{retry}</td><td>{html.escape(scan_details)}</td></tr>\n')
                    f.write('<tr class="details" style="display: none;"><td colspan="6">\n')
                    f.write('<div class="code-block">\n')
                    f.write('<div class="output-description">\n')
                    f.write(f'<pre class="output">{html.escape(output)}</pre>\n') 
                    f.write('<div class="vertical-line"></div>\n')
                    f.write(f'<pre class="description">{description}</pre>\n')
                    f.write('</div>\n')
                    f.write('</div>\n')
                    f.write('</td></tr>\n')

                f.write('</table>\n')


                
                
                f.write('<h1>Unconfirmed Checks</h1>\n')
                f.write('<table>\n')
                f.write('<tr><th>Plugin Name</th><th>Host:Port</th><th>Retry</th><th>Scan Details</th></tr>\n')
    
                for item in self.unknown_checks:
                    plugin_name = item[0]
                    ip = item[1]
                    port = item[2]
                    output = item[3]
                    retry = item[4]
                    scan_type = item[5]
                    parameters = item[6]
                    scan_details = f"{scan_type} {parameters}"
                    # Include scan_details in each row
                    f.write(f'<tr onclick="toggleDetails(this)"><td><span class="arrow">&#9658;</span>{html.escape(plugin_name)}</td><td>{html.escape(ip)}:{html.escape(port)}</td><td>{retry}</td><td>{html.escape(scan_details)}</td></tr>\n')
                    f.write('<tr class="details" style="display: none;"><td colspan="4">\n')
                    f.write('<div class="code-block">\n')
                    f.write(f'<pre>{html.escape(output)}</pre>\n')
                    f.write('</div>\n')
                    f.write('</td></tr>\n')
                
                f.write('</table>\n')
                
                f.write('<h1>Failed Checks</h1>\n')
                f.write('<table>\n')
                f.write('<tr><th>Plugin Name</th><th>Host:Port</th><th>Retry</th><th>Scan Details</th></tr>\n')
    
                for item in self.failed_checks:
                    plugin_name = item[0]
                    ip = item[1]
                    port = item[2]
                    output = item[3]
                    retry = item[4]
                    scan_type = item[5] 
                    parameters = item[6]
                    scan_details = f"{scan_type} {parameters}"
                    
                    # Include scan_details in each row
                    f.write(f'<tr onclick="toggleDetails(this)"><td><span class="arrow">&#9658;</span>{html.escape(plugin_name)}</td><td>{html.escape(ip)}:{html.escape(port)}</td><td>{retry}</td><td>{html.escape(scan_details)}</td></tr>\n')
                    f.write('<tr class="details" style="display: none;"><td colspan="4">\n')
                    f.write('<div class="code-block">\n')
                    f.write(f'<pre>{html.escape(output)}</pre>\n')
                    f.write('</div>\n')
                    f.write('</td></tr>\n')
                
                f.write('</table>\n')
                
                
                

                f.write('<h1>Supported Plugins</h1>\n')
                f.write('<table>\n')
                f.write('<tr><th>Plugin Name</th></tr>\n')
                for line in self.supported_plugins:
                    f.write(f'<tr onclick="toggleDetails(this)"><td>{line}</td></tr>\n')
                    f.write('<tr class="details" style="display: none;"><td colspan="2"></td></tr>\n')
                f.write('</table>\n')

                f.write('<h1>Unchecked Plugins</h1>\n')
                f.write('<table>\n')
                f.write('<tr><th>Plugin Name</th></tr>\n')

                for item in self.missing_plugins:
                    plugin_name = item[2]
                    f.write(f'<tr onclick="toggleDetails(this)"><td>{plugin_name}</td></tr>\n')
                    f.write('<tr class="details" style="display: none;"><td colspan="2"></td></tr>\n')
                f.write('</table>\n')
                f.write('</body>\n')
                f.write('</html>\n')

        except Exception as e:
            log.error(f'Error: {e}')
            sys.exit()
        log.success(f"Summary generated at {output_path}")  