---
layout: default
title: Devguide
nav_order: 4
---

# Developer Guide for Contributing Modules

## Introduction

This guide is intended for developers who wish to contribute modules to the Bulletproof Solutions Testing Interface (BSTI). Modules are standalone scripts that can be executed within the BSTI environment. They can be written in Bash, Python, or JSON.

## New Module Development System

BSTI is implementing an enhanced module development system with the following improvements:

1. **GUI-Based Module Editor** - A dedicated interface for creating and editing modules
2. **Structured Metadata** - Moving from comment-based metadata to a structured format
3. **Real-time Validation** - Automatic checks for metadata correctness and syntax
4. **Module Templates** - Pre-defined templates for common module types
5. **Improved Python Module Support** - Better management of Python dependencies

### Current Module Structure (Legacy)

Until the new system is fully implemented, modules should follow the existing structure with metadata sections for file requirements, command-line arguments, and other information embedded in comments.

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

## Module Metadata

### Current Metadata Format (Legacy)

Metadata is currently defined through comment sections within module files:

- `STARTFILES`/`ENDFILES`: List of required files with descriptions
- `ARGS`/`ENDARGS`: Command-line arguments with descriptions
- `AUTHOR`: Module author information
- `NESSUSFINDING`/`ENDNESSUS`: Nessus finding mapping information

### New Metadata Format (Coming Soon)

The new system will support structured metadata in separate companion files (`module_name.meta`) using YAML or JSON format. These files will contain all metadata previously defined in comments, plus additional fields for:

- Module description
- Version information
- Dependencies
- Target platforms
- Minimum BSTI version
- Categories/tags for improved searchability

Example of a future metadata file (YAML format):
```yaml
name: "SSH CBC Mode Detection"
description: "Detects SSH servers with CBC mode ciphers enabled"
version: "1.0"
author: "Johnny Test"
files:
  - name: "targets.txt"
    description: "List of IP addresses or hostnames to target"
arguments:
  - name: "TIMEOUT"
    description: "Timeout duration in seconds"
    default: "5"
nessus_findings:
  - "SSH Server CBC Mode Ciphers Enabled"
dependencies:
  - "nmap >= 7.80"
categories:
  - "network"
  - "ssh"
  - "encryption"
```

## Using the Module Editor

### Current Editor (Legacy)

The existing Module Editor tab allows basic editing and execution of modules:

1. Select a module from the dropdown menu
2. Edit the module code as needed
3. Save changes with the "Save Module" button
4. Execute with the "Execute Module" button

### Enhanced Module Editor (Coming Soon)

The new Module Editor will provide:

1. Structured forms for editing metadata
2. Template selection for new modules
3. Real-time validation and syntax checking
4. Improved code editor with better syntax highlighting
5. Module categorization and tagging system
6. One-click execution with argument validation

## Module Development Best Practices

1. **Clear Documentation**: Include detailed descriptions in all metadata fields
2. **Robust Error Handling**: Validate inputs and handle errors gracefully
3. **Consistent Output Format**: Follow standard output conventions for better log processing
4. **Modularity**: Break down complex tasks into smaller, reusable functions
5. **Testing**: Test your module thoroughly in various scenarios
6. **Security**: Never hardcode sensitive information like credentials

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

## Contributing Your Module

### Current Process (Legacy)

To contribute using the current system:

1. Fork the BSTI repository
2. Add your module script to the appropriate directory (`/modules`)
3. Ensure proper metadata formatting within comments
4. Create a pull request with a description of your module

### Future Contribution Process

Once the new system is implemented:

1. Fork the BSTI repository
2. Use the in-app Module Editor to create your module
3. Export both the script and metadata files
4. Add these files to your fork
5. Create a pull request with a description of your module

## Migration Guide (Coming Soon)

As we transition to the new system, we will provide:

1. Support for both formats during the transition period
2. A conversion tool to migrate legacy modules to the new format
3. Documentation for manually migrating complex modules

Stay tuned for updates on the implementation timeline and migration process.

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

