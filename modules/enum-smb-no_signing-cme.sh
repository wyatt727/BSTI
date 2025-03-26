#!/bin/bash
# STARTFILES
# targets.txt "Target file description"
# ENDFILES
# Author: Mitchell Kerns

sudo crackmapexec smb /tmp/targets.txt --gen-relay-list targets_$(date +%F).txt
sudo cat targets_$(date +%F).txt | sort | uniq | tee smb-not-signed.txt
