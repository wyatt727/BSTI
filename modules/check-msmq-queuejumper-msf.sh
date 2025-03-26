#!/bin/bash
# ARGS
# IP "IP address"
# ENDARGS
# AUTHOR: Mitchell Kerns

# Check with MSF
msfconsole -q -x "use auxiliary/scanner/msmq/cve_2023_21554_queuejumper; set RHOSTS $1; run; exit" | sed 's/\x1b\[[0-9;]*m//g'

