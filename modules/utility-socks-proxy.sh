#!/bin/bash
# ARGS
# Port "Port for socks proxy to use"
# ENDARGS
# AUTHOR: Mitchell Kerns

# Check if a port number is passed as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 [port]"
    exit 1
fi

TMUX_SESSION="socks_proxy"
PORT=$1

# Retrieve the IP address of eth0
IP_ADDR=$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
echo "Using IP:" $IP_ADDR
# Check if IP address was found
if [ -z "$IP_ADDR" ]; then
    echo "IP address for eth0 could not be found."
    exit 1
fi

# Backup the existing proxychains4.conf file
sudo cp /etc/proxychains4.conf /etc/proxychains4.conf.backup

# Update the proxychains4.conf file
# This will remove the last line (which should be the proxy configuration) and append the new configuration
sudo sed -i '$d' /etc/proxychains4.conf
echo "socks4 $IP_ADDR $PORT" | sudo tee -a /etc/proxychains4.conf > /dev/null

# Create or update the Metasploit resource script
echo "use auxiliary/server/socks_proxy" > start_socks.rc
echo "set SRVPORT $PORT" >> start_socks.rc
echo "set SRVHOST eth0" >> start_socks.rc
echo "set VERSION 4a" >> start_socks.rc
echo "run" >> start_socks.rc

# Check if the tmux session already exists
if tmux has-session -t $TMUX_SESSION 2>/dev/null; then
    echo "Session $TMUX_SESSION already exists."
    echo "Use 'tmux attach -t $TMUX_SESSION' to interact with the session."
else
    echo "Creating new tmux session named $TMUX_SESSION and starting socks proxy on port $PORT..."
    # Create a new tmux session and run Netcat
    tmux new-session -d -s $TMUX_SESSION "msfconsole -r start_socks.rc"
    echo "Socks Proxy started in tmux session $TMUX_SESSION on port $PORT"
    echo "Use 'tmux attach -t $TMUX_SESSION' or the UI to interact with the session."
fi
