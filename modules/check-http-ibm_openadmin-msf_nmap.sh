#!/bin/bash
# ARGS
# IP "RHOST"
# Port "RPORT"
# SSL "True or False"
# ENDARGS
# AUTHOR: Mitchell Kerns

# Nmap
sudo nmap -Pn -n -sV -p $2 $1 --script http-enum,http-headers

# MSF
msfconsole -q -x "use exploit/multi/http/ibm_openadmin_tool_soap_welcomeserver_exec; set RHOSTS $1; set RPORT $2; set SSL $3; check; exit" | sed 's/\x1b\[[0-9;]*m//g'
