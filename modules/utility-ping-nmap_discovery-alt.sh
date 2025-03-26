#!/bin/bash
# STARTFILES
# targets.txt "Target file"
# ENDFILES
# AUTHOR: Mitchell Kerns

sudo nmap -n -sn -iL /tmp/targets.txt -oG - | awk '/Up$/{print $2}' > /tmp/up.txt
echo "Total number of hosts is:"
ls /tmp/up.txt
wc -l /tmp/up.txt