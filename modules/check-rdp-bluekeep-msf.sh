#!/bin/bash
# ARGS
# IP "RHOSTS"
# PORT "RPORT"
# ENDARGS
# AUTHOR: Mitchell Kerns
# Description: Check for bluekeep without exploiting.

# MSF Check
msfconsole -q -x "use auxiliary/scanner/rdp/cve_2019_0708_bluekeep; set RHOSTS $1; set RPORT $2; run; exit" | sed 's/\x1b\[[0-9;]*m//g'
