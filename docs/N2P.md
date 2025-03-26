---
layout: default
title: Nessus2Plextrac
nav_order: 5
---

# Usage
If you prefer to use the tools from the commandline instead of within BSTI, the repo offerers standalone scripts for execution - the help for n2p-ng is below.


## 📍 Overview

This project is a overhaul of the original "Nessus2Plextrac". It aims to automate the process of uploading and processing Nessus vulnerability scan results to the PlexTrac platform. It provides core functionalities such as authentication, converting Nessus files to a PlexTrac-compatible format, uploading files and screenshots, updating descriptions for flaws, and adding custom fields. By automating these tasks, the project saves time for security teams, improves the accuracy of vulnerability reporting, and enhances the productivity of security operations.

---
## ⚠️ Disclaimer
### Limitation of Liability

This script is designed to automate aspects of the reporting process for the Plextrac platform. While it aims to streamline and simplify routine tasks, it does not replace or diminish the need for professional judgment and expertise in evaluating and verifying the findings.

### Manual Verification

It is strongly recommended that users conduct a comprehensive manual review of all automated outputs to validate their accuracy and completeness.

### Key Changes
This version of the script is intended to be used on a fresh report. If issues arise during the import process, delete all the current findings matching the scope you are trying to import and try again.

If that fails then create a new report or worst case a new client.


---

## ⚡️ Key Improvements
> - Conflict-Free Findings: No more conflicts between internal and external findings.
> - CSV over .nessus: Transitioned to the CSV file format, moving away from .nessus.
> - Automated Screenshot Uploads: Integrated seamlessly with NMB.
> - Enhanced Non-core Findings: Every uploaded non-core finding now has custom fields and tags preconfigured.
> - Optimized Performance: Significant improvements in execution time.
> - Client/Report Creation: Added the ability to create clients/reports from the command line.
> - Smart Filtering: Informational findings are excluded by default, removing the need for deletions.
> - Object-Oriented Refactor: The entire codebase is now object-oriented, making it more maintainable and encouraging collaboration.
> - Efficient Processing: The majority of resource-intensive tasks are executed before the file upload.

---

## ⚙️ Features

### 📸 Screenshot Uploads
---

To ensure a successful match between a screenshot and its corresponding flaw in Plextrac, it's crucial to follow a specific naming convention for your screenshot files.

***Note***: Any screenshots gathered by NMB will already be in this format.

#### File Format:
The screenshot files must be in PNG format.

#### File Naming:
The filename for each screenshot must be an MD5 hash. This hash should be the lowercase version of the corresponding plugin name as it appears in Nessus.

By adhering to this naming convention, the script will be able to accurately associate each screenshot with the appropriate flaw in Plextrac.

`Example`:

> - nessus plugin name: `web application potentially vulnerable to clickjacking`

> - md5 hash: `bc0f91e658f2a774e9861b84201ef6fd`



---

### 🛠️ Non-core Custom Fields

---
If the arg "-nc" is passed to the script, it will create the required custom fields and tags for non-core. 

`Example`: Default Data

> **Label**: Title of the recommendation - Short Recommendation

> - **Value:** FIXME

> **Label:** Recommendation owner (who will fix the finding)

> - **Value:** Systems Administrator

***Note:*** These will be the default values for every custom field added, fill in as you see fit.

---
### 🏷️ Non-core Tagging
---

Tags will be assigned based on severity rating. They can be manually customized if required.

`Example`: **Finding severity => High**

> priority_high

> complexity_complex

***Note:*** This is currently the best implementation based on the information provided, it is **HIGHLY** recommended for the user to review these tags and apply the correct context.

---
### 🔄 Internal / External Mode

---

When selecting between `-s internal/external` if the user selects "external" then every external finding will have a title prefix of (External). This can be removed by the user after script execution, but is required to help match the screenshots to the finding and prevent conflicts.


---

### 🎮 Using nessus2plextrac-ng


#### Create a report/client
```sh
python3 n2p_ng.py --create -t report-new -u user.name@email.com -p 'mypassword'
>>> Select from the list of templates and custom fields
>>> Follow along with the prompts to create a client/report
>>> keep note of client/report IDs for later use (when you want to add data to the report)
```

#### Simulate findings imports / add non-merged plugins

```bash
python3 plugin_manager.py -f <path_to_csv_file>
```
#### standard usage with screenshots
```sh
python3 n2p_ng.py -u user.name@email.com -p 'myPassWORD' -c <clientID> -r <reportID> -s external/internal -d /path/to/csv/directory -t report/report-new -ss /path/to/screenshots
```
#### Non-core usage with screenshots
```sh
python3 n2p_ng.py -u user.name@email.com -p 'myPassWORD' -c <clientID> -r <reportID> -s external/internal -d /path/to/csv/directory -t report/report-new -ss /path/to/screenshots -nc
```

#### Standard usage without screenshots
```sh
python3 n2p_ng.py -u user.name@email.com -p 'myPassWORD' -c <clientID> -r <reportID> -s external/internal -d /path/to/csv/directory -t report/report-new
```

---

### ❓ Usage Help



```sh
usage: nessus2plextrac-ng.py [-h] [-u USERNAME] [-p PASSWORD] [-c CLIENT_ID]
                             [-r REPORT_ID] [-s {internal,external}] [-d DIRECTORY]
                             [-t {report,report-new}] [-ss SCREENSHOT_DIR] [-nc]
                             [--create]

Import Nessus scans files in Plextrac while regrouping findings

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        User's plextrac username
  -p PASSWORD, --password PASSWORD
                        User's plextrac password
  -c CLIENT_ID, --clientID CLIENT_ID
                        Client ID in plextrac
  -r REPORT_ID, --reportID REPORT_ID
                        Report ID in plextrac
  -s {internal,external,web,mobile,surveillance}, --scope {internal,external,web,mobile,surveillance}
                        Scope/Tag to add to the imported finding ("internal" or "external")
                        
  -d DIRECTORY, --directory DIRECTORY
                        Directory/Folder where to find the Nessus CSV file[s]
  -t {report,report-new}, --targettedplextrac {report,report-new}
                        Targetted server [report] or [report-new]
  -ss SCREENSHOT_DIR, --screenshot_dir SCREENSHOT_DIR
                        Path to the directory containing the screenshots
  -nc, --noncore        Add non-core custom fields to findings
  --create              Prompt for client/report creation
  -cf CLIENT_CONFIG, --client_config CLIENT_CONFIG
                        Path to the TOML configuration file for client settings
```
```

---

## 🔧 Customization

Did the script not merge a finding correctly? Introducing plugin_manager.py. 

**NOTE:** It is recommended to run this script before the import.

### Overview

This script serves as a plugin manager that allows you to perform various tasks such as:
- Adding plugins to categories (Temporarily)
- Simulating which findings will be merged and which will be individual
- Viewing the current changes
- Writing the temp changes to `config.json`
- Clearing the temporary changes

The script reads from a `config.json` file to obtain the current list of plugins and categories. It also reads from a user-provided CSV file to identify findings that can be merged or remain individual.

### Usage

To run the script, use the following command:

```bash
python plugin_manager.py -f <path_to_csv_file>
```

Replace `<path_to_csv_file>` with the full path to your nessus CSV file.

### Actions

Here is what each action does:

- **Add Plugin**: Temporarily adds a plugin to a category. You will need to use 'Write Changes' to save it permanently.
- **Simulate Findings**: Simulates and displays what the merged and individual findings would be based on the CSV file.
- **View Changes**: Displays the current changes that have been made during this session.
- **Write Changes**: Writes all the current changes to `config.json`.
- **Clear Changes**: Clears all temporary changes made during this session.
- **Exit**: Exits the application, providing an option to save changes if any are pending.




## 🐞 Troubleshooting
While this project attempts to be as clean as possible, issues will arise. Here are some troubleshooting steps.

1. Remove any statefiles (.pkl) from the script directory.
2. Pull the latest version of the project. 
3. Ensure you are using .CSV files instead of .nessus
4. create a new client and report
5. ensure your screenshots either were produced by NMB or are the lowercase md5 hash of the plugin name as per nessus.
6. Re-read this README.
7. If required; reach out to Connor Fancy with questions and provide your CSV file.

---

## FAQ
### What to do with multiple CSV files?
The workflow for projects with multiple csv files **OF THE SAME SCOPE** should look like this: 

0. Don't upload findings gradually, import them all in one batch after all the scans have finished.
1. place all the csv files into one directory - make sure you seperate internal and external into their own directories.
2. place all the screenshots into one directory (yes this will overwrite but that is okay)
3. run the script as normal

### What does this script do that the old one doesn't?
#### Additions
- create clients/reports
- heavy processing is done locally rather than on plextrac's side.
- automatic screenshot upload
- addition of non-core custom fields and tags
- no more external/internal finding conflicts
- executes in a fraction of the time.

#### Removals
- CSV file format instead of .nessus 
- No longer "fixes" existing findings in plextrac, the idea is that everything can be done in one fresh execution.
  - meaning if you have a finding in plextrac with 50 assets and then upload another csv over it, it will not add assets to that existing finding, instead it will create a new finding since all flawIDs are now random.

### Is this script different than NMB?
Yes, this script is used to import results from nessus scans not verify or execute them. The flow is like this:
1. use nmb to launch nessus scans 
2. use nmb to export nessus scan results
3. use nmb to verify nessus findings and gather automatic screenshots
4. use nessus2plextrac-ng to create a client/report in plextrac
5. use nessus2plextrac-ng to import nessus results and screenshots gathered by NMB
6. touch up the report as needed and don't forget to crop screenshots after exporting

---

## 👏 Acknowledgments

> - `ℹ️  https://github.com/rouxn-bsi/reporting-toolset/tree/main/Nessus2Plextrac`

---
