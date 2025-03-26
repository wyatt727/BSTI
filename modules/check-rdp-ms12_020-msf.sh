#!/bin/bash
# ARGS
# IP "RHOSTS"
# ENDARGS
# AUTHOR: Mitchell Kerns
# Description: Check for ms12-020 without exploiting using msf.

# MSF Check
msfconsole -q -x "use auxiliary/scanner/rdp/ms12_020_check; set RHOSTS $1; set RPORT 3389; run; exit" | sed 's/\x1b\[[0-9;]*m//g'
