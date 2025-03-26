#!/bin/bash
# AUTHOR: Connor Fancy
# STARTFILES
# targets.txt "Targets file"
# exclude.txt "Exclude file"
# ENDFILES

TMUX_SESSION="nmap_discovery_scan"
TARGETS_FILE="/tmp/targets.txt"
EXCLUDE_FILE="/tmp/exclude.txt"
OUTPUT_FILE="/tmp/nmap_results.txt"  # Define the output file for Nmap results

# Check if the tmux session already exists
if tmux has-session -t $TMUX_SESSION 2>/dev/null; then
    echo "Session $TMUX_SESSION already exists."
    echo "Use 'tmux attach -t $TMUX_SESSION' to interact with the session."
else
    echo "Creating new tmux session named $TMUX_SESSION and starting Nmap scan..."

    # Define the nmap command with proper escaping and preceding echo statement
    NMAP_CMD="echo 'Starting Nmap Scan...'; "
    NMAP_CMD+="sudo nmap -n -sn -iL $TARGETS_FILE"
    if [ -s "$EXCLUDE_FILE" ]; then
        NMAP_CMD+=" --excludefile $EXCLUDE_FILE"
    fi
    NMAP_CMD+=" -oG $OUTPUT_FILE | awk '/Up\$/{print \$2}'; bash"  # Save the output to the file and extract IPs

    # Create a new tmux session and run the Nmap command
    tmux new-session -d -s $TMUX_SESSION "$NMAP_CMD"
    echo "Nmap scan started in tmux session $TMUX_SESSION."
    echo "Use 'tmux attach -t $TMUX_SESSION' or the UI to interact with the session."
    echo "Scan results will be saved in $OUTPUT_FILE."
fi
