#!/bin/bash
# ARGS
# IP ""
# Port ""
# ENDARGS
# AUTHOR: Mitchell Kerns 

sudo nmap -Pn -n -sV -p $2 $1 --script ssl-cert,ssl-enum-ciphers,ssl-dh-params,sslv2
