# BSTI Nessus Management Buddy (NMB)

## Overview
NMB is a powerful tool for managing Nessus vulnerability scanning operations. It provides various modes for deploying, creating, launching, pausing, resuming, monitoring, and exporting Nessus scans, as well as performing internal and external security assessments.

This implementation integrates the BSTI Nessus utility modules to enhance functionality including:
- Secure credential management
- Configuration wizard
- Progress tracking
- Parallel processing

## Installation

### Prerequisites
- Python 3.6 or higher
- Nessus scanner access
- Required Python packages (install from requirements.txt)

### Setup
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the setup script for your platform:
```bash
# For Linux/macOS
./install.sh

# For Windows
.\install.bat
```

## Usage

Basic usage:
```bash
python nmb.py -m MODE [OPTIONS]
```

### Available Modes
- `deploy`: Complete workflow - update settings, upload policy file, upload targets file, launch scan, monitor scan, export results, analyze results
- `create`: Update settings, upload policy file, upload targets files
- `launch`: Launch scan, export results, analyze results
- `pause`: Pause scan
- `resume`: Resume scan, export results, analyze results
- `monitor`: Monitor scan
- `export`: Export scan results, analyze results
- `external`: Perform nmap scans, manual finding verification, generate external report, take screenshots
- `internal`: Perform nmap scans, manual finding verification, generate internal report, take screenshots
- `regen`: Regenerate 'NMB_config.json'

### Common Options
- `-u, --username`: Username for the drone
- `-p, --password`: Password for the drone
- `-d, --drone`: Drone name or IP
- `-c, --client-name`: Client name or project name (used to name the scan and output files)
- `-s, --scope`: Specify if core, custom or non-core policy file (choices: "core", "nc", "custom")
- `-e, --exclude-file`: Exclude targets file
- `-l, --local`: Run manual checks on your local machine instead of over SSH
- `--discovery`: Enable discovery scan prior to running Nessus
- `--targets-file`: Path to the txt file containing targets
- `--csv-file`: Path to the CSV file
- `--config-wizard`: Launch the configuration wizard
- `--store-credentials`: Securely store provided credentials for future use
- `--parallel`: Enable parallel processing for faster execution

## Enhanced Features

### Configuration Wizard
The configuration wizard provides an interactive step-by-step process to configure the NMB tool:

```bash
python nmb.py --config-wizard
```

The wizard will guide you through the configuration process, allowing you to set up:
- Nessus scanner connection details
- Authentication credentials
- Default scan templates
- Output formats and locations
- Notification settings

### Secure Credential Management
NMB now securely stores credentials using platform-specific secure storage:
- macOS: Keychain
- Windows: Windows Credential Manager
- Linux: Secret Service API / libsecret

To store credentials:
```bash
python nmb.py -u USERNAME -p PASSWORD --store-credentials
```

Once stored, you can run commands without specifying credentials:
```bash
python nmb.py -m deploy -d drone1 -c client1 -s core --targets-file targets.txt
```

### Progress Tracking
All operations now include progress tracking with:
- Real-time progress indicators
- ETA calculations
- Detailed status updates

### Parallel Processing
Parallel processing can be enabled for faster execution of tasks:

```bash
python nmb.py -m deploy -d drone1 -c client1 -s core --targets-file targets.txt --parallel
```

This feature is particularly useful when:
- Processing large numbers of targets
- Performing multiple scans simultaneously
- Analyzing large result sets

## Examples

### Deploy a Core Nessus Scan
```bash
python nmb.py -m deploy -d nessus.example.com -c client_project -s core -u admin -p password --targets-file targets.txt
```

### Run Internal Security Assessment
```bash
python nmb.py -m internal -d scanner.example.com --csv-file assessment_results.csv
```

### Run Configuration Wizard and Save Settings
```bash
python nmb.py --config-wizard
```

### Monitor an Existing Scan
```bash
python nmb.py -m monitor -d nessus.example.com -c client_project
```

## Troubleshooting

### Common Issues

1. **Connection errors to Nessus scanner**:
   - Verify the scanner IP/hostname is correct
   - Check credentials
   - Ensure the scanner is running and accessible from your network

2. **Missing required arguments**:
   - Check that all required arguments for the specific mode are provided
   - Run with `--config-wizard` to configure default values

3. **Credential storage issues**:
   - Ensure you have the appropriate permissions for your platform's secure storage
   - On Linux, ensure libsecret is installed

4. **Scan pausing or hanging**:
   - Large scans may take time - check Nessus UI for detailed status
   - Use the monitor mode to track progress

## License
See the LICENSE file for details.

## Contributing
See DEVGUIDE.md for development guidelines and contribution information. 