#!/bin/bash
# ARGS
# PORT "Desired port for netcat"
# ENDARGS
# AUTHOR: Connor Fancy
# This script starts a Netcat listener inside a tmux session

# Define your tmux session name and Netcat listening port
TMUX_SESSION="nc_listener"
NC_PORT=$1

# Check if the tmux session already exists
if tmux has-session -t $TMUX_SESSION 2>/dev/null; then
    echo "Session $TMUX_SESSION already exists."
    echo "Use 'tmux attach -t $TMUX_SESSION' to interact with the session."
else
    echo "Creating new tmux session named $TMUX_SESSION and starting Netcat listener on port $NC_PORT..."
    # Create a new tmux session and run Netcat
    tmux new-session -d -s $TMUX_SESSION "nc -lvnp $NC_PORT"
    echo "Netcat listener started in tmux session $TMUX_SESSION on port $NC_PORT"
    echo "Use 'tmux attach -t $TMUX_SESSION' or the UI to interact with the session."
fi

