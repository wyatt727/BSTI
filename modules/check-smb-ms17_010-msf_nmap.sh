#!/bin/bash
# ARGS
# IP "RHOSTS"
# ENDARGS
# AUTHOR: Mitchell Kerns
# Description: Check for bluekeep without exploiting.

# MSF Check
msfconsole -q -x "use auxiliary/scanner/rdp/cve_2019_0708_bluekeep; set RHOSTS $1; set RPORT 445; set SMBDomain $2; run; exit" | sed 's/\x1b\[[0-9;]*m//g'

# Nmap Double-check
sudo nmap -Pn -n -sV -p 445 $1 --script smb-vuln-ms17-010
