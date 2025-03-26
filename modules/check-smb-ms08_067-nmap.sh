#!/bin/bash
# ARGS
# IP "RHOSTS"
# ENDARGS
# AUTHOR: Mitchell Kerns
# Description: Check for ms08-067 using nmap without exploiting.

# Nmap
sudo nmap -Pn -n -sV -p 445 $1 --script smb-vuln-ms08-067
