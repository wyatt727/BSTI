#!/bin/bash
# ARGS
# IP "IP address"
# ENDARGS
# AUTHOR: Mitchell Kerns

# Check for NTP Monlist Enabled
msfconsole -q -x "use auxiliary/scanner/ntp/ntp_monlist; set RHOSTS $1; run; exit"

# Check for NTP mode 6
sudo ntpq -c rv $1 | tee ntp_query
