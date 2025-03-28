#!/bin/bash
# NESSUSFINDING
# SSH Server CBC Mode Ciphers Enabled
# ENDNESSUS
# ARGS
# TARGET "Target IP address or hostname" 
# PORT "SSH port (default: 22)"
# ENDARGS
# AUTHOR: Security Tester

# Default port is 22 if not specified
PORT=${2:-22}
TARGET=$1

echo "Scanning $TARGET:$PORT for SSH CBC mode ciphers..."
echo "=================================================="
echo

# First, get SSH version information
echo "SSH Version Information:"
echo "------------------------"
nmap -p $PORT -sV --script=banner $TARGET | grep -i ssh

echo
echo "Checking for supported SSH algorithms and ciphers..."
echo "---------------------------------------------------"

# Use ssh2-enum-algos Nmap script to check for supported algorithms
nmap -p $PORT --script ssh2-enum-algos $TARGET | sed 's/\x1b\[[0-9;]*m//g'

echo
echo "Checking specifically for CBC ciphers..."
echo "---------------------------------------"

# Check if CBC ciphers are supported
CBC_OUTPUT=$(nmap -p $PORT --script ssh2-enum-algos $TARGET | grep -i cbc)

if [[ -n "$CBC_OUTPUT" ]]; then
    echo "VULNERABLE: The following CBC ciphers were detected:"
    echo "$CBC_OUTPUT" | sed 's/\x1b\[[0-9;]*m//g'
    echo
    echo "FINDING: SSH Server CBC Mode Ciphers Enabled"
    echo "IMPACT: CBC mode ciphers are vulnerable to theoretical plaintext"
    echo "        recovery attacks and the BEAST attack."
    echo "REMEDIATION: Reconfigure SSH server to disable CBC mode ciphers."
    echo "             Configure SSH to only use CTR or GCM cipher modes."
else
    echo "SECURE: No CBC mode ciphers were detected."
fi

# Additional security checks for SSH
echo
echo "Additional SSH Security Checks:"
echo "------------------------------"

# Check SSH protocol version
SSH_VERSION=$(nmap -p $PORT -sV $TARGET | grep -i ssh | grep -o -E "SSH-[0-9]\.[0-9]" | sort -u)
if [[ -n "$SSH_VERSION" ]]; then
    echo "SSH Protocol Version: $SSH_VERSION"
    if [[ "$SSH_VERSION" == "SSH-1.0" ]] || [[ "$SSH_VERSION" == "SSH-1" ]]; then
        echo "WARNING: SSH Protocol version 1 is insecure and should be disabled."
    fi
fi

# Check for other weak algorithms
echo
echo "Checking for other weak SSH algorithms..."
nmap -p $PORT --script ssh2-enum-algos $TARGET | grep -E 'arcfour|hmac-md5|hmac-sha1' | sed 's/\x1b\[[0-9;]*m//g'

echo
echo "Scan completed at $(date)" 