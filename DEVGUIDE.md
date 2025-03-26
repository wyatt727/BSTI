# Developer Guide for Contributing Modules

## Introduction

This guide is intended for developers who wish to contribute modules to the Bulletproof Solutions Testing Interface (BSTI). Modules are standalone scripts that can be executed within the BSTI environment. They can be written in Bash, Json or Python.

## Module Structure

Each module should follow a specific structure for compatibility with the BSTI system. This structure includes metadata sections for file requirements and command-line arguments.

### Bash Script Structure

```bash
#!/bin/bash
# STARTFILES
# file1.txt "Description for file1"
# ENDFILES
# ARGS
# ARG1 "Description for ARG1"
# ENDARGS
# AUTHOR: Your Name

# Script Logic Here
```

### Python Script Structure

```python
#!/usr/bin/env python3
# STARTFILES
# file1.txt "Description for file1"
# ENDFILES
# ARGS
# ARG1 "Description for ARG1"
# ENDARGS
# AUTHOR: Your Name

# Script Logic Here
```

### Json Script Structure
```json
{
    "grouped": true,
    "tabs": [
        {
            "name": "Tab Name 1",
            "command": "echo 'Tab 1'"
        },
        {
            "name": "Tab Name 2",
            "command": "echo 'Tab 2'"
        },
        {
            "name": "Tab Name 3",
            "command": "echo 'Tab 3'"
        }
    ]
}

```

## Metadata Explanation

- `STARTFILES`/`ENDFILES`: Encloses the file requirement metadata. Each line within this section should list a file name followed by a description. These files will be requested from the user and uploaded to the drone before script execution.
  
- `ARGS`/`ENDARGS`: Encloses the argument metadata. Each argument should be defined on a separate line, with the argument name followed by a description. These arguments will be requested from the user at runtime.

- `AUTHOR`: Specify the author's name for the script.

## Writing a Module

When writing a module, ensure you follow the above structure. Place your script logic after the metadata sections. For Bash scripts, use shell commands, and for Python scripts, standard Python syntax.

### Example Bash Module

```bash
#!/bin/bash
# STARTFILES
# targets.txt "List of IP addresses or hostnames to target"
# ENDFILES
# ARGS
# TIMEOUT "Timeout duration in seconds"
# ENDARGS
# AUTHOR: Johnny Test

# Script Logic
for target in $(cat /tmp/targets.txt); do
    ping -c 1 -W $TIMEOUT $target
done
```

### Example Python Module

```python
#!/usr/bin/env python3
# STARTFILES
# config.json "Configuration file in JSON format"
# ENDFILES
# ARGS
# MODE "Operation mode (e.g., 'test' or 'deploy')"
# ENDARGS
# AUTHOR: Johnny Test

import sys
import json

# Script Logic
with open('/tmp/config.json', 'r') as file:
    config = json.load(file)

print(f"Running in {sys.argv[1]} mode with config: {config}")
```

### Tmux integration: Bash Script Template
Below is a template for a Bash script that executes a command in a tmux session:

```bash
#!/bin/bash
# ARGS
# PORT "Desired port for netcat"
# ENDARGS
# AUTHOR: Your Name
# This script starts a Netcat listener inside a tmux session

# Define your tmux session name and Netcat listening port
TMUX_SESSION="nc_listener"
NC_PORT=$1

# Check if the tmux session already exists
if tmux has-session -t $TMUX_SESSION 2>/dev/null; then
    echo "Session $TMUX_SESSION already exists."
    echo "Use 'tmux attach -t $TMUX_SESSION' to interact with the session."
else
    echo "Creating new tmux session named $TMUX_SESSION and starting Netcat listener on port $NC_PORT..."
    # Create a new tmux session and run Netcat
    tmux new-session -d -s $TMUX_SESSION "nc -lvnp $NC_PORT"
    echo "Netcat listener started in tmux session $TMUX_SESSION on port $NC_PORT"
    echo "Use 'tmux attach -t $TMUX_SESSION' or the UI to interact with the session."
fi
```

You can then interact with the UI under "terminal > connect to tmux session" then select the named session from the dropdown list.

### Example Module with Nessus Mapping
```bash
#!/bin/bash
# NESSUSFINDING
# SSH Server CBC Mode Ciphers Enabled
# ENDNESSUS
# ARGS
# TARGET "Target as a string"

TARGET=$1
nmap --script ssh2-enum-algos $TARGET 
```

## Additional Notes

### PlexTrac Integration

As of the latest update, the PlexTrac integration functionality (creating reports and exporting findings) has been moved from a separate PlexTrac tab to the Plugin Manager tab. This consolidation improves workflow by keeping plugin management and PlexTrac export within the same interface.

The core functionality remains the same:
- **Create PlexTrac Report** - Creates a new report in PlexTrac
- **Export to PlexTrac** - Exports findings to an existing PlexTrac report

## Contributing Your Module

To contribute your module:

1. Fork the BSTI repository.
2. Add your module script to the appropriate directory (`/modules`).
3. Create a pull request with a brief description of your module and its functionality.

Your module will be reviewed by the BSTI maintainers and, upon approval, integrated into the system.

## Removing ANSI Color Codes

Currently BSTI doesn't handle the ANSI characters that are responsible for color coding text on linux. For interactive programs or ones that have continuous output (like responder) there is no workaround currently that we're aware of...  

However, if you use BSTI to take a screenshot of the log - the ANSI characters will be automatically stripped.

For programs/commands with a static output; you can strip the ANSI codes from the output with the following syntax. Simply pipe your command into the following:
```
| sed 's/\x1b\[[0-9;]*m//g'
```
As an example, here is how you might use this with a metasploit script:
```
msfconsole -q -x "use auxiliary/scanner/rdp/ms12_020_check; set RHOSTS $1; set RPORT 3389; run; exit" | sed 's/\x1b\[[0-9;]*m//g'
```

