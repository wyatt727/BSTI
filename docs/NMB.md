---
layout: default
title: NMB
nav_order: 6
---

# Usage
If you prefer to use the tools from the commandline instead of within BSTI, the repo offerers standalone scripts for execution - the help for NMB is below.

```bash
usage: nmb.py [OPTIONS]

options:
  -h, --help            show this help message and exit
  -m {deploy,create,launch,pause,resume,monitor,export,external,internal,regen}, --mode {deploy,create,launch,pause,resume,monitor,export,external,internal,regen}
                        choose mode to run Nessus:
                        deploy: update settings, upload policy file, upload targets file, launch scan, monitor scan, export results, analyze results
                        create: update settings, upload policy file, upload targets files
                        launch: launch scan, export results, analyze results
                        pause: pause scan
                        resume: resume scan, export results, analyze results
                        monitor: monitor scan
                        export: export scan results, analyze results
                        external: perform nmap scans, manual finding verification, generate external report, take screenshots
                        internal: perform nmap scans, manual finding verification, generate internal report, take screenshots
                        regen: Regenerates 'NMB_config.json'
  -u USERNAME, --username USERNAME
                        Username for the drone
  -p PASSWORD, --password PASSWORD
                        Password for the drone
  --targets-file TARGETS_FILE
                        Path to the txt file
  --csv-file CSV_FILE   Path to the csv file
  -d DRONE, --drone DRONE
                        drone name or IP
  -c CLIENT, --client-name CLIENT
                        client name or project name (used to name the scan and output files)
  -s {core,nc,custom}, --scope {core,nc,custom}
                        Specify if core, custom or non-core policy file
  -e EXCLUDE_FILE, --exclude-file EXCLUDE_FILE
                        exclude targets file
  -ex, --external       Enable external mode
  -l, --local           run manual checks on your local machine instead of over ssh
  --discovery           Enable discovery scan prior to running nessus.

Example:
nmb.py -d storm -c myclient -m deploy -s core -u bstg -p password --csv-file path/to/csv
```