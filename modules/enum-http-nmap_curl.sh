#!/bin/bash
# ARGS
# IP "RHOST"
# Port "RPORT"
# ENDARGS
# AUTHOR: Mitchell Kerns

echo "---------------------------------------Checking with nmap---------------------------------------------------------------"
# Try Nmap
sudo nmap -Pn -n -sV -p $2 $1 --script http-enum,http-headers

echo "---------------------------------------Checking with curl---------------------------------------------------------------"

# Try Curl
# IP address or hostname to check
IP="$1"
# Port number to check
PORT="$2"

# Function to check HTTP
check_http() {
    if curl -s --head "http://$IP:$PORT" | head -n 1 | grep "200 OK" > /dev/null; then
        echo "HTTP is available on port $PORT"
        curl "http://$IP:$PORT"
    else
        echo "HTTP is not available on port $PORT"
    fi
}

# Function to check HTTPS
check_https() {
    if curl -s --head "https://$IP:$PORT" --insecure | head -n 1 | grep "200 OK" > /dev/null; then
        echo "HTTPS is available on port $PORT"
        curl "https://$IP:$PORT" --insecure
    else
        echo "HTTPS is not available on port $PORT"
    fi
}

# Check if port number is provided
if [ -z "$PORT" ]; then
    echo "Error: No port number provided."
    echo "Usage: $0 [IP_or_hostname] [port]"
    exit 1
fi

# First, try HTTPS
echo "Checking HTTPS on port $PORT..."
if check_https; then
    exit 0
fi

# If HTTPS fails, try HTTP
echo "Checking HTTP on port $PORT..."
check_http
