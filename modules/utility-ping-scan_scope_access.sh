#!/bin/bash
# STARTFILES
# targets.txt "Target file description"
# ENDFILES
# AUTHOR: Mitchell

# Description: Takes a list of subnets in a txt file, performs a ping scan against them, and identifies any subnets that are reachoable or unreachable.

# Default file containing subnets
DEFAULT_SUBNETS_FILE="targets.txt"

# Check if a file name is provided as an argument
if [ "$#" -eq 1 ]; then
    SUBNETS_FILE="$1"
else
    SUBNETS_FILE=$DEFAULT_SUBNETS_FILE
fi

# Function to scan a single subnet
scan_subnet() {
    subnet=$1
    echo "Scanning $subnet..."
    
    # Perform a simple ping scan
    if sudo nmap -sn -n $subnet | grep -q "Host is up"; then
        echo -e "Active hosts found in $subnet"
    else
        echo -e "No active hosts found in $subnet"
    fi
}

# Check if the subnet file exists
if [ ! -f "$SUBNETS_FILE" ]; then
    echo "Subnet file not found: $SUBNETS_FILE"
    exit 1
fi

# Read each line in the file and scan
while IFS= read -r subnet; do
    scan_subnet "$subnet"
done < "$SUBNETS_FILE"
