#!/bin/bash
# ARGS
# DC_IP "Domain Controller IP Address"
# Domain "FQDN of domain: prod.example.local"
# Username "Valid User on domain"
# Password "Password (escape bad chars with \)"
# ENDARGS
# AUTHOR: Mitchell Kerns

DC_IP="$1"
Domain="$2"
User="$3"
Pass="$4"

# Construct the command using an array
# Here, use double quotes for variables but single quotes around the whole username:password part
cmd=("sudo" "python3" "/usr/share/doc/python3-impacket/examples/GetADUsers.py" "-dc-ip" "$DC_IP" "$Domain/$User:'$Pass'" "-all")

# Echo the command
echo "Running command: ${cmd[@]}"

# Execute the command
"${cmd[@]}"