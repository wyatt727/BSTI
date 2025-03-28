#!/usr/bin/env python3
"""
BSTI Module Template - Network Listener
This is a template for creating network listener modules in BSTI
"""

# STARTFILES
# config.json "Configuration file in JSON format with listener settings"
# ENDFILES
# ARGS
# PORT "Port number to listen on"
# PROTOCOL "Protocol to use (tcp, udp)"
# ENDARGS
# AUTHOR: Your Name

import sys
import os
import json
import socket
import time
import signal
import threading
from datetime import datetime

# Set default values and parse arguments
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
protocol = sys.argv[2].lower() if len(sys.argv) > 2 else "tcp"

# Constants
CONFIG_PATH = "/tmp/config.json"
BUFFER_SIZE = 1024
LOG_PREFIX = "[BSTI Listener]"

# Load configuration if available
config = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        print(f"{LOG_PREFIX} Loaded configuration from {CONFIG_PATH}")
    except json.JSONDecodeError:
        print(f"{LOG_PREFIX} Error: Invalid JSON in configuration file")
        sys.exit(1)
    except Exception as e:
        print(f"{LOG_PREFIX} Error loading configuration: {str(e)}")
else:
    print(f"{LOG_PREFIX} No configuration file found at {CONFIG_PATH}, using defaults")

# Override defaults with configuration values if present
port = config.get('port', port)
protocol = config.get('protocol', protocol)
listen_timeout = config.get('timeout', 300)  # 5 minutes default
log_connections = config.get('log_connections', True)

# Validate inputs
if not isinstance(port, int) or port < 1 or port > 65535:
    print(f"{LOG_PREFIX} Error: Invalid port number. Must be between 1-65535")
    sys.exit(1)

if protocol not in ['tcp', 'udp']:
    print(f"{LOG_PREFIX} Error: Invalid protocol. Must be 'tcp' or 'udp'")
    sys.exit(1)

# Setup signal handling for graceful shutdown
running = True

def signal_handler(sig, frame):
    global running
    print(f"\n{LOG_PREFIX} Received signal to terminate")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Helper functions
def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {level} - {message}")

def handle_tcp_connection(client_socket, client_address):
    """Handle a TCP client connection"""
    log_message(f"New connection from {client_address[0]}:{client_address[1]}")
    
    try:
        while running:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
                
            # Process the received data (example)
            received = data.decode('utf-8').strip()
            log_message(f"Received: {received}")
            
            # Example response
            response = f"Echo: {received}".encode('utf-8')
            client_socket.send(response)
    except Exception as e:
        log_message(f"Error handling connection: {str(e)}", "ERROR")
    finally:
        client_socket.close()
        log_message(f"Connection closed: {client_address[0]}:{client_address[1]}")

def handle_udp_packet(server_socket):
    """Handle UDP packets"""
    try:
        data, client_address = server_socket.recvfrom(BUFFER_SIZE)
        
        # Process the received data (example)
        received = data.decode('utf-8').strip()
        log_message(f"Received UDP from {client_address[0]}:{client_address[1]}: {received}")
        
        # Example response
        response = f"Echo: {received}".encode('utf-8')
        server_socket.sendto(response, client_address)
    except Exception as e:
        log_message(f"Error handling UDP packet: {str(e)}", "ERROR")

# Main function
def main():
    """Main function to set up and run the listener"""
    print(f"{'=' * 60}")
    print(f"{LOG_PREFIX} Starting network listener")
    print(f"Protocol: {protocol.upper()}")
    print(f"Port: {port}")
    print(f"{'=' * 60}")
    
    if protocol == "tcp":
        # TCP Server setup
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind(('0.0.0.0', port))
            server.listen(5)
            server.settimeout(1.0)  # Short timeout to check for running flag
            log_message(f"TCP listener started on port {port}")
            
            while running:
                try:
                    client, address = server.accept()
                    client_handler = threading.Thread(
                        target=handle_tcp_connection,
                        args=(client, address)
                    )
                    client_handler.daemon = True
                    client_handler.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    log_message(f"Error accepting connection: {str(e)}", "ERROR")
                    if not running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            log_message(f"Error setting up TCP listener: {str(e)}", "ERROR")
            sys.exit(1)
        finally:
            server.close()
            
    elif protocol == "udp":
        # UDP Server setup
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            server.bind(('0.0.0.0', port))
            server.settimeout(1.0)  # Short timeout to check for running flag
            log_message(f"UDP listener started on port {port}")
            
            while running:
                try:
                    handle_udp_packet(server)
                except socket.timeout:
                    continue
                except Exception as e:
                    log_message(f"Error in UDP listener: {str(e)}", "ERROR")
                    if not running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            log_message(f"Error setting up UDP listener: {str(e)}", "ERROR")
            sys.exit(1)
        finally:
            server.close()
    
    log_message("Listener shutting down")
    print(f"{'=' * 60}")
    print(f"{LOG_PREFIX} Listener stopped")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main() 