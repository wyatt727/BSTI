#!/bin/bash
# ARGS
# IP "RHOSTS"
# PORT "RPORT"
# ENDARGS
# NESSUSFINDING
# SSH Server CBC Mode Ciphers Enabled
# ENDNESSUS
# AUTHOR: Mitchell Kerns

# MSF SSH Version
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_version;set RHOSTS $1; set RPORT $2; run; exit" | sed 's/\x1b\[[0-9;]*m//g'

# Nmap
sudo nmap -Pn -n -sV -p $2 $1 --script sshv1,ssh2-enum-algos
