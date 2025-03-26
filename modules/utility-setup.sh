#!/bin/bash
# Author: Mitchell Kerns, Connor Fancy

# Function to check network connectivity
check_network_connection() {
    # Attempt to ping a reliable host
    if ! ping -c 1 google.com > /dev/null 2>&1; then
        echo "Network connection is not available. Please check your connection."
        exit 1
    fi
}

# Function for a progress bar (Doesn't do anything, it just gives the user a false sense of progress) 
#progress_bar() {
#    local duration=${1}
#    
#    for ((i=0; i<duration; i++)); do
#        echo -n "."  # Print a dot without a newline
#        sleep 1
#    done
#    echo  # Add a newline after the loop completes
#}

# Check for network connection
check_network_connection

# Update package lists silently
echo "Updating package lists..."
sudo apt-get update -y -qq > /dev/null 2>&1
echo "Package lists updated."
echo

# Install Docker and pull the pcredz Docker image silently
echo "Installing Docker and Eyewitness"
sudo apt-get install -y -qq docker.io eyewitness > /dev/null 2>&1
sudo docker pull snovvcrash/pcredz > /dev/null 2>&1
echo "Done. Moving on..."
echo

# Edit Responder.conf
echo "Configuring Responder.conf"
echo
sudo sed -i 's/^SMB = On/SMB = OFF/' /etc/responder/Responder.conf
sudo sed -i 's/^HTTP = On/HTTP = OFF/' /etc/responder/Responder.conf
echo "Done. Moving on..."
echo

# Install SNMP MIB downloader and configure SNMP silently
echo "Installing and configuring snmp-mibs-downloader"
sudo apt-get install -y -qq snmp-mibs-downloader > /dev/null 2>&1
sudo download-mibs > /dev/null 2>&1
sudo sed -i '/^mibs :/s/^/#/' /etc/snmp/snmp.conf
echo "Done. Moving on..."
echo

# Update Metasploit silently
echo "Updating metasploit"
sudo apt install -y -qq metasploit-framework > /dev/null 2>&1
echo "Done. Moving on..."
echo

# Install Python packages
echo "Installing mitm6 and httpx"
python3 -m pip install mitm6 > /dev/null 2>&1

python3 -m pip install httpx > /dev/null 2>&1
echo "Done."
echo

echo "Setup complete."
